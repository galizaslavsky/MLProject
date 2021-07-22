import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report,confusion_matrix
from sklearn.model_selection import train_test_split

from datetime import datetime
from getData import getStockData, getExtendedData

def amendFeatures(df):
    weekday = df['Date'].copy()
    month = df['Date'].copy()
    weekN = df['Date'].copy()
    for i in range(0, len(weekday)):
        weekday[i] = datetime.strptime(weekday[i], '%Y-%m-%d').weekday()
        month[i] = datetime.strptime(month[i], '%Y-%m-%d').month
        weekN[i] = datetime.strptime(weekN[i], '%Y-%m-%d').isocalendar()[1]
    df['Weekday'] = weekday.astype(int)
    df['Month'] = month.astype(int)
    df['WeekN'] = weekN.astype(int)

    cl_arr = df['Close'].copy()
    op_arr = df['Open'].copy()
    for i in range(1, len(cl_arr)):
        op_arr[i] = (op_arr[i] - cl_arr[i - 1]) / cl_arr[i - 1]
    op_arr[0] = 0
    df['Gap'] = op_arr * 100

    df['InDayChange'] = ((df['Close'] - df['Open']) / df['Close']) * 100
    df['InDayHighLow'] = ((df['High'] - df['Low']) / df['Close']) * 100

    clarr = df['Close'].copy()
    min25 = list(np.zeros(len(clarr)))
    max25 = list(np.zeros(len(clarr)))
    min100 = list(np.zeros(len(clarr)))
    max100 = list(np.zeros(len(clarr)))
    min250 = list(np.zeros(len(clarr)))
    max250 = list(np.zeros(len(clarr)))

    for i in range(250, len(clarr)):
        min25[i] = clarr[i - 25:i].min()
        max25[i] = clarr[i - 25:i].max()
        min100[i] = clarr[i - 100:i].min()
        max100[i] = clarr[i - 100:i].max()
        min250[i] = clarr[i - 250:i].min()
        max250[i] = clarr[i - 250:i].max()

    df['min25'] = (df['Close'] - min25) * 100 / df['Close']
    df['max25'] = (max25 - df['Close']) * 100 / df['Close']
    df['min100'] = (df['Close'] - min100) * 100 / df['Close']
    df['max100'] = (max100 - df['Close']) * 100 / df['Close']
    df['min250'] = (df['Close'] - min250) * 100 / df['Close']
    df['max250'] = (max250 - df['Close']) * 100 / df['Close']

    clarr = df['Close'].copy()
    delta2 = list(np.zeros(len(clarr)))
    delta3 = list(np.zeros(len(clarr)))
    delta4 = list(np.zeros(len(clarr)))
    delta5 = list(np.zeros(len(clarr)))
    for i in range(5, len(clarr)):
        delta2[i] = (clarr[i] - clarr[i - 2]) * 100 / clarr[i]
        delta3[i] = (clarr[i] - clarr[i - 3]) * 100 / clarr[i]
        delta4[i] = (clarr[i] - clarr[i - 4]) * 100 / clarr[i]
        delta5[i] = (clarr[i] - clarr[i - 5]) * 100 / clarr[i]

    df['delta2'] = delta2
    df['delta3'] = delta3
    df['delta4'] = delta4
    df['delta5'] = delta5

    arr = df.Close.copy()
    deltas = df.Close.copy()
    for i in range(0, len(arr) - 1):
        deltas[i] = (arr[i + 1] - deltas[i]) * 100 / arr[i + 1]
    deltas[len(arr) - 1] = 0
    df['nextDayChangeRatio'] = deltas

    df['Target'] = df['nextDayChangeRatio']
    df.at[df.query('abs(Target) < 2').index, 'Target'] = 0
    df.at[df.query('Target >= 2').index, 'Target'] = 1
    df.at[df.query('Target <= -2').index, 'Target'] = -1
    df['Target'] = df['Target'].astype(int)

    df.drop(range(0, 250), inplace=True)

    return df

def predict(name):
    df_ext = getExtendedData()

    df = getStockData(name)
    if not hasattr(df,'Target'):
        df = amendFeatures(df)

    last_day = df.loc[len(df)-1, ['Date', 'Open', 'Close', 'High', 'Low']]
    last_day_pred = df.tail(1)[['Weekday','WeekN','Month','InDayChange','InDayHighLow',
                                'min25','max25','min100','max100','min250','max250',
                                'delta2','delta3','delta4','delta5','Gap']]
    df.drop(len(df)-1, inplace=True)

    df.drop(df.query("Target==0 and abs(Gap)>10").index, axis=0, inplace=True)
    df.drop(df.query("Target==0 and InDayHighLow>12").index, axis=0, inplace=True)
    df.drop(df.query("Target==0 and abs(InDayChange)>10").index, axis=0, inplace=True)

    vc = df['Target'].value_counts()
    if vc[0] > vc[1] + vc[-1]:
        df = pd.concat(
            [df[df.Target == 0].sample(int(len(df[df.Target != 0]))), df[df.Target != 0], df[df.Target != 0]],
            axis=0,ignore_index=True)

    df = pd.concat([df, df_ext.sample(frac=0.8)], ignore_index=True)
    model = RandomForestClassifier(n_estimators=80)
    X = df[['Weekday','WeekN','Month','InDayChange','InDayHighLow','min25','max25',
             'min100','max100','min250','max250','delta2','delta3','delta4','delta5','Gap']]
    y = df['Target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.30, random_state=42)

    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    report = classification_report(y_test, model.predict(X_test)).split('\n')

    last_day['Prediction'] = model.predict(last_day_pred)[0]

    return (last_day, report, score)

def quickPrediction():
    df = pd.read_csv('./csv/my_list.csv')
    allStocks = df['stock']
    rows = []
    scores = []
    for s in allStocks:
        pr = predict(s)
        rows.append(pr[0])
        scores.append(pr[2])
    return rows, allStocks, scores
