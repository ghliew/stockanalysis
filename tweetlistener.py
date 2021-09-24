# tweeetlisener.py
"""Receives tweets that match a search string and store in a list of dictionaries
containing each tweet's screen_name/text/location and do sentimental analysis on the tweets"""
import keys
import preprocessor as p 
import sys
from textblob import TextBlob
import tweepy
import pandas as pd
import streamlit as st

#System Strings
TEXT_TWEET = '''
#### {}
    *{}
    *{}
    *{}
'''

class TweetListener(tweepy.StreamListener):
    """Handles incoming Tweet stream."""

    def __init__(self, api, sentiment_dict, search_key, limit=10):
        """Configure the SentimentListener."""
        self.sentiment_dict = sentiment_dict
        self.tweet_count = 0
        self.search_key = search_key
        self.TWEET_LIMIT = limit

        # set tweet-preprocessor to remove URLs/reserved words
        p.set_options(p.OPT.URL, p.OPT.RESERVED) 
        super().__init__(api)  # call superclass's init
    
    def on_connect(self):
        print('Connection successful\n')
        
    def on_status(self, status):
        """Called when Twitter pushes a new tweet to you."""
        # get the tweet's text
        try:  
            tweet_text = status.extended_tweet.full_text
        except: 
            tweet_text = status.text

        # ignore retweets and if the search_ket is not in the tweet text
        if tweet_text.startswith('RT') or self.search_key.lower() not in tweet_text.lower():
            return

        tweet_text = p.clean(tweet_text)  # clean the tweet
        
        if status.lang !='en':
            tweet_text = TextBlob(tweet_text).translate()
            print(f' Translated: {tweet_text}')
        
        # update self.sentiment_dict with the polarity
        blob = TextBlob(tweet_text)
        if blob.sentiment.polarity > 0:
            sentiment = 'Positive'
            self.sentiment_dict['positive'] += 1 
        elif blob.sentiment.polarity == 0:
            sentiment = 'Neutral'
            self.sentiment_dict['neutral'] += 1 
        else:
            sentiment = 'Negative'
            self.sentiment_dict['negative'] += 1 
            
        # display the tweet
        name_str = f'Screen name: {status.user.screen_name}'
        status_str = f'Status: {tweet_text}'
        location_str = f'Location: {status.user.location}'
        sentiment_str = f'Sentiment: {sentiment}'
        st.write(TEXT_TWEET.format(name_str,
         status_str,
         location_str,
         sentiment_str
         ),
         unsafe_allow_html=1)
        # st.write()
        # st.write(f'Location: {status.user.location}')
        # st.write(f'Sentiment: {sentiment}')
        # print(f'Screen name: {status.user.screen_name}')
        # print(f'Status: {tweet_text}')
        # print(f'Location: {status.user.location}')
        # print(f'Sentiment: {sentiment}')
        # print('\n')

        self.tweet_count += 1  # track number of tweets processed

        # if TWEET_LIMIT is reached, return False to terminate streaming
        return self.tweet_count != self.TWEET_LIMIT