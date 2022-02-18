from src import twitter_bot

user_id = 812926437032390656
extractor = twitter_bot.ExtractTweets()
extractor.insert_last_tweets_into_db(user_id=user_id)
tweet_poster = twitter_bot.ReplyTweet()
tweet_poster.post_tweet(user_id=user_id)