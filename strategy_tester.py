import MetaTrader5 as mt5
import pytz
from datetime import datetime, timedelta
import pandas as pd


def get_dt():
    if not mt5.initialize():
        print("initialize() failed, error code=", mt5.last_error())

    timezone = pytz.timezone("America/Sao_Paulo")
    now = datetime.now(timezone)
    utc_from = datetime(day=1, month=10, year=2020, tzinfo=timezone)
    rates = mt5.copy_rates_from("WINQ21", mt5.TIMEFRAME_M1, now, 99999)
    dt = pd.DataFrame(rates)

    dt['time'] = pd.to_datetime(dt['time'], unit='s')
    dt['MA9'] = dt['close'].rolling(window=9).mean()
    dt['MA20'] = dt['close'].rolling(window=20).mean()

    return dt


def is_ponto_continuo(dt):

    if dt['MA20'] > dt['MA9'] and dt['open'] - dt['close'] > 50:
        if dt['MA20'] - dt['open'] <= 10 or dt['MA20'] - dt['high'] <= 10:
            if dt['close'] <= dt['MA9']:
                return True

    elif dt['MA20'] < dt['MA9'] and dt['close'] - dt['open'] > 50:
        if dt['open'] - dt['MA20'] <= 10 or dt['low'] - dt['MA20'] <= 10:
            if dt['close'] >= dt['MA9']:
                return True
    else:
        return False


def run():
    dt = get_dt()

    for index, row in dt.iterrows():
        if is_ponto_continuo(row):
            dt.loc[index, 'target'] = 1
        else:
            dt.loc[index, 'target'] = 0

    print(dt.target.value_counts())