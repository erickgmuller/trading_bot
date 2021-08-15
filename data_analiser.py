import MetaTrader5 as mt5
import pytz
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
SYMBOL = os.getenv('SYMBOL')
LOT = os.getenv('LOT')
TIMEFRAME = os.getenv('TIMEFRAME')

def symbol_verifier():
    all_symbols = mt5.symbols_get()
    for symbol in all_symbols:
        if symbol.name == SYMBOL:
            return True
    return False


def get_dt(timeframe=mt5.TIMEFRAME_M5):

    # Timezone de SP e define o horário de agora (se for forex +6 horas)
    timezone = pytz.timezone("America/Sao_Paulo")

    if SYMBOL == 'WINQ21':
        now = datetime.now(timezone)
    else:
        now = datetime.now(timezone) + timedelta(hours=6)

    rates = mt5.copy_rates_from(SYMBOL, timeframe, now, 99999)
    dt = pd.DataFrame(rates)

    dt = dt.iloc[:-1]

    dt['time'] = pd.to_datetime(dt['time'], unit='s')
    dt['MA9'] = dt['close'].rolling(window=9).mean()
    dt['MA20'] = dt['close'].rolling(window=20).mean()

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
        levels = {'0': bot['low'], '38.2': (bot['low'] + float(diff['low'] * 0.382)),
                  '50': (bot['low'] + float(diff['low'] * 0.5)), '61.8': (bot['low'] + float(diff['low'] * 0.618)),
                  '100': top['high'], "150": (top['high'] + float(diff['low'] * 0.5))}
    elif tend == 'n':
        levels = {'0': top['high'], '38.2': (top['high'] - float(diff['low'] * 0.382)),
                  '50': (top['high'] - float(diff['low'] * 0.5)), '61.8': (top['high'] - float(diff['low'] * 0.618)),
                  '100': bot['low'], "150": (bot['low'] - float(diff['low'] * 0.5))}

    levels['0'] = levels['0'] - (levels['0'] % 5)
    levels['38.2'] = levels['38.2'] - (levels['38.2'] % 5)
    levels['50'] = levels['50'] - (levels['50'] % 5)
    levels['100'] = levels['100'] - (levels['100'] % 5)
    levels['150'] = levels['150'] - (levels['150'] % 5)

    return levels


def tendencia(dt):
    last120 = dt.tail(120)
    last30 = dt.tail(30)
    negPoints = 0
    posPoints = 0
    macro = False
    micro = False

    # Checa tendencia macro
    for index, candle in last120.iterrows():
        if float(candle['open']) < float(candle['close']) and float(candle['close']) > float(candle['MA20']):
            # Candle positivo e fechamento acima da média de 20, corpo de 50 pts
            posPoints += 1
        elif float(candle['open']) > float(candle['close']) and float(candle['close']) < float(candle['MA20']):
            # Candle negativo e fechamento abaixo da média de 20, corpo de 50 pts
            negPoints += 1

    if negPoints > posPoints and float(posPoints / negPoints) < 0.85:
        print("Tendencia macro negativa (-)")
        print("Pontos positivos: ", posPoints, " e pontos negativos: ", negPoints)
        macro = 'n'
    elif negPoints < posPoints and float(negPoints / posPoints) < 0.85:
        print("Tendencia macro positiva (+)")
        print("Pontos positivos: ", posPoints, " e pontos negativos: ", negPoints)
        macro = 'p'
    elif negPoints == posPoints or float(negPoints / posPoints) > 0.85 or float(posPoints / negPoints) > 0.85:
        print("Tendencia macro consolidação (=)")
        print("Pontos positivos: ", posPoints, " e pontos negativos: ", negPoints)
        macro = 'c'

    # Checa tendencia micro
    negPoints = 0
    posPoints = 0
    for index, candle in last30.iterrows():
        if float(candle['open']) < float(candle['close']) and float(candle['close']) > float(candle['MA20']):
            # Candle positivo e fechamento acima da média de 20, corpo de 50 pts
            posPoints += 1
        elif float(candle['open']) > float(candle['close']) and float(candle['close']) < float(candle['MA20']):
            # Candle negativo e fechamento abaixo da média de 20, corpo de 50 pts
            negPoints += 1

    if negPoints > posPoints and float(posPoints / negPoints) < 0.85:
        print("Tendencia micro negativa (-)")
        print("Pontos positivos: ", posPoints, " e pontos negativos: ", negPoints)
        micro = 'n'
    elif negPoints < posPoints and float(negPoints / posPoints) < 0.85:
        print("Tendencia micro positiva (+)")
        print("Pontos positivos: ", posPoints, " e pontos negativos: ", negPoints)
        micro = 'p'
    elif negPoints == posPoints or float(negPoints / posPoints) > 0.85 or float(posPoints / negPoints) > 0.85:
        print("Tendencia micro consolidação (=)")
        print("Pontos positivos: ", posPoints, " e pontos negativos: ", negPoints)
        micro = 'c'

    if(macro == micro):
        print("Tendências estão alinhadas!")
        return True
    else:
        print("Tendências não estão alinhadas.")
        return False


def ponto_continuo(dt, forex=False):
    lastCandle = dt.tail(1)

    # 1 - Entender tendência:

    tend = tendencia(dt)

    # 2 - De acordo com a tendência, analisar se é ponto contínuo
    comp_val_candles = 50
    comp_val_ma = 15

    if forex:
        comp_val_candles = comp_val_candles / 10
        comp_val_ma = comp_val_ma / 10

    if tend:
        if float(lastCandle['MA20']) > float(lastCandle['MA9']) and float(
                (lastCandle['open']) - float(lastCandle['close']) > comp_val_candles):
            if abs(float(lastCandle['MA20']) - float(lastCandle['open'])) <= comp_val_ma or abs(
                    float(lastCandle['MA20']) - float(lastCandle['high'])) <= comp_val_ma:
                if float(lastCandle['close']) <= float(lastCandle['MA9']):
                    return 'SELL'
        if float(lastCandle['MA20']) < float(lastCandle['MA9']) and float(
                (lastCandle['close']) - float(lastCandle['open']) > comp_val_candles):
            if abs(float((lastCandle['open'] - lastCandle['MA20']))) <= comp_val_ma or abs(
                    float((lastCandle['low'] - lastCandle['MA20']))) <= comp_val_ma:
                if float(lastCandle['close']) >= float(lastCandle['MA9']):
                    return 'BUY'
        else:
            return 'NONE'
    else:
        return 'NONE'


def send_order(order_type, forex=False):
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


    if order_type == 'BUY' and not forex:
        order_type = mt5.ORDER_TYPE_BUY
        sl = fibo['0'] - 50 * point
        tp = fibo['150'] - 100 * point
    elif order_type == 'SELL' and not forex:
        order_type = mt5.ORDER_TYPE_SELL
        sl = fibo['0'] + 50 * point
        tp = fibo['150'] + 100 * point
    elif order_type == 'BUY' and forex:
        order_type = mt5.ORDER_TYPE_BUY
        sl = fibo['0'] - 5 * point
        tp = fibo['150'] - 10 * point
    elif order_type == 'SELL' and forex:
        order_type = mt5.ORDER_TYPE_SELL
        sl = fibo['0'] + 5 * point
        tp = fibo['150'] + 10 * point
    else:
        exit()

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": float(LOT),
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

    # Enviando o request e checando o retorno do MT5
    result = mt5.order_send(request)
    print(mt5.last_error())
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

    print(mt5.last_error())
    print("2. order_send done, ", result)
    print("   opened position with POSITION_TICKET={}".format(result.order))
