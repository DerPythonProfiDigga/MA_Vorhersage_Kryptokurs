# Imports
import pandas as pd
from binance.client import Client
import numpy as np
import json
import requests

ZeitInterval = '1h'
start_str =  ' Dec 2022 00:00:00 UTC'
end_str = ' Dec 2022 23:59:59 UTC'

# Verbinden mit BinanceAPI
client = Client('83AErTjgxkHNPEB4FyUe7fD8dGXZScIQ2Fw5gneHWZYHNgs9WoE8HJxWVrPEOco4', 'PHZAwfDNxHL5rfpgbFh97CpUrx5sEIjVS1HuQEkIBeTmaGpFS8m3vsNI4xPb7bRr')
info = client.get_exchange_info()
symbols = [x['symbol'] for x in info['symbols']]
relevant = [symbol for symbol in symbols if symbol.endswith('USDT')]
symbol = ('BTCUSDT', 'ETHUSDT' , 'BNBUSDT', 'LTCUSDT', 'DOGEUSDT')


def getdailydata(symbol):
    frame = pd.DataFrame(client.get_historical_klines(symbol,
                                                      ZeitInterval, start_str, end_str))
    if len(frame) > 0:
        frame = frame.iloc[:,:5]
        frame.columns = ['Time','Open','High','Low','Close']
        frame = frame.set_index('Time')
        frame.index = pd.to_datetime(frame.index, unit='ms')
        frame = frame.astype(float)
        return frame
dfs = []

for coin in symbol:
    dfs.append(getdailydata(coin))

# Ziping Dateframe and relevant so kann man ein datafram für jedeneinzelen Coin erstellen.
# Somit wissen wir für jeden Dataframe den zugehörigen Coin.
# und schlussendlich werden die ddfs zusammen geführt (merge)
mergeddf = pd.concat(dict(zip(symbol,dfs)), axis=1)

# Wir wollen nur close spalte -> müssen diese herausfiltern
# "level_values(1)" steht für die 2. Zelle (Die erste Zeille wäre "level_values(0)"), danach Filtern wir nach 'Close'.
closesdf = mergeddf.loc[:,mergeddf.columns.get_level_values(1).isin(['Close'])]

# Die Zelle besteht nur noch aus Close Preisen -> Demnach brauchen wir diese auch nicht mehr anzuzeigen
# Im nächsten Schritt wird diese entfernt
closesdf.columns = closesdf.columns.droplevel(1)

# Logreturn steht für die Rentabilität
# Diese zeigt jegliche Veränderung des Preises in einem gewissen Zeitfenster auf
logretdf = np.log(closesdf.pct_change() + 1)

# Erzeugung einer Korrelationsmatrix aus Pandas mit der 'corr()' Funktion
logretdf.corr()

#Speichern der Korrelationsmatrix in einem CSV
corr_df = logretdf.corr()
corr_df.to_csv('Korrelations_Matrix.csv', float_format='%.6f')

# Um dies jetzt visuell darzustellen importieren wir 'Seaborn'
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')

# Heatmap Grössendarstellung
sns.set(rc = {'figure.figsize':(10,10)})

# Visualisierung der Korrelation in einer Heatmap
# Visualisierung aller Coins: "sns.heatmap(logretdf.corr())" mit Grösse: "50, 30"
sns_plot = sns.heatmap(logretdf[['BTCUSDT', 'ETHUSDT' , 'BNBUSDT', 'LTCUSDT', 'DOGEUSDT']].corr())
fig = sns_plot.get_figure()
fig.savefig("Korrelations_Matrix.png")