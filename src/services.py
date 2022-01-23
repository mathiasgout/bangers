import os as _os
import shutil as _shutil
from typing import Dict, List
from .models import DB_NAME, Base, engine
from .contents import TWEETS_TEXTS, TWEETS_MEDIAS
import datetime as _datetime
import requests as _request
import mimetypes as _mimetypes
import string as _string
import random as _random
from sqlalchemy import create_engine as _create_engine
from sqlalchemy.orm import sessionmaker as _sessionmaker

def create_database():
    SRC_PATH = _os.path.dirname(_os.path.realpath(__file__))
    if not _os.path.exists(_os.path.join(SRC_PATH,DB_NAME)):
        Base.metadata.create_all(engine)

def _form_tweet_text() -> str:
    return _random.choice(TWEETS_TEXTS)

def _form_tweet_media() -> str:
    return _random.choice(TWEETS_MEDIAS)
    
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

def _get_media_urls_from_tweet(tweet) -> List[str]:
    
    # Si pas de média
    if not hasattr(tweet, "extended_entities"):
        return []

    urls = []
    medias = tweet.extended_entities["media"]
    for media in medias:

        # Si c'est une vidéo
        if "video_info" in media:
            variants = media["video_info"]["variants"]
            bitrate_url = {}
            for variant in variants:
                if ("bitrate" in variant) and ("url" in variant):
                    bitrate_url[variant["bitrate"]] = variant["url"]

            # Garde la vidéo de meilleure qualité
            if bitrate_url:
                urls.append(bitrate_url[max(bitrate_url.keys())])

        # Si c'est une photo
        else:
            if "media_url_https" in media:
                urls.append(media["media_url_https"])
            elif "media_url" in media:
                urls.append(media["media_url"])

    return urls

def _download_media(url: str, dir_path: str):
    r = _request.get(url)
    content_type = r.headers['content-type']
    extension = _mimetypes.guess_extension(content_type)
    file_name = ''.join(_random.choice(_string.ascii_letters) for i in range(6)) + extension
    with open(_os.path.join(dir_path, file_name), "wb") as f:
        f.write(r.content)

def _download_medias(urls: List[str]):
    SRC_PATH = _os.path.dirname(_os.path.realpath(__file__))
    MEDIA_PATH = _os.path.join(SRC_PATH, "medias")
    if not _os.path.exists(MEDIA_PATH):
        _os.mkdir(MEDIA_PATH)
    
    for url in urls:
        _download_media(url, MEDIA_PATH)
    
def _remove_medias_directory():
    SRC_PATH = _os.path.dirname(_os.path.realpath(__file__))
    MEDIA_PATH = _os.path.join(SRC_PATH, "medias")
    try:
        _shutil.rmtree(MEDIA_PATH)
    except Exception:
        print(f"can not remove {MEDIA_PATH} directory")

def _generate_db_session():
    engine = _create_engine(f'sqlite:///{DB_NAME}')
    Session = _sessionmaker(bind=engine)
    session = Session()

    return session

