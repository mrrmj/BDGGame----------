# scraper/__init__.py
from .login import login_to_bdg
from .scrape_data import scrape_game_history

__all__ = ["login_to_bdg", "scrape_game_history"]  # Optional: defines what gets imported with `from scraper import *`