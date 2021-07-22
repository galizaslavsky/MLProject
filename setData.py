import os
import pandas as pd

import time
import calendar
from predict import amendFeatures
from getData import getStockDataFromURL

def updateData():
    ts_exist = os.path.isfile('./csv/time_stamp.csv')
    ed_exist = os.path.isfile('./csv/extended_data.csv')
    ml_exist = os.path.isfile('./csv/my_list.csv')

    if not (ts_exist and ed_exist and ml_exist):
        setupData()
    else:
        curr = calendar.timegm(time.gmtime())
        df = pd.read_csv('./csv/time_stamp.csv')
        if (len(df) == 0) or (curr - df['ts'][0] > 3600*24):
            setupData()

def setupData():
    df = pd.DataFrame({'ts': calendar.timegm(time.gmtime())}, index=[0])
    df.to_csv('./csv/time_stamp.csv')

    if not os.path.isfile('./csv/my_list.csv'):
        df = pd.DataFrame({'stock': ['AAPL', 'AMD', 'AMZN', 'FB', 'GOOG', 'INTC', 'MSFT', 'NVDA', 'NFLX']},
                          index=range(9))
        df.to_csv('./csv/my_list.csv')
    else:
        df = pd.read_csv('./csv/my_list.csv')

    for s in df['stock']:
        df_st = getStockDataFromURL(s)
        if df_st is None:
            continue
        df_st = amendFeatures(df_st)
        df_st.drop(list(df_st.filter(regex='Unnamed')), axis=1, inplace=True)
        df_st.to_csv(f'./csv/{s}.csv')
        
    setupExtendedData()

def setupExtendedData():
    try:
        df = pd.read_csv('./csv/my_list.csv')
        allStocks = df['stock'].sample(n=5)
        df = pd.read_csv(f'./csv/{allStocks[0]}.csv')
        for n in allStocks[1:]:
            df_itr = pd.read_csv(f'./csv/{n}.csv')
            df = pd.concat([df,df_itr],ignore_index=True)
    except:
        return -1

    df.drop(df.query("Target==0 and abs(Gap)>10").index, axis=0, inplace=True)
    df.drop(df.query("Target==0 and InDayHighLow>12").index, axis=0, inplace=True)
    df.drop(df.query("Target==0 and abs(InDayChange)>10").index, axis=0, inplace=True)
    df.drop(df.query("nextDayChangeRatio==0").index, axis=0, inplace=True)

    vc = df['Target'].value_counts()
    if vc[0] > 2 * (vc[1] + vc[-1]):
        df = pd.concat(
            [df[df.Target == 0].sample(int(len(df[df.Target != 0]) * 2)), df[df.Target != 0], df[df.Target != 0]],
            axis=0, ignore_index=True)
    elif vc[0] > vc[1] + vc[-1]:
        df = pd.concat(
            [df[df.Target == 0].sample(int(len(df[df.Target != 0]))), df[df.Target != 0], df[df.Target != 0]],
            axis=0, ignore_index=True)
    df.to_csv(f'./csv/extended_data.csv')
    return 0

def addToStockList(stock):
    allStocks = pd.read_csv('./csv/my_list.csv')
    if len(allStocks.query(f"stock == '{stock}'")) != 0:
        return
    df = getStockDataFromURL(stock)
    if not type(df) is int:
        if len(df) <= 250:
            return
        l = list(allStocks['stock'])
        l.append(stock)
        l.sort()
        allStocks = pd.DataFrame({'stock': l}, index=range(len(l)))
        allStocks.to_csv('./csv/my_list.csv')
        df = amendFeatures(df)
        df.drop(list(df.filter(regex='Unnamed')), axis=1, inplace=True)
        df.to_csv(f'./csv/{stock}.csv')

def deleteStocks(stocks):
    l = list(pd.read_csv('./csv/my_list.csv')['stock'])
    for i in stocks[::-1]:
        if len(l) <= 5:
            break
        os.remove(f'./csv/{l[int(i)]}.csv')
        l.pop(int(i))
    allStocks = pd.DataFrame({'stock': l}, index=range(len(l)))
    allStocks.to_csv('./csv/my_list.csv')