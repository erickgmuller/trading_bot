from monitor import get_dt
import matplotlib.pyplot as plt

dt = get_dt()

def is_ponto_continuo(dt):
    if dt['MA20'] > dt['MA9'] and dt['open'] - dt['close'] > 50:
        if dt['MA20'] - dt['open'] <= 10 or dt['MA20'] - dt['high'] <= 10:
            if dt['close'] <= dt['MA9']:
                return True

    elif float(dt['MA20']) < float(dt['MA9']) and float(
            (dt['close']) - float(dt['open']) > 50):
        if abs(float((dt['open'] - dt['MA20']))) <= 10 or abs(
                float((dt['low'] - dt['MA20']))) <= 10:
            if float(dt['close']) >= float(dt['MA9']):
                return True
    else:
        return False


for index, row in dt.iterrows():
    if is_ponto_continuo(row):
        dt.loc[index, 'target'] = 1
    else:
        dt.loc[index, 'target'] = 0

print(dt.target.value_counts())
print(dt.head(1)['time'])
