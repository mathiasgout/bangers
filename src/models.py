import sqlalchemy as _sqlalchemy
from sqlalchemy.ext.declarative import declarative_base as _declarative_base

DB_NAME = "database.db"

engine = _sqlalchemy.create_engine(f'sqlite:///{DB_NAME}')
Base = _declarative_base()

class Tweets(Base):
    __tablename__ = "tweets"

    id = _sqlalchemy.Column(_sqlalchemy.Integer, primary_key=True)
    user_id= _sqlalchemy.Column(_sqlalchemy.Integer)
    screen_name = _sqlalchemy.Column(_sqlalchemy.String(100))
    tweet_id = _sqlalchemy.Column(_sqlalchemy.Integer)
    text = _sqlalchemy.Column(_sqlalchemy.String(1000))
    mentions = _sqlalchemy.Column(_sqlalchemy.String(1000))
    url = _sqlalchemy.Column(_sqlalchemy.String(1000))
    created_at = _sqlalchemy.Column(_sqlalchemy.Integer)
    extracted_at = _sqlalchemy.Column(_sqlalchemy.Integer)
    used = _sqlalchemy.Column(_sqlalchemy.Integer)
    deleted = _sqlalchemy.Column(_sqlalchemy.Integer)

    def __repr__(self) -> str:
        return f"<Tweets screen_name={self.screen_name} tweet_id={self.tweet_id} text={self.text}>"

