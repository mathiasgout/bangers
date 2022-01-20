import os as _os
from typing import Dict
from .models import DB_NAME, Base, engine
from .texts import TWEETS_TEXTS
import datetime as _datetime
import requests as _request
import random as _random
from sqlalchemy import create_engine as _create_engine
from sqlalchemy.orm import sessionmaker as _sessionmaker

def create_database():
    DIR_PATH = _os.path.dirname(_os.path.realpath(__file__))
    if not _os.path.exists(_os.path.join(DIR_PATH,DB_NAME)):
        Base.metadata.create_all(engine)

def _form_tweet_text() -> str:
    return _random.choice(TWEETS_TEXTS)
    
def _extract_infos_from_tweet(tweet) -> Dict:
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
    tweet_info["created_at"] = int(_datetime.datetime.timestamp(tweet.created_at))
    tweet_info["extracted_at"] = int(_datetime.datetime.timestamp(_datetime.datetime.now()))
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

def _extract_media_id(tweet) -> int:
    media_id = tweet.entities["media"][0]["id"]
    return media_id

def _download_media(url: str, extension: str):
    r = _request.get(url)
    with open(f"media.{extension}", "wb") as f:
        f.write(r.content)

def _generate_db_session():
    engine = _create_engine(f'sqlite:///{DB_NAME}')
    Session = _sessionmaker(bind=engine)
    session = Session()

    return session

