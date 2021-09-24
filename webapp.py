import streamlit as st
import stocksutil as sutil
from tweetlistener import TweetListener
import yfinance as yf
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as  plt
import tweepy
import keys
from textblob import TextBlob
import preprocessor as p
from tweetlistener import TweetListener
from pandas_datareader import data as pdr
from stocksutil import get_google_link
from stocksutil import get_yahoo_link

yf.pdr_override() # <== that's all it takes :-)

#System Strings
TEXT_PRICE = '''## {} - {} {}
#### {} - {}
'''
TEXT_RSI = '''## {} {}
### {}
'''
TEXT_DEFAULT_RSI = 'Current RSI:'

TEXT_LINK = '''[Google News]({}), [Yahoo Finance]({})'''

def get_stock_df(ticker):
    enddate = dt.datetime.now()
    startdate = dt.datetime.now() - relativedelta(years=1)
    df = pdr.get_data_yahoo(ticker, start=startdate, end=enddate)
    return df

def get_rsi_df(df_c):
    df = df_c.copy()
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
    
    df_combined = pd.DataFrame()
    df_combined['Adj Close']= df['Adj Close']
    df_combined['RSI'] = RSI

    return df_combined


def get_rsi_fig(df_combined):
    combined = df_combined    
    fig, axs = plt.subplots(nrows=2, ncols=1, figsize=(12,8))
    axs[0].plot(combined.index, combined['Adj Close'], color='lightgray')
    axs[0].set_title("Adjusted Close Price", color='white')
    axs[0].grid(True)
    axs[0].set_axisbelow(True)
    axs[0].set_facecolor('black')
    axs[0].figure.set_facecolor('#121212')
    axs[0].tick_params(axis='x', colors='white')
    axs[0].tick_params(axis='y', colors='white')
    
    axs[1].plot(combined.index, combined['RSI'], color='lightgray')
    axs[1].set_title("RSI", color='white')
    axs[1].grid(False)
    axs[1].set_axisbelow(True)
    axs[1].set_facecolor('black')
    axs[1].figure.set_facecolor('#121212')
    axs[1].axhline(30, linestyle='solid', color='red')
    axs[1].axhline(70, linestyle='solid', color='green')
    axs[1].tick_params(axis='x', colors='white')
    axs[1].tick_params(axis='y', colors='white')
    
    return fig

def get_ls_symbol(df_sym):
    '''Return a str list that will be displayed in selectbox'''
    ls_symbol = (df_sym['Symbol'] + ' - ' + df_sym['Security']).to_list()
    return ls_symbol

def get_price_chg_str(df_sym):
    '''Return a str with stock price and percentage change from yesterday
    Args:
        df_sym (pandas.DataFrame)
    Returns:
        pchange_str (str)
    '''
    close_prev = df_sym['Close'].values[-2]
    close_latest =  df_sym['Close'].values[-1]
    price_chg = (close_latest/close_prev-1)*100
    price_chg_color = 'green' if price_chg>0 else 'red'
    price_chg_sign = '+' if price_chg>0 else ''
    price_chg_str = '<span style="color:{}">{}{:.2f}%</span>'.format(price_chg_color, price_chg_sign, price_chg)
    return price_chg_str

def get_current_rsi_str(df_rsi):
    '''Return a str with current RSI value
    Args:
        df_rsi (pandas.DataFrame)
    Returns:
        rsi_str (str)
    '''
    rsi = df_rsi['RSI'].values[-1]
    if rsi >= 70:
        rsi_color = 'green'
        rsi_desc = 'Overbought! Might be a good time to SELL'
    elif rsi <= 30:
        rsi_color = 'red'
        rsi_desc = 'Oversold! Might be a good time to BUY'
    else:
        rsi_color = 'black'
        rsi_desc = ''
    rsi_str = '<span style="color:{}">{:.2f} </span>'.format(rsi_color, rsi)
    return rsi_str, rsi_desc

# @st.cache()
def get_tweets_sentimental(text, num_tweet):
    auth = tweepy.OAuthHandler(keys.consumer_key, keys.consumer_secret)
    auth.set_access_token(keys.access_token, keys.access_token_secret)  
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True) 
    search_key = text
    limit = num_tweet
    sentiment_dict = {'positive':0, 'negative':0, 'neutral':0}
    tweet_listener= TweetListener(api, sentiment_dict, search_key, limit)
    tweet_stream = tweepy.Stream(auth=api.auth, listener = tweet_listener)
    tweet_stream.filter(track=[search_key], languages=['en'], is_async=False)
    return sentiment_dict


@st.cache()
def get_snp_data():
    SNP_TABLE_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    html = pd.read_html(SNP_TABLE_URL, header=0)
    df = html[0]
    return df

### Streamlit UI ###
st.set_page_config(page_title="Stock Brew ☕")

st.title("Stock Brew ☕")

st.markdown('''
"Rule No.1: Never lose money. Rule No. 2: Never forget rule No.1." - Warren Buffett \n
In order to not lose money in the stock market, it is really important to both enter the market at the right time and take profit when necessary. \n
This application provides:
* List of S&P500 Companies
* Latest price with RSI analysis
* Live Tweets Sentimental analysis
* Useful links
''')

df = get_snp_data()
sector = df.groupby('GICS Sector')

# Sidebar Title
st.sidebar.header('S&P 500')
# Sidebar - Sector selection
sorted_sector_unique = sorted( df['GICS Sector'].unique() )
selected_sector = st.sidebar.multiselect('Sector', sorted_sector_unique, sorted_sector_unique)
# Sector filtered dataframe
df_selected_sector = df[ (df['GICS Sector'].isin(selected_sector)) ]

st.header('S&P500')
with st.expander("📘 - See S&P500 Explanation"):
    st.write('''The Standard and Poor's 500, or simply the S&P 500, is a stock market index tracking the performance of 500 large companies 
            listed on stock exchanges in the United States. It is one of the most commonly followed equity indices.''')
st.write('Data Dimension: ' + str(df_selected_sector.shape[0]) + ' rows and ' + str(df_selected_sector.shape[1]) + ' columns.')
st.write(df_selected_sector)

ls_symbol_modified = get_ls_symbol(df_selected_sector)
ls_symbol_modified = ls_symbol_modified + ['Select a Ticker Symbol...']
ticker = st.selectbox("", ls_symbol_modified, index=len(ls_symbol_modified)-1).split()[0]
df_ticker = df_selected_sector[df_selected_sector['Symbol']==ticker]

if ticker!="Select":
    df_ticker_price = get_stock_df(ticker)
    price_chg_str = get_price_chg_str(df_ticker_price)
    st.write(TEXT_PRICE.format(
        ticker,
        *df_ticker['Security'],
        price_chg_str,
        *df_ticker['GICS Sector'],
        *df_ticker['GICS Sub-Industry']
        ), 
        unsafe_allow_html=1)
    df_rsi = get_rsi_df(df_ticker_price)
    rsi_str, rsi_desc = get_current_rsi_str(df_rsi)
    st.write(TEXT_RSI.format(TEXT_DEFAULT_RSI, rsi_str, rsi_desc), unsafe_allow_html=1)
    fig = get_rsi_fig(df_rsi)
    with st.expander("📘 - See RSI Explanation"):
        st.write('''The relative strength index (RSI) is a momentum indicator 
                used in technical analysis that measures the magnitude of recent price changes 
                to evaluate overbought or oversold conditions 
                in the price of a stock or other asset.
                \nGenerally, when the RSI surpasses the horizontal 30 reference level, 
                it is a bullish sign, and when it slides below the horizontal 70 reference level, 
                it is a bearish sign''')
    st.pyplot(fig)

    #Links to Yahoo Finance and Google News
    with st.expander("📘 - Useful Links"):
        st.write(TEXT_LINK.format(get_google_link,get_yahoo_link))

    #Tweet Sentimental Analysis
    st.header('Live Tweet Sentimental Analysis')
    user_input = st.text_input("Enter word to search below (ex. Tesla), search time will depend on live tweets" )
    num_tweet = st.slider("Number of Tweets", 1, 5, 3, 1)
    if st.button("Start searching for Tweets"):
        sentiment_dict= get_tweets_sentimental(user_input, num_tweet)
        st.write(f'Tweet sentiment for "{user_input}"')
        st.write('Positive:', sentiment_dict['positive'])
        st.write(' Neutral:', sentiment_dict['neutral'])
        st.write('Negative:', sentiment_dict['negative'])

