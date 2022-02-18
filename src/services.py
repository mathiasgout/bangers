import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database
from .config import config


def get_engine(user: str, password: str, host: str, port: str, database: str):
    url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    if not database_exists(url):
        create_database(url)
    
    engine = create_engine(url, echo=False)
    return engine

def get_engine_from_settings(env : str = "prod"):
    keys = ["user", "password", "host", "port", "database"]
    filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "database.ini")
    if env=="prod":
        settings = config(filename=filename, section="postgresql-prod")
    elif env=="dev":
        settings = config(filename=filename, section="postgresql-dev")
    else:
        raise Exception("'env' must be equals to 'prod' or 'dev'")
    
    if not all(key in keys for key in settings.keys()):
        raise Exception("Bad config file")

    return get_engine(settings["user"], settings["password"], settings["host"], settings["port"], settings["database"])

@contextmanager
def session_scope(env : str = "prod"):
    try:
        engine = get_engine_from_settings(env=env)
        session = sessionmaker(bind=engine)()
        print(f"Session {session} opened")
        yield session
    except Exception as e:
        session.rollback()
        print(f"Session {session} rollbacked")
        raise e
    finally:
        session.commit()
        print(f"Session {session} committed")
        session.close()
        print(f"Session {session} closed")

