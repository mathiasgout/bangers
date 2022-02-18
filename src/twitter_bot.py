import os
import datetime
import random
import dotenv as dotenv
import tweepy as tweepy
import sqlalchemy
from  sqlalchemy.sql.expression import func
from typing import Dict, List
from abc import ABC, abstractmethod
from .services import session_scope
from .models import Tweets
from .contents import TWEETS_TEXTS

# Chargement des clefs du fichier .env en variable d'environnements
dotenv.load_dotenv()

def get_twitter_api(env : str = "prod") -> tweepy.API:
    """Renvoie un objet API twitter en prennant en argument les clefs 

    Returns:
        _tweepy.API: l'objet API twitter
    """

    if env=="prod":
        auth = tweepy.OAuthHandler(os.environ["TWITTER_API_KEY"], os.environ["TWITTER_API_KEY_SECRET"])
        auth.set_access_token(os.environ["TWITTER_ACCESS_TOKEN"], os.environ["TWITTER_ACCESS_TOKEN_SECRET"])
    elif env=="dev":
        auth = tweepy.OAuthHandler(os.environ["TWITTER_API_KEY_DEV"], os.environ["TWITTER_API_KEY_SECRET_DEV"])
        auth.set_access_token(os.environ["TWITTER_ACCESS_TOKEN_DEV"], os.environ["TWITTER_ACCESS_TOKEN_SECRET_DEV"])  
    twitter_api = tweepy.API(auth, wait_on_rate_limit=True)

    return twitter_api

class ExtractTweets:
    env: str
    
    def __init__(self, env : str = "prod") -> None:
        self.env = env
        self.twitter_api = get_twitter_api(env=env)

    def _extract_infos_from_tweet(self, tweet: tweepy.models.Status) -> Dict:
        """Extrait les informations importantes d'un tweet et les renvoie sous forme d'un dictionnaire

        Args:
            tweet (tweepy.models.Status): un tweet

        Returns:
            Dict: les informations importantes du tweet
        """

        tweet_info = {}
        tweet_info["user_id"] = tweet.user.id
        tweet_info["screen_name"] = f"@{tweet.user.screen_name}"
        tweet_info["tweet_id"] = tweet.id
        tweet_info["url"] = f"https://twitter.com/twitter/statuses/{tweet.id}"
        tweet_info["created_at"] = int(datetime.datetime.timestamp(tweet.created_at))
        tweet_info["extracted_at"] = int(datetime.datetime.timestamp(datetime.datetime.now()))
        tweet_info["used"] = 0
        tweet_info["deleted"] = 0
        
        # Texte
        try:
            tweet_info["text"] = tweet.full_text
        except AttributeError:
            tweet_info["text"] = tweet.text
        except:
            tweet_info["text"] = None

        # Mentions
        mentions = []
        for mention in tweet.entities["user_mentions"]:
            try:
                mentions.append(f"@{mention['screen_name']}")
            except AttributeError:
                pass
        tweet_info["mentions"] = str(mentions)

        return tweet_info

    def _extract_last_tweets_info_from_user_id(self, user_id: int, num_pages: int = 10, count: int = 20, since_tweet_id: int = None) -> List[Dict]:
        """Extrait les derniers tweets d'un utilisateur en fonction de son ID.

        Args:
            user_id (int): l'ID de l'utilisateur
            num_pages (int, optional): Nombre de page de tweets à extraire. Defaults to 1.
            count (int, optional): Nombre de tweets par page. Defaults to 20.
            since_tweet_id (int, optional): Seul les tweets avec un ID supérieur à since_tweet_id sont extraits. Defaults to None.

        Returns:
            List[Dict]: Liste de dictionnaire des informations importantes du tweet
        """
        tweets_info = []
        for page in tweepy.Cursor(self.twitter_api.user_timeline, user_id=user_id, count=count, since_id=since_tweet_id, include_rts=False, tweet_mode="extended").pages(num_pages):
            for tweet in page:
                if hasattr(tweet, 'retweeted'):
                    if not tweet.retweeted:
                        tweet_info = self._extract_infos_from_tweet(tweet)
                        tweets_info.append(tweet_info)
        print(f"{len(tweets_info)} tweets extracted from user {user_id}")
        return tweets_info

    def insert_last_tweets_into_db(self, user_id: int):
        
        with session_scope(env=self.env) as session:
            last_tweet = session.query(Tweets).filter(Tweets.user_id == user_id).order_by(sqlalchemy.desc(Tweets.tweet_id)).first()
            if last_tweet:
                print(f"Last Tweet ID in database from user {last_tweet.user_id} ({last_tweet.screen_name}) is {last_tweet.tweet_id}")
                tweets_info = self._extract_last_tweets_info_from_user_id(user_id=user_id, num_pages=10, count=20, since_tweet_id=last_tweet.tweet_id)
            else:
                print(f"No tweets from user {user_id} in database")
                tweets_info = self._extract_last_tweets_info_from_user_id(user_id=user_id, num_pages=10, count=20)

            # Insertion des nouvelles lignes
            rows = []
            for tweet_info in tweets_info:
                row = Tweets(user_id=tweet_info["user_id"], 
                            screen_name=tweet_info["screen_name"], 
                            tweet_id=tweet_info["tweet_id"], 
                            text=tweet_info["text"], 
                            mentions=tweet_info["mentions"], 
                            url=tweet_info["url"],
                            created_at=tweet_info["created_at"], 
                            extracted_at=tweet_info["extracted_at"], 
                            used=tweet_info["used"], 
                            deleted=tweet_info["deleted"])

                rows.append(row)
            session.add_all(rows)
            print(f"{len(rows)} tweets from user {user_id} added to database.")


class TweetPoster(ABC):
    env: str

    def __init__(self, env : str = "prod") -> None:
        self.env = env
        self.twitter_api = get_twitter_api(env=env)

    def _form_tweet_text(self) -> str:
        return random.choice(TWEETS_TEXTS)

    def _check_if_tweet_exists(self, tweet_id: int) -> bool:
        it_exist = True
        try:
            self.twitter_api.get_status(id=tweet_id)
            print(f"Tweet with id : {tweet_id} exists")
        except Exception:
            it_exist = False
            print(f"Tweet with id : {tweet_id} does not exist")

        return it_exist

    @abstractmethod
    def post_tweet(self, user_id: int):
        pass


class QuoteTweet(TweetPoster):
    
    def __init__(self, env : str = "prod") -> None:
        super().__init__(env=env)

    def post_tweet(self, user_id: int):
        with session_scope(env=self.env) as session:
            # Get a tweet from user_id to reply to it
            success = False
            while not success:
                tweets = session.query(Tweets).filter(Tweets.user_id == user_id, Tweets.used == 0, Tweets.deleted == 0).order_by(sqlalchemy.desc(Tweets.created_at)).limit(20)
                tweet = tweets.from_self().order_by(func.random()).first()
                if tweet:
                    if self._check_if_tweet_exists(tweet_id=tweet.tweet_id):
                        tweet.used = 1
                        success = True
                    else:
                        tweet.deleted = 1  
                else:
                    raise Exception(f"No tweet from user {user_id} in database")
        
            text =self._form_tweet_text()
            attachment_url = tweet.url
            self.twitter_api.update_status(status=text, attachment_url=attachment_url)
            print(f"TWEET POSTED : type : Quote, text: '{text}', in reply to Tweet ID : {tweet.tweet_id}")


class ReplyTweet(TweetPoster):
    
    def __init__(self, env : str = "prod") -> None:
        super().__init__(env=env)

    def post_tweet(self, user_id: int):
        with session_scope(env=self.env) as session:
            # Get a tweet from user_id to reply to it
            success = False
            while not success:
                tweets = session.query(Tweets).filter(Tweets.user_id == user_id, Tweets.used == 0, Tweets.deleted == 0).order_by(sqlalchemy.desc(Tweets.created_at)).limit(20)
                tweet = tweets.from_self().order_by(func.random()).first()
                if tweet:
                    if self._check_if_tweet_exists(tweet_id=tweet.tweet_id):
                        tweet.used = 1
                        success = True
                    else:
                        tweet.deleted = 1  
                else:
                    raise Exception(f"No tweet from user {user_id} in database")
        
            text =self._form_tweet_text()
            in_reply_to_status_id = tweet.tweet_id
            self.twitter_api.update_status(status=text, in_reply_to_status_id=in_reply_to_status_id, auto_populate_reply_metadata=True)
            print(f"TWEET POSTED : type : Reply, text: '{text}', in reply to Tweet ID : {tweet.tweet_id}")
