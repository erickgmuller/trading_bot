import time
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
from data_analiser import get_dt, ponto_continuo, send_order, symbol_verifier
import os
from dotenv import load_dotenv

load_dotenv()
SYMBOL = os.getenv('SYMBOL')

def monitor():

    # Inicializando o MT5 e fazendo login

    if not mt5.initialize():
        print("initialize() failed, error code=", mt5.last_error())


    if not symbol_verifier():
        print("Ativo não encontrado dentro da corretora")
        exit

    while True:
        print("\n")
        print("------------------------------------------------------------------")
        print("------------------------- Nova Interação -------------------------")
        temp = get_dt()
        temp = temp.tail(1)
        now = datetime.now()
        start = pd.to_datetime(temp['time'])

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
        elif pc == 'c':
            pass
        else:
            print("Ponto Contínuo achado:", pc)
            send_order(temp, pc)

        # Dorminndo até o próximo candle

        end = pd.to_datetime(temp.tail(1)['time']) + timedelta(minutes=1)

        if SYMBOL == 'USDJPY':
            timeforsleep = end - (now + timedelta(hours=6))
        else:
            timeforsleep = end - now

        print("Dormindo: ", float(timeforsleep.dt.total_seconds()), " segundos até o próximo candle")
        time.sleep(float(timeforsleep.dt.total_seconds()))

        # Delay
        time.sleep(2)


monitor()
