import pandas as pd
from strategy_tester import is_ponto_continuo
from data_analiser import get_dt
import MetaTrader5 as mt5
import matplotlib.pyplot as plt
from sklearn.feature_selection import SelectKBest
from sklearn.model_selection import GridSearchCV
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

if not mt5.initialize():
    print("initialize() failed, error code=", mt5.last_error())

# Pega o dataframe e da um shift para mudar o fechamento para -1 candle e assim "prever" o próximo
df_win = get_dt()
for index, row in df_win.iterrows():
    if is_ponto_continuo(row):
        df_win.loc[index, 'target'] = 1
    else:
        df_win.loc[index, 'target'] = 0

df_win['close'] = df_win['close'].shift(-1)
# Drop nas informações nulas (modelo de analise de features não recebe valores nulos)
df_win.dropna(inplace=True)

# Definindo o range de linhas para treino e teste
qtd_linhas = len(df_win)
qtd_linhas_treino = int(qtd_linhas * 0.75)
qtd_linhas_teste = qtd_linhas - 15

qtd_linhas_validacao = qtd_linhas_treino - qtd_linhas_teste

# Criando um index que vai equivaler as linhas criadas
df_win = df_win.reset_index(drop=True)

# Dando um drop nas features que não fazem sentido (feito após segundo teste)
features = df_win.drop(['time', 'close', 'open','MA9'], 1)
labels = df_win['target']

features_list = ('open', 'tick_volume', 'real_volume', 'MA9', 'MA20')

# Rodando o K Best para entender qual melhores features
k_best_features = SelectKBest(k='all')
k_best_features.fit_transform(features, labels)
k_best_features_scores = k_best_features.scores_
raw_pairs = zip(features_list[1:], k_best_features_scores)
ordered_pairs = list(reversed(sorted(raw_pairs, key=lambda x: x[1])))

k_best_features_final = dict(ordered_pairs[:15])
best_features = k_best_features_final.keys()

print(k_best_features_final)

# Usando um scaler MiniMax para deixar todas features com "pesos" iguais para a máquina
scaler = MinMaxScaler().fit(features)
features_scale = scaler.transform(features)

# Definindo o tamanho das amostragem de treino e teste
x_train = features_scale[:qtd_linhas_treino]
x_test = features_scale[qtd_linhas_treino:qtd_linhas_teste]

y_train = labels[:qtd_linhas_treino]
y_test = labels[qtd_linhas_treino:qtd_linhas_teste]

# Treinando com dois modelos, regressão linear e rede neural, para ver qual melhor
# Regressão Linear
lr = linear_model.LinearRegression()
lr.fit(x_train, y_train)
pred = lr.predict(x_test)
cd = r2_score(y_test, pred)

print('Coeficiente de determinação:', cd)

# # Rede neural simples
# rn = MLPRegressor(max_iter=2000)
# rn.fit(x_train, y_train)
# pred = rn.predict(x_test)
# cd = rn.score(x_test, y_test)
#
# print('Coeficiente de determinação:', cd)

# Executando previsão

previsao = features_scale[qtd_linhas_teste:qtd_linhas]

time_full = df_win['time']
time_parcial = time_full[qtd_linhas_teste:qtd_linhas]

res_full = df_win['close']
res_parcial = res_full[qtd_linhas_teste:qtd_linhas]

pred = lr.predict(previsao)

df = pd.DataFrame({'time': time_parcial, 'real': res_parcial, 'previsão': pred})
df['real'] = df['real'].shift(+1)

df.set_index('time', inplace=True)

# Montando gráfico das previsões

plt.figure(figsize=(16,8))
plt.title('Fechamento de candles')
plt.plot(df['real'], label='real', color='blue', marker ='o')
plt.plot(df['previsão'], label='pred', color='red', marker ='o')
plt.xlabel('Horario fechamento candle')
plt.ylabel('Preço fechamento')
leg = plt.legend()
plt.show()