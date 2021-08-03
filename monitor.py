import MetaTrader5 as mt5
import time
import pytz
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
SYMBOL = os.getenv('SYMBOL')
LOT = os.getenv('LOT')

def get_dt():

    # Inicializando o MT5 e

    if not mt5.initialize():
        print("initialize() failed, error code=", mt5.last_error())

    timezone = pytz.timezone("America/Sao_Paulo")

    # set time zone to UTC
    now = datetime.now(timezone)

    rates = mt5.copy_rates_from(SYMBOL, mt5.TIMEFRAME_M1, now, 9999)

    dt = pd.DataFrame(rates)
    dt['time'] = pd.to_datetime(dt['time'], unit='s')
    dt['MA9'] = dt['close'].rolling(window=9).mean()
    dt['MA20'] = dt['close'].rolling(window=20).mean()

    # print(dt.columns.values)
    return dt


def last_top(dt):
    last100 = dt.tail(30)
    temp = dt.tail(1)

    for index, candle in last100.iterrows():
        if float(candle['high']) > float(temp['high']):
            temp = candle
    return temp


def last_bot(dt):
    last100 = dt.tail(30)
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
        levels = {'0': bot['low'], '38.2': (bot['low'] + float(diff['low'] * 0.382)), '50': (bot['low'] + float(diff['low'] * 0.5)), '61.8': (bot['low'] + float(diff['low'] * 0.618)),
                  '100': top['high'], "150": (top['high'] + float(diff['low']*0.5))}
    elif tend == 'n':
        levels = {'0': top['high'], '38.2': (top['high'] - float(diff['low'] * 0.382)), '50': (top['high'] - float(diff['low'] * 0.5)), '61.8': (top['high'] - float(diff['low'] * 0.618)),
                  '100': bot['low'], "150": (bot['low'] - float(diff['low'] * 0.5))}

    return levels


def tendencia(dt):
    last100 = dt.tail(30)
    negPoints = 0
    posPoints = 0

    for index, candle in last100.iterrows():
        if float(candle['open']) < float(candle['close']) and float(candle['close']) > float(candle['MA20']):
            # Candle positivo e fechamento acima da média de 20, corpo de 50 pts
            posPoints += 1
        elif float(candle['open']) > float(candle['close']) and float(candle['close']) < float(candle['MA20']):
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
        if float(lastCandle['MA20']) > float(lastCandle['MA9']) and float((lastCandle['open']) - float(lastCandle['close']) > 50):
            if abs(float(lastCandle['MA20']) - float(lastCandle['open'])) <= 10 or abs(float(lastCandle['MA20']) - float(lastCandle['high'])) <= 10:
                if float(lastCandle['close']) <= float(lastCandle['MA9']):
                    return 'SELL'
        else:
            return 'NONE'
    elif tend == 'p':
        if float(lastCandle['MA20']) < float(lastCandle['MA9']) and float((lastCandle['close']) - float(lastCandle['open']) > 50):
            if abs(float((lastCandle['open'] - lastCandle['MA20']))) <= 10 or abs(float((lastCandle['low'] - lastCandle['MA20']))) <= 10:
                if float(lastCandle['close']) >= float(lastCandle['MA9']):
                    return 'BUY'
        else:
            return 'NONE'
    elif tend == 'c':
        print('Aviso: ativo em tendência de consolidação. Programa aguardará o ativo entrar em alta ou baixa')
        return 'NONE'
    else:
        return 'NONE'


def send_order(dt, order_type):
    # Confirma se a ação realmente existe

    print("Enviando ordem de ", order_type, " para o  servidor")

    symbol_info = mt5.symbol_info(SYMBOL)
    if symbol_info is None:
        print(SYMBOL, " não foi achado")
        mt5.shutdown()
        quit()

    # Montando as informações do request a ser enviado

    point = mt5.symbol_info(SYMBOL).point
    price = mt5.symbol_info_tick(SYMBOL).ask

    deviation = 20
    fibo = fibonacci(get_dt())
    tp = fibo['150'] * point

    if order_type == 'BUY':
        order_type = mt5.ORDER_TYPE_BUY
        sl = fibo['0'] - 50 * point

    elif order_type == 'SELL':
        order_type = mt5.ORDER_TYPE_SELL
        sl = fibo['0'] + 50 * point
    else:
        exit()

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": deviation,
        "magic": 234000,
        "comment": "Abrindo ordem pelo script",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    print(request)
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
        print("\n")
        print("------------------------------------------------------------------")
        print("------------------------- Nova Interação -------------------------")
        temp = get_dt()
        temp = temp.tail(1)
        now = datetime.now()
        start = pd.to_datetime(temp['time'])
        lastStop = now.replace(hour=18, minute=0, second=0, microsecond=0)

        if (lastStop == start.values):
            break

        # Checando se o último candle foi um PC

        temp = get_dt()
        pc = ponto_continuo(temp)

        printCandle = pd.to_datetime(temp.tail(1)['time'])
        printCandle = printCandle.dt.strftime("%H:%M")
        print("Candle analisado:", printCandle.values[0])

        if (type(pc) == 'str'):
            pc = pc.strip()

        if pc is None or pc == 'NONE':
            print("Não é ponto contínuo")
        else:
            print("Ponto Contínuo achado:", pc)
            send_order(temp, pc)

        # Dorminndo até o próximo candle

        end = start + timedelta(minutes=1)

        timeforsleep = end - now
        timeforsleep = timeforsleep.dt.total_seconds()

        print("Dormindo: " + str(timeforsleep.values[0]) + " segundos até o próximo candle fechar")
        time.sleep(float(timeforsleep.values[0]))

        # Delay
        time.sleep(2)

#monitor()
