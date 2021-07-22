import urllib.request
import io
import os
import pandas as pd

import time
import calendar

def getStockData(name):
    if os.path.isfile(f'./csv/{name}.csv'):
        df = pd.read_csv(f'./csv/{name}.csv')
        df.drop(list(df.filter(regex='Unnamed')), axis=1, inplace=True)
        return df
    return getStockDataFromURL(name)

def getStockDataFromURL(name):
    d = list(time.gmtime())
    period2 = calendar.timegm(d)

    d = list(time.gmtime())
    d[0] -= 6
    period1 = calendar.timegm(d)

    try:
        with urllib.request.urlopen(f'https://query1.finance.yahoo.com/v7/finance/download/{name}?period1={period1}&period2={period2}&interval=1d&events=history&includeAdjustedClose=true') as response:
          html = response.read()
    except:
        return
    return pd.read_csv(io.StringIO(html.decode('utf-8')))

def getStocksList():
    df = pd.read_csv('./csv/my_list.csv')
    allStocks = df['stock']
    rows = []
    for s in allStocks:
        rows.append(getStockData(s).iloc[-1,:])
    return(rows, allStocks)

def getExtendedData():
    df = pd.read_csv('./csv/extended_data.csv')
    df.drop(list(df.filter(regex='Unnamed')), axis=1, inplace=True)
    return df