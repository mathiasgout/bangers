import os
import unittest
from  sqlalchemy.sql.expression import func
from src.services import session_scope
from src.twitter_bot import ExtractTweets, QuoteTweet, ReplyTweet
from src.models import Tweets


class TestExtractTweets(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.user_id = 813286
        cls.extractor = ExtractTweets(env="dev")
        cls.tweets_info = cls.extractor._extract_last_tweets_info_from_user_id(user_id=cls.user_id)

    @classmethod
    def tearDownClass(cls):
        # Suppressions de tous les tweets de la database
        with session_scope(env="dev") as session:
            session.query(Tweets).delete()
        print("Tweets deleted from database")

    def test_tweets_info_type(self):
        self.assertTrue(isinstance(self.tweets_info, list))

    def test_tweet_info_keys(self):
        self.assertIn("user_id", self.tweets_info[0].keys())
        self.assertIn("screen_name", self.tweets_info[0].keys())
        self.assertIn("tweet_id", self.tweets_info[0].keys())
        self.assertIn("url", self.tweets_info[0].keys())
        self.assertIn("created_at", self.tweets_info[0].keys())
        self.assertIn("extracted_at", self.tweets_info[0].keys())
        self.assertIn("used", self.tweets_info[0].keys())
        self.assertIn("deleted", self.tweets_info[0].keys())
        self.assertIn("text", self.tweets_info[0].keys())
        self.assertIn("mentions", self.tweets_info[0].keys())

    def test_tweet_info_values(self):
        self.assertTrue(self.tweets_info[0]["user_id"] == self.user_id)
        self.assertTrue(self.tweets_info[0]["used"] == 0)
        self.assertTrue(self.tweets_info[0]["deleted"] == 0)
        self.assertIsNotNone(self.tweets_info[0]["screen_name"])
        self.assertIsNotNone(self.tweets_info[0]["tweet_id"])
        self.assertIsNotNone(self.tweets_info[0]["url"])
        self.assertIsNotNone(self.tweets_info[0]["created_at"])
        self.assertIsNotNone(self.tweets_info[0]["extracted_at"])
        self.assertIsNotNone(self.tweets_info[0]["text"])
        self.assertIsNotNone(self.tweets_info[0]["mentions"])

    def test_insert_last_tweets_into_db(self):
        self.extractor.insert_last_tweets_into_db(user_id=self.user_id)
        with session_scope(env="dev") as session:
            random_tweet = session.query(Tweets).filter(Tweets.user_id == self.user_id).order_by(func.random()).first()
            self.assertEqual(random_tweet.user_id, self.user_id)
            self.assertTrue(random_tweet.used == 0)
            self.assertTrue(random_tweet.deleted == 0)


class TestTweetPoster(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with session_scope(env="dev") as session:
            tweet1 = Tweets(user_id=813286, screen_name="@BarackObama", tweet_id=1493653951752900611, text="truc", mentions="[]", url="https://twitter.com/BarackObama/status/1493653951752900611", created_at=1, extracted_at=2, used=0, deleted=0)
            session.add_all([tweet1])

    @classmethod
    def tearDownClass(cls):
        # Suppressions de tous les tweets de la database
        with session_scope(env="dev") as session:
            session.query(Tweets).delete()
        print("Tweets deleted from database")

    def setUp(self):
        self.quote_poster = QuoteTweet(env="dev")
        self.reply_poster = ReplyTweet(env="dev")

    def test_form_tweet_text(self):
        self.assertTrue(isinstance(self.quote_poster._form_tweet_text(), str))

    def test_check_if_tweet_exists(self):
        self.assertTrue(self.quote_poster._check_if_tweet_exists(tweet_id=1491925070163365896))
        self.assertFalse(self.quote_poster._check_if_tweet_exists(tweet_id=-1))
    
    def test_tweet_used_to_1(self):
        self.quote_poster.post_tweet(user_id=813286)
        with session_scope(env="dev") as session:
            tweet = session.query(Tweets).filter(Tweets.tweet_id == 1493653951752900611).first()
            self.assertEqual(tweet.used, 1)

    def test_tweet_error(self):
        with self.assertRaises(Exception) as context:
            self.quote_poster.post_tweet(user_id=1)


