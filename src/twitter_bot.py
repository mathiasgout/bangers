import os as _os
from typing import Dict, List, Callable
import dotenv as _dotenv
import tweepy as _tweepy
import sqlalchemy as _sqlalchemy
from  sqlalchemy.sql.expression import func as _func
from .models import Tweets
from .services import _extract_infos_from_tweet, _generate_db_session, _form_tweet_text, _form_tweet_media, _download_medias, _get_media_urls_from_tweet, _remove_medias_directory

# Chargement des clefs du fichier .env en variable d'environnements
_dotenv.load_dotenv()


TWITTER_API_KEY = _os.environ["TWITTER_API_KEY"]
TWITTER_API_KEY_SECRET = _os.environ["TWITTER_API_KEY_SECRET"]
TWITTER_ACCESS_TOKEN = _os.environ["TWITTER_ACCESS_TOKEN"]
TWITTER_ACCESS_TOKEN_SECRET = _os.environ["TWITTER_ACCESS_TOKEN_SECRET"]


def _get_twitter_api() -> _tweepy.API:
    """Renvoie un objet API twitter en prennant en argument les clefs 

    Returns:
        _tweepy.API: l'objet API twitter
    """

    auth = _tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_KEY_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    twitter_api = _tweepy.API(auth, wait_on_rate_limit=True)

    return twitter_api

def _extract_tweet(tweet_id: int) -> _tweepy.models.Status:
    twitter_api = _get_twitter_api()

    return twitter_api.get_status(id=tweet_id, tweet_mode="extended")

def _extract_last_tweets(user_id: int, num_pages: int = 1, count: int = 20, since_tweet_id: int = None) -> List[Dict]:
    """Extrait les derniers tweets d'un utilisateur en fonction de son ID.

    Args:
        user_id (int): l'ID de l'utilisateur
        num_pages (int, optional): Nombre de page de tweets à extraire. Defaults to 1.
        count (int, optional): Nombre de tweets par page. Defaults to 20.
        since_tweet_id (int, optional): Seul les tweets avec un ID supérieur à since_tweet_id sont extraits. Defaults to None.

    Returns:
        List[Dict]: Liste de dictionnaire des informations importantes du tweet
    """
    twitter_api = _get_twitter_api()
    tweets_info = []
    for page in _tweepy.Cursor(twitter_api.user_timeline, user_id=user_id, count=count, since_id=since_tweet_id, include_rts=False, tweet_mode="extended").pages(num_pages):
        for tweet in page:
            if hasattr(tweet, 'retweeted'):
                if not tweet.retweeted:
                    tweet_info = _extract_infos_from_tweet(tweet)
                    tweets_info.append(tweet_info)

    return tweets_info

def _check_if_tweet_exists(tweet_id: int) -> bool:
    twitter_api = _get_twitter_api()
    
    it_exist = True
    try:
        twitter_api.get_status(id=tweet_id)
    except (_tweepy.errors.Forbidden, _tweepy.errors.NotFound):
        it_exist = False

    return it_exist

def _upload_medias() -> List[int]:
    twitter_api = _get_twitter_api()

    SRC_PATH = _os.path.dirname(_os.path.realpath(__file__))
    MEDIA_PATH = _os.path.join(SRC_PATH, "medias")
    media_ids = []
    for file_name in _os.listdir(MEDIA_PATH):
        media = twitter_api.media_upload(filename=_os.path.join(MEDIA_PATH, file_name))
        media_ids.append(media.media_id)

    return media_ids

def reply_tweet(tweet_selected: Tweets, text: str, media_ids: List[int]):
    twitter_api = _get_twitter_api()
    twitter_api.update_status(status=text, in_reply_to_status_id=tweet_selected.tweet_id, auto_populate_reply_metadata=True, media_ids=media_ids)

def quote_tweet(tweet_selected: Tweets, text: str, media_ids: List[int]):
    twitter_api = _get_twitter_api()
    twitter_api.update_status(status=text, attachment_url=tweet_selected.url, media_ids=media_ids)

def retweet_tweet(tweet_selected: Tweets, text: str, media_ids: List[int]):
    twitter_api = _get_twitter_api()
    twitter_api.retweet(id=tweet_selected.tweet_id)

def insert_last_tweets_db(user_id: int):
    session = _generate_db_session()

    # Check l'ID du dernier tweet de l'utilisateur
    last_tweet = session.query(Tweets).filter(Tweets.user_id == user_id).order_by(_sqlalchemy.desc(Tweets.tweet_id)).first()
    if last_tweet:
        tweets_info = _extract_last_tweets(user_id=user_id, num_pages=10, count=20, since_tweet_id=last_tweet.tweet_id)
    else:
        tweets_info = _extract_last_tweets(user_id=user_id, num_pages=10, count=20)

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
    session.commit()

def post_tweet(user_id : int, type_of_tweet_fn: Callable[[Tweets, str], None]):
    session = _generate_db_session()
    _remove_medias_directory()
    
    success = False
    while not success:
        tweet_selected = session.query(Tweets).filter(Tweets.user_id == user_id, Tweets.used == 0, Tweets.deleted == 0).order_by(_func.random()).first() 
        if _check_if_tweet_exists(tweet_id=tweet_selected.tweet_id):
            url_tweet_with_media = _form_tweet_media()
            tweet_id_with_media = url_tweet_with_media.split("/")[-1]
            if _check_if_tweet_exists(tweet_id=tweet_id_with_media):
                _download_medias(urls=_get_media_urls_from_tweet(tweet=_extract_tweet(tweet_id=tweet_id_with_media)))
                media_ids = _upload_medias()
            else:
                print(f"URL media : {url_tweet_with_media} DELETED")
                media_ids = []

            type_of_tweet_fn(text=_form_tweet_text(), tweet_selected=tweet_selected, media_ids=media_ids)
            tweet_selected.used = 1
            success = True 
        else:
            tweet_selected.deleted = 1

        session.commit()


