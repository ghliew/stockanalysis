from dotenv import load_dotenv
import os

load_dotenv()  # take environment variables from .env.
# environment variables

consumer_key= os.getenv("consumer_key")
consumer_secret= os.getenv("consumer_secret")
access_token= os.getenv("access_token")
access_token_secret= os.getenv("access_token_secret")

mapquest_key= os.getenv("mapquest_key")