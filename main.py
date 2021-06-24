import MetaTrader5 as mt5
import time
import pytz
from datetime import datetime, timedelta
import pandas as pd

SYMBOL = "WIN$"
LOT = 0.1
# Inicializando o MT5 e

if not mt5.initialize():
    print("initialize() failed, error code=", mt5.last_error())

timezone = pytz.timezone("America/Sao_Paulo")


def get_dt():
    # set time zone to UTC
    now = datetime.now(timezone)

    rates = mt5.copy_rates_from(SYMBOL, mt5.TIMEFRAME_M1, now, 1000)

    dt = pd.DataFrame(rates)
    dt['time'] = pd.to_datetime(dt['time'], unit='s')
    dt['MA9'] = dt['close'].rolling(window=9).mean()
    dt['MA20'] = dt['close'].rolling(window=20).mean()

    # print(dt.columns.values)
    return dt


def last_top(dt):
    last100 = dt.tail(100)
    temp = dt.tail(1)

    for index, candle in last100.iterrows():
        if float(candle['high']) > float(temp['high']):
            temp = candle
    return temp


def last_bot(dt):
    last100 = dt.tail(100)
    temp = dt.tail(1)
    for index, candle in last100.iterrows():
        if float(candle['low']) < float(temp['low']):
            temp = candle
    return temp


def fibonacci(dt):
    top = last_top(dt)
    bot = last_bot(dt)
    diff = top - bot

    tend = tendencia(dt)
    levels = {}

    if tend == 'p':
        levels = {'0': bot, '38.2': (bot + (diff * 0.382)), '50': (bot + (diff * 0.5)), '61.8': (bot + diff * 0.618),
                  '100': top, "150": (top + diff*0.5)}
    elif tend == 'n':
        levels = {'0': top, '38.2': (top - (diff * 0.382)), '50': (top - (diff * 0.5)), '61.8': (top - diff * 0.618),
                  '100': bot, "150": (bot - diff * 0.5)}

    return levels


def tendencia(dt):
    last100 = dt.tail(100)
    negPoints = 0
    posPoints = 0

    for index, candle in last100.iterrows():
        if candle['open'] < candle['close'] and candle['close'] > candle['MA20'] and (
                candle['close'] - candle['open']) > 50:
            # Candle positivo e fechamento acima da média de 20, corpo de 50 pts
            posPoints += 1
        elif candle['open'] > candle['close'] and candle['close'] < candle['MA20'] and (
                candle['open'] - candle['close']) > 50:
            # Candle negativo e fechamento abaixo da média de 20, corpo de 50 pts
            negPoints += 1

    if negPoints != 0 and posPoints != 0:
        if negPoints > posPoints:
            print("Tendencia negativa (-)")
            print("Pontos positivos: ", posPoints, " e pontos negativos: ", negPoints)
            return 'n'
        elif negPoints < posPoints:
            print("Tendencia positiva (+)")
            print("Pontos positivos: ", posPoints, " e pontos negativos: ", negPoints)
            return 'p'
        elif negPoints == posPoints or (posPoints / negPoints) > 70:
            print("Tendencia consolidação (=)")
            print("Pontos positivos: ", posPoints, " e pontos negativos: ", negPoints)
            return 'c'


def ponto_continuo(dt):
    lastCandle = dt.tail(1)

    # 1 - Entender tendência:

    tend = tendencia(dt)

    # 2 - De acordo com a tendência, analisar se é ponto contínuo

    if tend == 'n':
        if lastCandle['MA20'] > lastCandle['MA9']:
            if (lastCandle['open'] - lastCandle['MA20']) <= 10 or (lastCandle['high'] - lastCandle['MA20']) <= 10:
                if lastCandle['close'] < lastCandle['MA9']:
                    return 'SELL'
        else:
            return 'NONE'
    elif tend == 'p':
        if float(lastCandle['MA20']) < float(lastCandle['MA9']):
            if float((lastCandle['open'] - lastCandle['MA20'])) <= 10 or float((lastCandle['low'] - lastCandle['MA20'])) <= 10:
                if float(lastCandle['close']) > float(lastCandle['MA9']):
                    return 'BUY'
        else:
            return 'NONE'
    elif tend == 'c':
        print('Aviso: ativo em tendência de consolidação. Programa aguardará o ativo entrar em alta ou baixa')
        return 'NONE'


def send_order(dt, order_type):
    # Confirma se a ação realmente existe

    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info is None:
        print(SYMBOL, " não foi achado")
        mt5.shutdown()
        quit()

    # Montando as informações do request a ser enviado

    point = mt5.symbol_info(SYMBOL).point
    price = mt5.symbol_info_tick(SYMBOL).ask
    deviation = 20

    if order_type == 'BUY':
        order_type = mt5.ORDER_TYPE_BUY
    elif order_type == 'SELL':
        order_type = mt5.ORDER_TYPE_SELL

    fibo = fibonacci(get_dt())

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT,
        "type": order_type,
        "price": price,
        "sl": fibo['0'] - 50,
        "tp": fibo['150'],
        "deviation": deviation,
        "magic": 234000,
        "comment": "Abrindo ordem pelo script",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }

    # Enviando o request e checando o retorno do MT5
    result = mt5.order_send(request)
    print("1. order_send(): by {} {} lots at {} with deviation={} points".format(SYMBOL, LOT, price, deviation));
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("2. order_send failed, retcode={}".format(result.retcode))
        # request the result as a dictionary and display it element by element
        result_dict = result._asdict()
        for field in result_dict.keys():
            print("   {}={}".format(field, result_dict[field]))
            # if this is a trading request structure, display it element by element as well
            if field == "request":
                traderequest_dict = result_dict[field]._asdict()
                for tradereq_filed in traderequest_dict:
                    print("       traderequest: {}={}".format(tradereq_filed, traderequest_dict[tradereq_filed]))
        print("shutdown() and quit")
        mt5.shutdown()
        quit()

    print("2. order_send done, ", result)
    print("   opened position with POSITION_TICKET={}".format(result.order))


def monitor():
    while True:
        print("---- Novo Candle ----")
        temp = get_dt()
        temp = temp.tail(1)
        now = datetime.now()
        start = pd.to_datetime(temp['time'])
        lastStop = now.replace(hour=18, minute=0, second=0, microsecond=0)

        if (lastStop == start.values):
            break

        end = start + timedelta(minutes=1)

        timeforsleep = end - now
        timeforsleep = timeforsleep.dt.total_seconds()
        printCandle = start.dt.strftime("%H:%M")
        print("Último candle foi: ", type(printCandle))
        print("Sleeping: " + str(timeforsleep.values[0]) + " seconds")
        time.sleep(float(timeforsleep.values[0]))

        temp = get_dt()
        pc = ponto_continuo(temp)
        if pc != 'NONE':
            print("Ponto Contínuo achado: ", pc)
            send_order(temp, pc)
        else:
            print("Não é ponto contínuo")

        time.sleep(1)


monitor()
