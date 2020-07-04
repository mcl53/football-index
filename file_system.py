import os
from datetime import datetime
import pandas as pd


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
