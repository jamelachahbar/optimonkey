# filename: plot_stocks.py
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

# Define the stock symbols and the date range
stocks = ['NVDA', 'TSLA']
start_date = datetime(datetime.now().year, 1, 1)

# Fetch the stock data
data = yf.download(stocks, start=start_date)

# Calculate the YTD percentage change
ytd_change = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100

# Plotting
plt.figure(figsize=(10, 5))
ytd_change.plot(kind='bar', color=['blue', 'orange'])
plt.title('YTD Percentage Change in Stock Prices (NVDA and TSLA)')
plt.ylabel('Percentage Change (%)')
plt.xticks(rotation=0)
plt.grid(axis='y')

# Save the plot
plt.savefig('ytd_stock_change.png')
plt.close()