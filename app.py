from flask import Flask, render_template, request, redirect
import pandas as pd
import setData, getData, predict

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    setData.updateData()
    rows,stocks = getData.getStocksList()
    return render_template('index.html', page='INDEX', rows=rows, stocks=stocks)

@app.route('/stock',methods=['POST'])
def stockData():
    name = request.form['name'].upper()
    return redirect(f'/stock/{name}')

@app.route('/stock/<name>')
def stock(name):
    try:
        rows = getData.getStockData(name).tail(100)
    except:
        return redirect(f'/error')
    else:
        return render_template('stock.html', page='STOCK', name=name, rows=rows[::-1])

@app.route('/wait_to_predict')
def wait():
    return render_template('wait_to_predict.html', page='WAIT_TO_PREDICT')


@app.route('/predict')
def predictList():
    rows,stocks, scores = predict.quickPrediction()
    return render_template('predict.html', page='PREDICT', rows=rows, stocks=stocks, scores=scores )

@app.route('/stock_predict',methods=['POST'])
def predictDataFromURL():
    name = request.form['name'].upper()
    return redirect(f'/stock_predict/{name}')

@app.route('/stock_predict/<name>')
def stock_predict(name):
    try:
        pr = predict.predict(name)
    except:
        return redirect(f'/error')
    else:
        prediction = pr[0]
        report = []
        for row in pr[1][1:7]:
            report.append((row.split()))
        report[1][0] = 'Short'
        report[2][0] = 'Flat'
        report[3][0] = 'Long'
        report[5].insert(1," ")
        report[5].insert(2, " ")
        score = pr[2]
        return render_template('stock_predict.html', page='STOCK_PREDICT', name=name, prediction=prediction,
                               report=report, score=score)

@app.route('/favorites')
def favorites():
    stocks = pd.read_csv('./csv/my_list.csv')['stock']
    return render_template('favorites.html', page='FAVORITES', stocks = stocks)

@app.route('/favorites/add',methods=['POST'])
def add_favorites():
    stock = request.form['symbol'].upper()
    setData.addToStockList(stock)
    return redirect(f'/favorites')

@app.route('/favorites/delete',methods=['POST'])
def delete_favorites():
    setData.deleteStocks(list(request.form))
    return redirect(f'/favorites')

@app.route('/about')
def about():
    return render_template('about.html', page='ABOUT')

@app.route('/error')
def error():
    return render_template('error.html', page='ERROR')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8082, debug=True)