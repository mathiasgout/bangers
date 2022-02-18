"""À exécuter lors de l'initialisation de nouvelles tables/database
"""
import os
from src import services, models

def init_databases():
    prod_engine = services.get_engine_from_settings()
    dev_engine = services.get_engine_from_settings(filename=os.path.join(os.path.dirname(os.path.realpath(__file__)), "tests/database.ini"))
    models.Base.metadata.create_all(prod_engine)
    models.Base.metadata.create_all(dev_engine)

if __name__ == "__main__":
    init_databases()