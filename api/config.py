import os

DB_URI = os.environ.get("DB_URI", 'sqlite:///elo.db')
VERBOSE_SQL = os.environ.get("VERBOSE_SQL", False)
DEBUG = os.environ.get("DEBUG", True)
