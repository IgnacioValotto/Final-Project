import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import requests
from helpers import apology, login_required, lookup, usd
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
import json
from alpha_vantage.fundamentaldata import FundamentalData
# Configure application
app = Flask(__name__)


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Configura tu API key aquí





# Ruta principal que muestra la lista de acciones
@app.route('/quotes')
@login_required
def quotes():
    search_symbol = request.args.get('symbol')

    if search_symbol and search_symbol.strip():
        symbols = [search_symbol.upper()]
    else:
    # Lista de símbolos de acciones para mostrar
        symbols = [
            'AAPL', 'MSFT', 'GOOGl', 'VIST', 'AMZN', 'TSLA', 'FB', 'NVDA', 'PYPL', 'ADBE', 'MELI', 'TX'
        ]
        data = []
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            # Recuperar datos históricos
            hist_day = ticker.history(period="1d")
            hist_month = ticker.history(period="1mo")
            hist_6months = ticker.history(period="6mo")

            # Calcular variaciones de precios
            if not hist_day.empty and not hist_month.empty and not hist_6months.empty:
                price_last_day = hist_day['Close'].iloc[-1]
                price_first_day_month = hist_month['Close'].iloc[0]
                price_last_day_month = hist_month['Close'].iloc[-1]
                price_first_day_6months = hist_6months['Close'].iloc[0]
                price_last_day_6months = hist_6months['Close'].iloc[-1]

                # Asumiendo que tienes una forma de calcular las variaciones correctamente
                # Aquí deberías calcular las variaciones y luego agregarlas a `data`
                # Por ejemplo:
                variation_day = ((price_last_day - price_last_day) / price_last_day) * 100
                variation_month = ((price_last_day_month - price_first_day_month) / price_first_day_month) * 100
                variation_6months = ((price_last_day_6months - price_first_day_6months) / price_first_day_6months) * 100

                # Añadir los datos calculados a la lista `data`
                data.append({
                    'symbol': symbol,
                    'price': price_last_day,
                    'variation_day': variation_day,
                    'variation_month': variation_month,
                    'variation_6months': variation_6months
                })

    return render_template('quotes.html', data=data)




# Ruta que muestra detalles de una acción específica
@app.route('/details/<symbol>')
@login_required
def details(symbol):
    # Aquí puedes añadir lógica adicional si es necesario
    return render_template('quote_details.html', symbol=symbol)

if __name__ == '__main__':
    app.run(debug=True)




def get_financial_news(query):
    API_KEY = '151cedc6c06f4ccca9c3059fdce27d16'
    BASE_URL = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",  # Solicita artículos en inglés
        "apiKey": API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    return data['articles']


@app.route('/', methods=['GET'])
@login_required
def financial_news():
    query = request.args.get('q', 'mercado financiero')  # Usa 'mercado financiero' como valor por defecto
    articles = get_financial_news(query)
    return render_template('financial_news.html', articles=articles)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/portafolio")
@login_required
def portafolio():
    user_id = session["user_id"]
    # Incluir stock_price y total_price en la consulta
    portfolio = db.execute("SELECT symbol, shares, stock_price, total_price FROM portafolio WHERE user_id = ?", user_id)
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

    total_stocks_value = 0
    for stock in portfolio:
        current_data = lookup(stock["symbol"])
        stock["current_price"] = current_data["price"]
        stock["purchase_price"] = stock["stock_price"]
        stock["total_current_value"] = stock["current_price"] * stock["shares"]
        stock["daily_return"] = (stock["current_price"] - stock["purchase_price"]) / stock["purchase_price"] * 100
        # Calcular average_cost_per_share usando total_price y shares
        stock["average_cost_per_share"] = stock["total_price"] / stock["shares"]
        stock["total_investment"] = stock["shares"] * stock["average_cost_per_share"]

        # Calcular el retorno total en porcentaje
        stock["total_return"] = (stock["total_current_value"] - stock["total_investment"]) / stock["total_investment"] * 100
        total_stocks_value += stock["total_current_value"]

    total_value = cash + total_stocks_value

    return render_template("portafolio.html", portfolio=portfolio, cash=cash, total_value=total_value)






@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method=="POST":
        symbol= request.form.get("symbol")
        if not symbol:
            return apology("No Symbol")
        price= lookup(symbol)
        if price is None:
            return apology("Symbol doesnt exist")
        shares= request.form.get("shares")
        if not shares.isdigit():
            return apology("Shares must be a number")
        if not shares:
            return apology("Insert valid number of shares")
        shares= float(shares)
        if not shares.is_integer():
             return apology("Shares must be a whole number")
        if shares<=0:
            return apology("Insert positive number of shares")
        shares=int(shares)
        cash = db.execute("SELECT cash FROM users WHERE id= ?",
        session["user_id"])
        cash= int(cash[0]['cash'])
        totalPrice= shares * price["price"]
        totalPrice= int(totalPrice)
        if cash < totalPrice:
            return apology("No Enough cash")
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", totalPrice, session["user_id"])


        symboLL = db.execute("SELECT symbol FROM portafolio WHERE user_id= ? AND symbol = ?", session["user_id"], symbol)


        if len(symboLL) != 0 :
            db.execute("UPDATE portafolio SET shares = shares + ?, total_price = total_price + ? WHERE user_id = ? AND symbol = ?", shares,totalPrice, session["user_id"], symbol)
        else:
            db.execute("INSERT INTO portafolio (user_id, symbol, shares, stock_price, total_price) VALUES (?, ?, ?, ?, ?)", session["user_id"], symbol, shares, price["price"],totalPrice)
        db.execute("INSERT INTO history(id_user, symbol, shares, stock_price,transaction_type, transaction_time) VALUES(?,?,?,?,?,datetime('now'))",session["user_id"], symbol, shares, price["price"],"Buy")


        return redirect("/portafolio")





    else:
        return render_template("trade.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method=="POST":
        symbol= request.form.get("symbol")
        if not symbol:
            return apology("No Symbol")
        stocks_owned = db.execute("SELECT symbol FROM portafolio WHERE user_id = ?", session["user_id"])

        stock = db.execute("SELECT shares FROM portafolio WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)
        if not stock:
            return apology("You don't have that stock")

        shares= request.form.get("shares")
        if not shares:
            return apology("Insert valid number of shares")
        shares= int(shares)
        if shares<=0:
            return apology("Insert positive number of shares")
        shareSS=int(stock[0]["shares"])
        if shareSS<shares:
             return apology("Don't have enough shares to sell")

        price= lookup(symbol)
        totalPrice= shares * price["price"]
        totalPrice= int(totalPrice)
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", totalPrice, session["user_id"])
        db.execute("UPDATE portafolio SET shares = shares - ? WHERE user_id = ? AND symbol = ?", shares, session["user_id"], symbol)

        sharesAfter = db.execute("SELECT shares FROM portafolio WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)

        shareSSAfter=int(sharesAfter[0]["shares"])
        if shareSSAfter==0:
            db.execute("DELETE FROM portafolio WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)

        db.execute("INSERT INTO history(id_user, symbol, shares, stock_price,transaction_type, transaction_time) VALUES(?,?,?,?,?,datetime('now'))",session["user_id"], symbol, shares, price["price"],"Sell")

        return redirect("/portafolio")
    else:
        stocks_owned = db.execute("SELECT symbol,shares FROM portafolio WHERE user_id = ?", session["user_id"])
        print(stocks_owned)
        return render_template("trade.html", stocks_owned=stocks_owned)


@app.route("/buy_crypto", methods=["GET", "POST"])
@login_required
def buy_crypto():
    """Buy crypto"""
    if request.method == "POST":
        symbol = request.form.get("symbol")
        if not symbol:
            return apology("No Symbol")
        price = lookup(symbol)
        if price is None:
            return apology("Symbol doesn't exist")
        shares = request.form.get("shares")
        shares = float(shares)
        if shares <= 0:
            return apology("Insert positive number of Cryptos")


        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = float(cash[0]['cash'])
        totalPrice = shares * price["price"]

        if cash < totalPrice:
            return apology("No Enough cash")

        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", totalPrice, session["user_id"])

        symboLL = db.execute("SELECT symbol FROM crypto_portfolio WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)

        if len(symboLL) != 0:
            db.execute("UPDATE crypto_portfolio SET shares = shares + ?, total_price = total_price + ? WHERE user_id = ? AND symbol = ?", shares, totalPrice, session["user_id"], symbol)
        else:
            db.execute("INSERT INTO crypto_portfolio (user_id, symbol, shares, stock_price, total_price) VALUES (?, ?, ?, ?, ?)", session["user_id"], symbol, shares, price["price"], totalPrice)

        db.execute("INSERT INTO history(id_user, symbol, shares, stock_price, transaction_type, transaction_time) VALUES(?,?,?,?,?,datetime('now'))", session["user_id"], symbol, shares, price["price"], "Buy")

        return redirect("/portafolio")

    else:
        return render_template("tradecrypto.html")

@app.route("/sell_crypto", methods=["GET", "POST"])
@login_required
def sell_crypto():
    if request.method=="POST":
        symbol= request.form.get("symbol")
        if not symbol:
            return apology("No Symbol")
        stocks_owned = db.execute("SELECT symbol FROM crypto_portfolio WHERE user_id = ?", session["user_id"])

        stock = db.execute("SELECT shares FROM crypto_portfolio WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)
        if not stock:
            return apology("You don't have that stock")

        shares= request.form.get("shares")
        if not shares:
            return apology("Insert valid number of shares")
        shares= float(shares)
        if shares<=0:
            return apology("Insert positive number of shares")
        shareSS=float(stock[0]["shares"])
        if shareSS<shares:
             return apology("Don't have enough shares to sell")

        price= lookup(symbol)
        totalPrice= shares * price["price"]
        totalPrice= int(totalPrice)
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", totalPrice, session["user_id"])
        db.execute("UPDATE crypto_portfolio SET shares = shares - ? WHERE user_id = ? AND symbol = ?", shares, session["user_id"], symbol)

        sharesAfter = db.execute("SELECT shares FROM crypto_portfolio WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)

        shareSSAfter=float(sharesAfter[0]["shares"])
        if shareSSAfter==0:
            db.execute("DELETE FROM crypto_portfolio WHERE user_id = ? AND symbol = ?", session["user_id"], symbol)

        db.execute("INSERT INTO history(id_user, symbol, shares, stock_price,transaction_type, transaction_time) VALUES(?,?,?,?,?,datetime('now'))",session["user_id"], symbol, shares, price["price"],"Sell")

        return redirect("/portafolio")
    else:
        stocks_owned = db.execute("SELECT symbol,shares FROM crypto_portfolio WHERE user_id = ?", session["user_id"])
        print(stocks_owned)
        return render_template("tradecrypto.html", stocks_owned=stocks_owned)
@app.route("/crypto_portfolio")
@login_required
def crypto_portfolio():
    user_id = session["user_id"]
    # Incluir stock_price y total_price en la consulta
    portfolio = db.execute("SELECT symbol, shares, stock_price, total_price FROM crypto_portfolio WHERE user_id = ?", user_id)
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

    total_stocks_value = 0
    for stock in portfolio:
        current_data = lookup(stock["symbol"])
        stock["current_price"] = current_data["price"]
        stock["purchase_price"] = stock["stock_price"]
        stock["total_current_value"] = stock["current_price"] * stock["shares"]
        stock["daily_return"] = (stock["current_price"] - stock["purchase_price"]) / stock["purchase_price"] * 100
        # Calcular average_cost_per_share usando total_price y shares
        stock["average_cost_per_share"] = stock["total_price"] / stock["shares"]
        stock["total_investment"] = stock["shares"] * stock["average_cost_per_share"]

        # Calcular el retorno total en porcentaje
        stock["total_return"] = (stock["total_current_value"] - stock["total_investment"]) / stock["total_investment"] * 100
        total_stocks_value += stock["total_current_value"]

    total_value = cash + total_stocks_value

    return render_template("crypto_portfolio.html", portfolio=portfolio, cash=cash, total_value=total_value)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    user_id = session["user_id"]
    history = db.execute("SELECT id_user, symbol, shares,stock_price, transaction_type,transaction_time FROM history WHERE id_user = ?", user_id)
    return render_template("history.html", history=history)



@app.route('/crypto_info/<symbol>')
@login_required
def crypto_info(symbol):
    # Aquí puedes agregar cualquier lógica adicional necesaria para obtener información sobre la criptomoneda
    return render_template('crypto_info.html', symbol=symbol)

@app.route("/crypto_market")
@login_required
def crypto_market():
    search_symbol = request.args.get('symbol')

    if search_symbol and search_symbol.strip():
        # Asegúrate de agregar '-USD' para buscar criptomonedas
        symbols = [f"{search_symbol.upper()}-USD"]
    else:
        # Lista de símbolos de criptomonedas para mostrar por defecto
        symbols = ['BTC-USD','ETH-USD', 'SOL-USD', 'ADA-USD', 'BNB-USD', 'XRP-USD']

    data = []
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        # Recuperar datos históricos
        hist_day = ticker.history(period="1d")
        hist_month = ticker.history(period="1mo")
        hist_6months = ticker.history(period="6mo")

        # Calcular variaciones de precios
        if not hist_day.empty and not hist_month.empty and not hist_6months.empty:
            price_last_day = hist_day['Close'].iloc[-1]
            price_first_day_month = hist_month['Close'].iloc[0]
            price_last_day_month = hist_month['Close'].iloc[-1]
            price_first_day_6months = hist_6months['Close'].iloc[0]
            price_last_day_6months = hist_6months['Close'].iloc[-1]

            # Calcular las variaciones
            variation_day = ((price_last_day - price_last_day) / price_last_day) * 100
            variation_month = ((price_last_day_month - price_first_day_month) / price_first_day_month) * 100
            variation_6months = ((price_last_day_6months - price_first_day_6months) / price_first_day_6months) * 100

            # Añadir los datos calculados a la lista `data`
            data.append({
                'symbol': symbol,
                'price': price_last_day,
                'variation_day': variation_day,
                'variation_month': variation_month,
                'variation_6months': variation_6months
            })
    return render_template('crypto_market.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        rows = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method=="POST":
        #Get username and password and check errors
        username =request.form.get("username")
        if not username:
            return apology("No username")
        password =request.form.get("password")
        confirmation= request.form.get("confirmation")
        if not password:
            return apology("No password")
        if password!=confirmation:
            return apology("Password don't match")
        hashedpassword = generate_password_hash(password)
        rows = db.execute(
            "SELECT username FROM users WHERE username= ?", username)
        if len(rows)!=0:
            return apology("Username already taken")


        db.execute("INSERT INTO users(username,hash)VALUES(?,?)",username,hashedpassword)
        rows = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = rows[0]["id"]
        return redirect("/")


    else:
        return render_template("register.html")




@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    if request.method=="POST":
        deposit= int(request.form.get("deposit"))
        if not deposit:
            return apology("No deposit")
        if deposit<=0:
            return apology("Insert positive number of cash")
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", deposit, session["user_id"])

        return redirect("/")

    else:
         return render_template("deposit.html")
