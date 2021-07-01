# trading-bot

## Informações do script

Script feito em python, usando MetaTrader 5 para envio de ordens.

Análisa um timeframe somente;

Como funciona a execução:

1. Abre o MT5
2. Ve quanto tempo falta para próximo candle fechar.
3. Pega candle que recém fechou e ve se entra na estratégia de ponto contínuo.
4. Caso seja, envia ordem(SL: Último fundo, TP: Projeção de 150% entre último fundo e topo)
5. Caso não seja, entra em loop e termina as 18:00, horário de Brasília.

Todo acompanhamento de cada interação via console.

## Instalação

`git clone <repository-url>`