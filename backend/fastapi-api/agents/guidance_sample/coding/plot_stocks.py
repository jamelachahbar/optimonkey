# filename: plot_stocks.py
import yfinance as yf
import matplotlib.pyplot as plt
import datetime

# Define the stock symbols and the date range
stocks = ['NVDA', 'TSLA']
start_date = datetime.datetime(datetime.datetime.now().year, 1, 1)
end_date = datetime.datetime.now()

# Fetch the stock data
data = yf.download(stocks, start=start_date, end=end_date)['Adj Close']

# Plot the data
plt.figure(figsize=(10, 5))
for stock in stocks:
    plt.plot(data.index, data[stock], label=stock)

# Customize the plot
plt.title('YTD Stock Price Change: NVDA vs TSLA')
plt.xlabel('Date')
plt.ylabel('Adjusted Close Price')
plt.legend()
plt.grid()

# Save the plot
plt.savefig('ytd_stock_price_change.png')
plt.close()