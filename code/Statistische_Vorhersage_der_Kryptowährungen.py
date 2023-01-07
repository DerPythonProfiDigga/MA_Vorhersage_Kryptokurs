# Imports
import pandas as pd
from binance.client import Client
import numpy as np
import csv

def rechne_mittelwert(crypto_preis_dict):
    crypto_mittelwert = 0
    crypto_summe = 0
    anzahl_crypto_preise = len(crypto_preis_dict)
    for datum_key, crypto_preis_value in crypto_preis_dict.items():
        crypto_summe += crypto_preis_value
    crypto_mittelwert = 1 / anzahl_crypto_preise * crypto_summe
    return crypto_mittelwert

def rechne_varianz(crypto_preis_dict):
    crypto_mittelwert = rechne_mittelwert(crypto_preis_dict)
    crypto_varianz_wert = 0
    anzahl_crypto_preise = len(crypto_preis_dict)
    for datum_key, crypto_preis_value in crypto_preis_dict.items():
        schlaufe_varianz_wert = (crypto_preis_value - crypto_mittelwert) ** 2
        crypto_varianz_wert += schlaufe_varianz_wert
    crypto_varianz_wert = 1 / anzahl_crypto_preise * crypto_varianz_wert
    return crypto_varianz_wert

def rechne_kovarianz(preis_dict_1, preis_dict_2):
    if len(preis_dict_1) != len(preis_dict_2):
        raise Exception("Crypro Datenhaltung Länge nicht identisch")
    crypto_mittelwert_y = rechne_mittelwert(preis_dict_1)
    crypto_mittelwert_x = rechne_mittelwert(preis_dict_2)
    anzahl_crypto_preise = len(preis_dict_1)
    crypto_kovarianz_wert = 0
    for datum_key, crypto_preis_value in preis_dict_1.items():
        if datum_key not in preis_dict_2.keys():
            raise Exception(
                "Die Schlüssel der beiden Input Dictionairs müssen identisch sein")
        schlaufe_kovarianz_wert = (preis_dict_1[datum_key] -
                                   crypto_mittelwert_y) * (
                                          preis_dict_2[datum_key] - crypto_mittelwert_x)
        crypto_kovarianz_wert += schlaufe_kovarianz_wert
    crypto_kovarianz_wert = 1 / anzahl_crypto_preise * crypto_kovarianz_wert
    return crypto_kovarianz_wert

def rechne_regressionskoeffizient(preis_dict_1, preis_dict_2):
    kovarianz = rechne_kovarianz(preis_dict_1, preis_dict_2)
    varianz = rechne_varianz(preis_dict_2)
    regressionskoeffizient = kovarianz / varianz
    return regressionskoeffizient

def rechne_regressions_konstante(preis_dict_1, preis_dict_2):
    regressionskoeffizient = rechne_regressionskoeffizient(preis_dict_1, preis_dict_2)
    crypto_mittelwert_y = rechne_mittelwert(preis_dict_1)
    crypto_mittelwert_x = rechne_mittelwert(preis_dict_2)
    regressions_konstante = crypto_mittelwert_y - (regressionskoeffizient * crypto_mittelwert_x)
    return regressions_konstante

def rechne_geschaetzter_wert_Y(preis_dict_1, preis_dict_2):
    regressions_konstante = rechne_regressions_konstante(preis_dict_1, preis_dict_2)
    regressionskoeffizient = rechne_regressionskoeffizient(preis_dict_1, preis_dict_2)
    last_key_x = list(preis_dict_2)[-1]
    letzer_preis_x = (preis_dict_2[last_key_x])
    geschaetzter_wert_Y = regressions_konstante + (regressionskoeffizient * letzer_preis_x)
    return geschaetzter_wert_Y

def getdailydata(symbol, client, start_str, end_str, ZeitInterval):
    frame = pd.DataFrame(client.get_historical_klines(symbol,
                                                      ZeitInterval, start_str, end_str))
    if len(frame) > 0:
        frame = frame.iloc[:, :5]
        frame.columns = ['Time', 'Open', 'High', 'Low', 'Close']
        frame = frame.set_index('Time')
        frame.index = pd.to_datetime(frame.index, unit='ms')
        frame = frame.astype(float)
        return frame

#Zur Daten Beschaffung für den darauf folgenden Tag -> um tatsächlicher Preis mit Vorhersage zu vergleichen
def getdailydata_next(symbol, client, preis_next, ZeitInterval):
    frame = pd.DataFrame(client.get_historical_klines(symbol,
                                                      ZeitInterval, preis_next))
    if len(frame) > 0:
        frame = frame.iloc[:, :5]
        frame.columns = ['Time', 'Open', 'High', 'Low', 'Close']
        frame = frame.set_index('Time')
        frame.index = pd.to_datetime(frame.index, unit='ms')
        frame = frame.astype(float)
        return frame

def rechne_tag(start_str, end_str, preis_next, ZeitInterval):
    # Verbinden mit BinanceAPI
    client = Client('83AErTjgxkHNPEB4FyUe7fD8dGXZScIQ2Fw5gneHWZYHNgs9WoE8HJxWVrPEOco4',
                    'PHZAwfDNxHL5rfpgbFh97CpUrx5sEIjVS1HuQEkIBeTmaGpFS8m3vsNI4xPb7bRr')
    info = client.get_exchange_info()
    symbols = [x['symbol'] for x in info['symbols']]
    relevant = [symbol for symbol in symbols if symbol.endswith('USDT')]
    symbol = ('BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'LTCUSDT', 'DOGEUSDT')

    dfs = []

    for coin in symbol:
        dfs.append(getdailydata(coin, client, start_str, end_str, ZeitInterval))

    # Ziping Dateframe and relevant so kann man ein datafram für jedeneinzelen Coin erstellen.
    # Somit wissen wir für jeden Dataframe den zugehörigen Coin.
    # und schlussendlich werden die ddfs zusammen geführt (merge)
    mergeddf = pd.concat(dict(zip(symbol, dfs)), axis=1)

    # Wir wollen nur close spalte -> müssen diese herausfiltern
    # "level_values(1)" steht für die 2. Zelle (Die erste Zeille wäre "level_values(0)"), danach Filtern wir nach 'Close'.
    closesdf = mergeddf.loc[:, mergeddf.columns.get_level_values(1).isin(['Close'])]

    crypto_usdt_dict = {}

    for key, item in closesdf.items():
        crypto_usdt_dict_sub = {}
        for date_key, crypto_close_price in item.items():
            key_str = date_key.strftime("%Y-%m-%d-%H")
            crypto_usdt_dict_sub[key_str] = crypto_close_price
            #print(key_str)

        crypto_usdt_dict[key[0]] = crypto_usdt_dict_sub

    crypto_kovarianz_wert = rechne_kovarianz(crypto_usdt_dict["ETHUSDT"], crypto_usdt_dict["BTCUSDT"])

    #Abrufen der Funktion zur Berechnung der Daten aus der Regressionsfunktion
    geschaetzter_wert_Y_btc_eth = rechne_geschaetzter_wert_Y(crypto_usdt_dict["BTCUSDT"], crypto_usdt_dict["ETHUSDT"])
    geschaetzter_wert_Y_btc_bnb = rechne_geschaetzter_wert_Y(crypto_usdt_dict["BTCUSDT"], crypto_usdt_dict["BNBUSDT"])
    geschaetzter_wert_Y_btc_ltc = rechne_geschaetzter_wert_Y(crypto_usdt_dict["BTCUSDT"], crypto_usdt_dict["LTCUSDT"])
    geschaetzter_wert_Y_btc_doge = rechne_geschaetzter_wert_Y(crypto_usdt_dict["BTCUSDT"], crypto_usdt_dict["DOGEUSDT"])
    durchschnitt_geschaetzter_wert_Y_btc = (geschaetzter_wert_Y_btc_eth + geschaetzter_wert_Y_btc_bnb + geschaetzter_wert_Y_btc_ltc + geschaetzter_wert_Y_btc_doge) / 4
    start_preis_btc = list(crypto_usdt_dict['BTCUSDT'].values())[0]
    end_preis_btc = list(crypto_usdt_dict['BTCUSDT'].values())[-1]

    geschaetzter_wert_Y_eth_btc = rechne_geschaetzter_wert_Y(crypto_usdt_dict["ETHUSDT"], crypto_usdt_dict["BTCUSDT"])
    geschaetzter_wert_Y_eth_bnb = rechne_geschaetzter_wert_Y(crypto_usdt_dict["ETHUSDT"], crypto_usdt_dict["BNBUSDT"])
    geschaetzter_wert_Y_eth_ltc = rechne_geschaetzter_wert_Y(crypto_usdt_dict["ETHUSDT"], crypto_usdt_dict["LTCUSDT"])
    geschaetzter_wert_Y_eth_doge = rechne_geschaetzter_wert_Y(crypto_usdt_dict["ETHUSDT"], crypto_usdt_dict["DOGEUSDT"])
    durchschnitt_geschaetzter_wert_Y_eth = (geschaetzter_wert_Y_eth_btc + geschaetzter_wert_Y_eth_bnb + geschaetzter_wert_Y_eth_ltc + geschaetzter_wert_Y_eth_doge) / 4
    start_preis_eth = list(crypto_usdt_dict['ETHUSDT'].values())[0]
    end_preis_eth = list(crypto_usdt_dict['ETHUSDT'].values())[-1]

    geschaetzter_wert_Y_bnb_btc = rechne_geschaetzter_wert_Y(crypto_usdt_dict["BNBUSDT"], crypto_usdt_dict["BTCUSDT"])
    geschaetzter_wert_Y_bnb_eth = rechne_geschaetzter_wert_Y(crypto_usdt_dict["BNBUSDT"], crypto_usdt_dict["ETHUSDT"])
    geschaetzter_wert_Y_bnb_ltc = rechne_geschaetzter_wert_Y(crypto_usdt_dict["BNBUSDT"], crypto_usdt_dict["LTCUSDT"])
    geschaetzter_wert_Y_bnb_doge = rechne_geschaetzter_wert_Y(crypto_usdt_dict["BNBUSDT"], crypto_usdt_dict["DOGEUSDT"])
    durchschnitt_geschaetzter_wert_Y_bnb = (geschaetzter_wert_Y_bnb_btc + geschaetzter_wert_Y_bnb_eth + geschaetzter_wert_Y_bnb_ltc + geschaetzter_wert_Y_bnb_doge) / 4
    start_preis_bnb = list(crypto_usdt_dict['BNBUSDT'].values())[0]
    end_preis_bnb = list(crypto_usdt_dict['BNBUSDT'].values())[-1]

    geschaetzter_wert_Y_ltc_btc = rechne_geschaetzter_wert_Y(crypto_usdt_dict["LTCUSDT"], crypto_usdt_dict["BTCUSDT"])
    geschaetzter_wert_Y_ltc_eth = rechne_geschaetzter_wert_Y(crypto_usdt_dict["LTCUSDT"], crypto_usdt_dict["ETHUSDT"])
    geschaetzter_wert_Y_ltc_bnb = rechne_geschaetzter_wert_Y(crypto_usdt_dict["LTCUSDT"], crypto_usdt_dict["BNBUSDT"])
    geschaetzter_wert_Y_ltc_doge = rechne_geschaetzter_wert_Y(crypto_usdt_dict["LTCUSDT"], crypto_usdt_dict["DOGEUSDT"])
    durchschnitt_geschaetzter_wert_Y_ltc = (geschaetzter_wert_Y_ltc_btc + geschaetzter_wert_Y_ltc_eth + geschaetzter_wert_Y_ltc_bnb + geschaetzter_wert_Y_ltc_doge) / 4
    start_preis_ltc = list(crypto_usdt_dict['LTCUSDT'].values())[0]
    end_preis_ltc = list(crypto_usdt_dict['LTCUSDT'].values())[-1]

    geschaetzter_wert_Y_doge_btc = rechne_geschaetzter_wert_Y(crypto_usdt_dict["DOGEUSDT"], crypto_usdt_dict["BTCUSDT"])
    geschaetzter_wert_Y_doge_eth = rechne_geschaetzter_wert_Y(crypto_usdt_dict["DOGEUSDT"], crypto_usdt_dict["ETHUSDT"])
    geschaetzter_wert_Y_doge_bnb = rechne_geschaetzter_wert_Y(crypto_usdt_dict["DOGEUSDT"], crypto_usdt_dict["BNBUSDT"])
    geschaetzter_wert_Y_doge_ltc = rechne_geschaetzter_wert_Y(crypto_usdt_dict["DOGEUSDT"], crypto_usdt_dict["LTCUSDT"])
    durchschnitt_geschaetzter_wert_Y_doge = (geschaetzter_wert_Y_doge_btc + geschaetzter_wert_Y_doge_eth + geschaetzter_wert_Y_doge_bnb + geschaetzter_wert_Y_doge_ltc) / 4
    start_preis_doge = list(crypto_usdt_dict['DOGEUSDT'].values())[0]
    end_preis_doge = list(crypto_usdt_dict['DOGEUSDT'].values())[-1]

    dfs = []

    for coin in symbol:
        dfs.append(getdailydata_next(coin, client, preis_next, ZeitInterval))

    mergeddf_next = pd.concat(dict(zip(symbol, dfs)), axis=1)
    closesdf_next = mergeddf_next.loc[:, mergeddf_next.columns.get_level_values(1).isin(['Close'])]
    crypto_usdt_dict_next = {}

    for key, item in closesdf_next.items():
        crypto_usdt_dict_sub_next = {}
        for date_key, crypto_close_price_next in item.items():
            key_str = date_key.strftime("%Y-%m-%d-%H")
            crypto_usdt_dict_sub_next[key_str] = crypto_close_price_next
        crypto_usdt_dict_next[key[0]] = crypto_usdt_dict_sub_next

    #Tatsächlich eingetroffene Preise für den Vergleich mit den vorhergesagten Preisen
    next_preis_btc = list(crypto_usdt_dict_next['BTCUSDT'].values())[0]
    next_preis_eth = list(crypto_usdt_dict_next['ETHUSDT'].values())[0]
    next_preis_bnb = list(crypto_usdt_dict_next['BNBUSDT'].values())[0]
    next_preis_ltc = list(crypto_usdt_dict_next['LTCUSDT'].values())[0]
    next_preis_doge = list(crypto_usdt_dict_next['DOGEUSDT'].values())[0]

    return [start_str,
            end_str,
            geschaetzter_wert_Y_btc_eth,
            geschaetzter_wert_Y_btc_bnb,
            geschaetzter_wert_Y_btc_ltc,
            geschaetzter_wert_Y_btc_doge,
            durchschnitt_geschaetzter_wert_Y_btc,
            start_preis_btc,
            end_preis_btc,
            next_preis_btc,
            next_preis_btc - durchschnitt_geschaetzter_wert_Y_btc,
            geschaetzter_wert_Y_eth_btc,
            geschaetzter_wert_Y_eth_bnb,
            geschaetzter_wert_Y_eth_ltc,
            geschaetzter_wert_Y_eth_doge,
            durchschnitt_geschaetzter_wert_Y_eth,
            start_preis_eth,
            end_preis_eth,
            next_preis_eth,
            next_preis_eth - durchschnitt_geschaetzter_wert_Y_eth,
            geschaetzter_wert_Y_bnb_btc,
            geschaetzter_wert_Y_bnb_eth,
            geschaetzter_wert_Y_bnb_ltc,
            geschaetzter_wert_Y_bnb_doge,
            durchschnitt_geschaetzter_wert_Y_bnb,
            start_preis_bnb,
            end_preis_bnb,
            next_preis_bnb,
            next_preis_bnb - durchschnitt_geschaetzter_wert_Y_bnb,
            geschaetzter_wert_Y_ltc_btc,
            geschaetzter_wert_Y_ltc_eth,
            geschaetzter_wert_Y_ltc_bnb,
            geschaetzter_wert_Y_ltc_doge,
            durchschnitt_geschaetzter_wert_Y_ltc,
            start_preis_ltc,
            end_preis_ltc,
            next_preis_ltc,
            next_preis_ltc - durchschnitt_geschaetzter_wert_Y_ltc,
            geschaetzter_wert_Y_doge_btc,
            geschaetzter_wert_Y_doge_eth,
            geschaetzter_wert_Y_doge_bnb,
            geschaetzter_wert_Y_doge_ltc,
            durchschnitt_geschaetzter_wert_Y_doge,
            start_preis_doge,
            end_preis_doge,
            next_preis_doge,
            next_preis_doge - durchschnitt_geschaetzter_wert_Y_doge
            ]


def start():
    ZeitInterval = '1h'
    start_str_init =  ' Dec 2022 00:00:00 UTC'
    end_str_init = ' Dec 2022 23:59:59 UTC'
    preis_next_init = ' Dec 2022 00:00:00 UTC'

    counter_start = 1
    counter_end = 15

    data = [['Start Datum', 'End Datum', "geschaetzter_wert_Y_btc_eth",
            "geschaetzter_wert_Y_btc_bnb",
            "geschaetzter_wert_Y_btc_ltc",
            "geschaetzter_wert_Y_btc_doge",
            "durchschnitt_geschaetzter_wert_Y_btc",
            'start_preis_btc',
            'end_preis_btc',
            'tatsächlicher_next_preis_btc',
            'Differenz_btc',
            "geschaetzter_wert_Y_eth_btc",
            "geschaetzter_wert_Y_eth_bnb",
            "geschaetzter_wert_Y_eth_ltc",
            "geschaetzter_wert_Y_eth_doge",
            "durchschnitt_geschaetzter_wert_Y_eth",
            'start_preis_eth',
            'end_preis_eth',
            'tatsächlicher_next_preis_eth',
            'Differenz_eth',
            "geschaetzter_wert_Y_bnb_btc ",
            "geschaetzter_wert_Y_bnb_eth ",
            "geschaetzter_wert_Y_bnb_ltc ",
            "geschaetzter_wert_Y_bnb_doge",
            "durchschnitt_geschaetzter_wert_Y_bnb",
            'start_preis_bnb',
            'end_preis_bnb',
            'tatsächlicher_next_preis_bnb',
            'Differenz_bnb',
            "geschaetzter_wert_Y_ltc_btc ",
            "geschaetzter_wert_Y_ltc_eth ",
            "geschaetzter_wert_Y_ltc_bnb ",
            "geschaetzter_wert_Y_ltc_doge",
            "durchschnitt_geschaetzter_wert_Y_ltc",
            'start_preis_ltc',
            'end_preis_ltc',
            'tatsächlicher_next_preis_ltc',
            'Differenz_ltc',
            "geschaetzter_wert_Y_doge_btc",
            "geschaetzter_wert_Y_doge_eth",
            "geschaetzter_wert_Y_doge_bnb",
            "geschaetzter_wert_Y_doge_ltc",
            "durchschnitt_geschaetzter_wert_Y_doge",
            'start_preis_doge',
            'end_preis_doge',
            'tatsächlicher_next_preis_doge',
            'Differenz_doge'
             ]]

    #Schlaufe für die Anzahl Testtage
    for counter in range(counter_start, counter_end):
        start_str = str(counter) + start_str_init
        end_str = str(counter) + end_str_init
        preis_next = str(counter + 1) + preis_next_init

        print('Day: ', counter)

        day_data = rechne_tag(start_str, end_str, preis_next, ZeitInterval)
        data.append(day_data)

    #Abspeichern aller benötigten Daten in einem CSV-File
    with open('data.csv', 'w', newline='') as csvfile:
        my_writer = csv.writer(csvfile, delimiter=';')
        my_writer.writerows(data)

start()
