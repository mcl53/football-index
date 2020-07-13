import os
from datetime import datetime
import pandas as pd
import utils


def read_player_prices(player):
	data = pd.read_csv(f"player_prices/{player}.csv", index_col=None)
	return data


def read_media_scores(date):
	media_scores = pd.read_csv(f"media_scores/{date}.csv")
	return media_scores


def price_changes_for_date(datestr, future_prices=False):
	media_scores = read_media_scores(datestr)
	start_ts = utils.convert_datestr_to_timestamp(datestr)
	end_ts = start_ts + 86400

	columns = ["start_price", "end_price", "media_score"]

	if future_prices:
		one_ahead_ts = start_ts + (86400 * 2)
		two_ahead_ts = start_ts + (86400 * 3)
		columns += ["24h", "48h"]

	date_info = pd.DataFrame(columns=columns)

	for player in media_scores.iterrows():
		player_name = player[1]["urlname"]
		media_score = player[1]["score"]

		player_prices = read_player_prices(player_name)

		try:
			start_price = player_prices[player_prices["timestamp"] == start_ts]["close"].iloc[0]
			end_price = player_prices[player_prices["timestamp"] == end_ts]["close"].iloc[0]
			player_data = [start_price, end_price, media_score]

			if future_prices:
				one_day_price = player_prices[player_prices["timestamp"] == one_ahead_ts]["close"].iloc[0]
				two_day_price = player_prices[player_prices["timestamp"] == two_ahead_ts]["close"].iloc[0]
				player_data += [one_day_price, two_day_price]
		
		except IndexError:
			continue

		player_df = pd.DataFrame([player_data], columns=columns)

		date_info = date_info.append(player_df, ignore_index=True)

	return date_info


def read_all_data(dates_list=None):
	if dates_list is None:
		dates_list = utils.return_dates()
	
	all_data = pd.DataFrame(columns=["start_price", "end_price", "media_score", "24h", "48h"])

	for date in dates_list[0:-1]:
		this_date_prices = price_changes_for_date(date, future_prices=True)
		all_data = all_data.append(this_date_prices, ignore_index=True)
	
	return all_data


if __name__ == "__main__":
	standard = price_changes_for_date("20200701")
	with_future_prices = price_changes_for_date("20200701", future_prices=True)

	print(standard.iloc[0])
	print(with_future_prices.iloc[0])
