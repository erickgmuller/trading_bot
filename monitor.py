import time
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
from data_handler import get_dt, ponto_continuo, send_order, symbol_verifier
import os
from dotenv import load_dotenv
import threading

load_dotenv()
SYMBOL = os.getenv('SYMBOL')

# Inicializando o MT5 e fazendo login

if not mt5.initialize():
    print("initialize() failed, error code=", mt5.last_error())

def monitor(timeframe = 'M2'):

    # Verifica se o ativo está realmente linkado a conta da corretora
    if not symbol_verifier(SYMBOL):
        print("Ativo não encontrado dentro da corretora")
        exit

    # Cria o delay do fechamento do candle a partir do timeframe passado
    delay = timedelta()
    if(len(timeframe) == 2):
        if(timeframe[0] == 'M'):
            delay = timedelta(minutes=int(timeframe[1]))
        elif(timeframe[0] == 'H'):
            delay = timedelta(hours=int(timeframe[1]))
        elif(timeframe[0] == 'D'):
            delay = timedelta(days=int(timeframe[1]))
        elif(timeframe[0] == 'W'):
            delay = timedelta(weels=int(timeframe[1]))
    elif (len(timeframe) == 3):
        if (timeframe[0] == 'M' and timeframe[1].isnumeric()):
            delay = timedelta(minutes=int(timeframe[1:2]))
        elif (timeframe[0] == 'H'):
            delay = timedelta(hours=int(timeframe[1:2]))
        elif (timeframe[0:1] == 'MN'):
            delay = 4 * (timedelta(weeks=int(timeframe[1:2])))

    # Inicia o loop que vai monitorar os fechamentos dos candles, testar estratégia e enviar ordens
    while True:
        print("\n")
        print("------------------------------------------------------------------")
        print("------------------------- Nova Interação -------------------------")
        print("Thread do timeframe: ", timeframe)
        # Checando se o dia do último candle é o mesmo.
        dt = get_dt(timeframe)

        if(dt.tail(1)['time'].dt.dayofweek.values < datetime.today().weekday()):
            print("Esperando candle fechar no dia de hoje")
            time.sleep(60)
            continue

        # Checando se o último candle foi um PC
        pc = ponto_continuo(dt)

        if (type(pc) == 'str'):
            pc = pc.strip()

        if pc is None or pc == 'NONE':
            print("Não é ponto contínuo")
        elif pc == 'c':
            pass
        elif pc == 'BUY' or pc == 'SELL':
            print("Ponto Contínuo achado:", pc)
            send_order(pc, timeframe)

        # Printando o candle que foi analisado
        printCandle = pd.to_datetime(dt.tail(1)['time'])
        printCandle = printCandle.dt.strftime("%H:%M")
        print("Candle analisado:", printCandle.values[0])

        # Dorminndo até o próximo candle
        now = datetime.now()
        end = pd.to_datetime(dt.tail(1)['time']) + delay * 2

        if SYMBOL == 'WINQ21':
            timeforsleep = end - now
        else:
            timeforsleep = end - (now + timedelta(hours=6))

        print("Dormindo: ", float(timeforsleep.dt.total_seconds()), " segundos até o próximo candle")
        time.sleep((abs(int(timeforsleep.dt.total_seconds()))) + 5)

m1 = threading.Thread(target=monitor, args=('M1',))
m2 = threading.Thread(target=monitor, args=('M2',))
m5 = threading.Thread(target=monitor, args=('M5',))

m1.start()
time.sleep(2)
m2.start()
time.sleep(2)
m5.start()

