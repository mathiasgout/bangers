import random
from src.services import create_database
from src.twitter_bot import insert_last_tweets_db, post_tweet, reply_tweet, quote_tweet, retweet_tweet

# Création de la database si elle n'existe pas
create_database()

user_id = 812926437032390656 
insert_last_tweets_db(user_id=user_id)
post_tweet(user_id=user_id, type_of_tweet_fn=random.choice([reply_tweet, quote_tweet, retweet_tweet]))
