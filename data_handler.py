import MetaTrader5 as mt5
import pytz
from datetime import datetime, timedelta
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
LOT = os.getenv('LOT')
SYMBOL = os.getenv('SYMBOL')

def symbol_verifier(symbol):
    all_symbols = mt5.symbols_get()
    for ativo in all_symbols:
        if ativo.name == symbol:
            return True
    return False


def get_dt(timeframe):

    if (len(timeframe) == 2):
        if (timeframe[0] == 'M'):
            if(timeframe[1] == '1'):
                timeframe = mt5.TIMEFRAME_M1
            elif(timeframe[1] == '2'):
                timeframe = mt5.TIMEFRAME_M2
            elif(timeframe[1] == '5'):
                timeframe = mt5.TIMEFRAME_M5
    elif (len(timeframe) == 3):
        if (timeframe[0] == 'M'):
            if (timeframe[1:3] == '10'):
                timeframe = mt5.TIMEFRAME_M10
            elif (timeframe[1:3]  == '15'):
                timeframe = mt5.TIMEFRAME_M15

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
    last120 = dt.tail(90)
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
        macro = 'n'
    elif negPoints < posPoints and float(negPoints / posPoints) < 0.85:
        macro = 'p'
    elif negPoints == posPoints or float(negPoints / posPoints) > 0.85 or float(posPoints / negPoints) > 0.85:
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
        micro = 'n'
    elif negPoints < posPoints and float(negPoints / posPoints) < 0.85:
        micro = 'p'
    elif negPoints == posPoints or float(negPoints / posPoints) > 0.85 or float(posPoints / negPoints) > 0.85:
        micro = 'c'

    if(macro == micro and macro == 'p'):
        print("Tendências estão alinhadas e é tendência positiva")
        return macro
    elif(macro == micro and macro == 'n'):
        print("Tendências estão alinhadas e é tendência negativa")
        return macro
    elif(macro == micro and macro == 'c'):
        print("Tendências estão alinhadas, mas é consolidação")
        return False
    else:
        print("Tendências não estão alinhadas.")
        return False


def ponto_continuo(dt, forex=False):
    lastCandle = dt.tail(1)

    # 1 - Entender tendência:

    tend = tendencia(dt)

    # 2 - De acordo com a tendência, analisar se é ponto contínuo
    comp_val_candles = 50
    comp_val_ma = 20

    if forex:
        comp_val_candles = comp_val_candles / 10
        comp_val_ma = comp_val_ma / 10

    if tend == 'n':
        if float(lastCandle['MA20']) > float(lastCandle['MA9']) and float(
                (lastCandle['open']) - float(lastCandle['close']) > comp_val_candles):
            if abs(float(lastCandle['MA20']) - float(lastCandle['open'])) <= comp_val_ma or abs(
                    float(lastCandle['MA20']) - float(lastCandle['high'])) <= comp_val_ma:
                if float(lastCandle['close']) <= float(lastCandle['MA9']):
                    return 'SELL'
    elif tend == 'p':
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


def send_order(order_type, timeframe, forex=False):
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
    fibo = fibonacci(get_dt(timeframe))
    if order_type == 'BUY':
        margin = round((fibo['150'] - fibo['0']) * 0.1)
    elif order_type == 'SELL':
        margin = round((fibo['0'] - fibo['150']) * 0.1)

    margin = margin - (margin % 5)
    if order_type == 'BUY' and not forex:
        order_type = mt5.ORDER_TYPE_BUY
        sl = fibo['0'] - margin * point
        tp = fibo['150'] - margin * point
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
