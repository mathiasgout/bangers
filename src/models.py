from sqlalchemy import Column, Integer, BigInteger, String
from sqlalchemy.ext.declarative import declarative_base 

Base = declarative_base()

class Tweets(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True)
    user_id= Column(BigInteger)
    screen_name = Column(String(100))
    tweet_id = Column(BigInteger)
    text = Column(String(1000))
    mentions = Column(String(1000))
    url = Column(String(1000))
    created_at = Column(Integer)
    extracted_at = Column(Integer)
    used = Column(Integer)
    deleted = Column(Integer)

    def __repr__(self) -> str:
        return f"<Tweets screen_name={self.screen_name} tweet_id={self.tweet_id} text={self.text}>"

