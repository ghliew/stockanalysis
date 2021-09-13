# main.py
"""Functions to grab stocks data and features"""
import yfinance as yf
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as  plt
from pandas_datareader import data as pdr

yf.pdr_override() # <== that's all it takes :-)

def get_rsi(ticker):
    enddate = dt.datetime.now()
    startdate = dt.datetime.now() - relativedelta(years=1)
    df = pdr.get_data_yahoo(ticker, start=startdate, end=enddate)
    change = df['Adj Close'].diff(1)
    change.dropna(inplace=True)
    gain = change.copy()
    loss = change.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    days=14
    average_gain = gain.rolling(window=days).mean()
    average_loss = abs(loss.rolling(window=days).mean())
    relative = average_gain/average_loss
    RSI = 100.0 - (100.0/(1.0+relative))
    
    combined = pd.DataFrame()
    combined['Adj Close']= df['Adj Close']
    combined['RSI'] = RSI
    
    plt.figure(figsize=(12,8))
    ax1 = plt.subplot(211)
    ax1.plot(combined.index, combined['Adj Close'], color='lightgray')
    ax1.set_title("Adjusted Close Price", color='white')
    ax1.grid(True)
    ax1.set_axisbelow(True)
    ax1.set_facecolor('black')
    ax1.figure.set_facecolor('#121212')
    ax1.tick_params(axis='x', colors='white')
    ax1.tick_params(axis='y', colors='white')
    
    plt.figure(figsize=(12,8))
    ax2 = plt.subplot(212, sharex=ax1)
    ax2.plot(combined.index, combined['RSI'], color='lightgray')
    ax2.set_title("RSI", color='white')
    ax2.grid(False)
    ax2.set_axisbelow(True)
    ax2.set_facecolor('black')
    ax2.figure.set_facecolor('#121212')
    ax2.axhline(30, linestyle='solid', color='red')
    ax2.axhline(70, linestyle='solid', color='green')
    ax2.tick_params(axis='x', colors='white')
    ax2.tick_params(axis='y', colors='white')


