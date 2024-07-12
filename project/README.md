#Project Title: My Own Personal Broker
####The URL of your video: https://www.youtube.com/watch?v=DlM1rxgDPtM
####Description of your project:
My project aims to recreate a Broker and its functions, allowing the user to create unreal scenarios and gain experience in the world of investments without taking risks. To achieve this, I used Python, Flask, SQL, and HTML. It is based on the pset called "finance," to build upon that foundation and enhance it significantly, changing its design, greatly improving its existing functions, and adding new features, such as the ability to operate in the crypto world.

In app.py, the backend of my project is defined. It is divided by each action that can be performed in the broker. It is quite extensive, so I will divide it and briefly explain each function.

In templates, the HTML templates used for the website are stored, which contain the design of each page and the available functions on each of them. In static, the "style.css" file is found, which contains the used design. In finance.db, the tables created with SQLite3 are located, used to store information. These include: users (storing user information such as their name, password, and cash), portfolio (storing each user's stock portfolio), crypto_portfolio (storing each user's cryptocurrency portfolio), and history (storing the user's transaction history). In helpers.py, there are some purely auxiliary functions.

The first part defines the functions that aim to operate in the stock market:

The function "Quotes" is used to search for certain symbols using the yfinance API and return their information to display in quotes.html. In quotes.html, general market information is also shown using a widget from TrendingView. The function "details" serves to pass the chosen symbol to the quote_detail.html template once the user selects a stock to analyze, and this template again uses the TrendingView Widgets.

The function "get_financial_news" uses the GetNews API. Then, in "financial_news," it collects these news articles and passes them to financial_news.html to show them to the user.

The function "Portfolio" uses the "portfolio" table created in SQL to extract information, perform some calculations, and pass it to portfolio.html. In this template, the user’s portfolio of stocks is displayed.

The function "buy" is designed to purchase stocks in the market. It uses the yfinance API to extract price information, adds the purchased stock to the portfolio, and deducts the spent money from the user's cash. It also includes certain precautions to ensure the user enters valid values. The function "sell" is similar but performs the opposite action. It is designed to show the user's stocks, allow them to select which one to sell, and effectively sell it. Both functions display trade.html, a template designed for the user to access these operations.

The function "history" aims to save the user's transaction information. It obtains information from a SQL table called history and displays it in history.html, a template that shows the user their transaction history.

The function "deposit" has the sole purpose of allowing money to be deposited into the account to purchase the necessary stocks.

The functions designed for the crypto world are as follows:

The function "buy_crypto" is developed to do the same as the "buy" function but for cryptocurrencies. The difference is that it uses a different portfolio and allows the user to purchase less than one unit. "Sell_crypto" is similar but performs the opposite action. Both functions display tradecrypto.html.
The function "crypto_market" is similar to "Quotes" but provides cryptocurrency information. It directs to crypto_market.html.
The function "Crypto_info" is similar to "details" but for the selected cryptocurrency. It directs to crypto_info.html.

The final part defines functions for the website's operation:
The function "Register" allows the user to create an account when first entering. It directs to register.html.
The function "Login" enables the user to have an account where their portfolio is saved once they log out. It directs to login.html.
The function "Logout" allows the user to log out of their account and log in with another one.


