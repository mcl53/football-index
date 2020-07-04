import os
from datetime import datetime
import pandas as pd
from fi_api_calls import get_media_scores, get_player_price_history


def save_player_prices(player_name, player_prices):
	exists = os.path.exists(f"player_prices/{player_name}.csv")
	if exists:
		old_player_prices = read_player_prices(player_name)
		current_date = datetime.now()
		current_date.replace(hour=0, minute=0, second=0, microsecond=0)
		current_epoch = datetime.timestamp(current_date)
		last_download_time = old_player_prices.iloc[len(old_player_prices) - 1]["time"]
		if current_epoch - last_download_time > 86400:
			new_prices_trimmed = player_prices.iloc[len(old_player_prices):]
			player_prices = player_prices.append(new_prices_trimmed)
	
	if len(player_prices) > 0:
		player_prices.to_csv(f"player_prices/{player_name}.csv", index=False)


def read_player_prices(player):
	data = pd.read_csv(f"player_prices/{player}.csv", index_col=None)
	return data


def player_prices_need_update(player_name):
	exists = os.path.exists(f"player_prices/{player_name}.csv")
	if exists:
		old_player_prices = read_player_prices(player_name)
		current_date = datetime.now()
		current_date.replace(hour=0, minute=0, second=0, microsecond=0)
		current_epoch = datetime.timestamp(current_date)
		last_download_time = old_player_prices.iloc[-1]["time"]
		if current_epoch - last_download_time < 86400:
			return False
		else:
			return True
		

def update_players(players):
	all_player_prices = get_player_price_history(players)

	for player in all_player_prices:
		player_name, player_prices = next(iter(player.items()))

		save_player_prices(player_name, player_prices)


def save_media_scores(dates):
	for date in dates:
		exists = os.path.exists(f"media_scores/{date}.csv")
		if not exists:
			media_scores = get_media_scores(date)
			media_scores.to_csv(f"media_scores/{date}.csv", index=None)


def read_media_scores(date):
	media_scores = pd.read_csv(f"media_scores/{date}.csv")
	return media_scores
