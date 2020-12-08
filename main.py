import datetime
import os
import pandas as pd
import pickle
from secrets import nn_default, nn_optimal, timezone
from utils import return_dates, to_currency
from mongo import read_media_scores, read_player_prices
from generate_models import train_price_predictor

import warnings
warnings.filterwarnings("ignore")

import pytz
tz = pytz.timezone(timezone)


def predict_stocks_to_buy(date, current_money, v=False):
	
	year = int(date[0:4])
	month = int(date[4:6])
	day = int(date[6:])
	date_obj = datetime.datetime(year, month, day)
	global tz
	tz_aware = tz.localize(date_obj, is_dst=None)
	timestamp = datetime.datetime.timestamp(date_obj) + tz_aware.tzinfo._dst.seconds
	
	media_scores = read_media_scores(date)
	
	with open("./price_prediction_model.p", "rb") as f:
		model = pickle.load(f)

	players_to_buy_columns = ["player", "buy_price", "predicted24h", "predicted48h", "actual24h", "actual48h", "sell_at", "percent_gain", "actual_gain"]
	players_to_buy = pd.DataFrame(columns=players_to_buy_columns)
	
	if v:
		print_columns = ["player", "pred_inc", "act_inc", "pred_percent", "act_percent", "pred_buy", "act_buy"]
		print_info = pd.DataFrame(columns=print_columns)
	
	for player_name in media_scores["urlname"]:
		data = read_player_prices(player_name)
		try:
			start_price = data.loc[data["timestamp"] == timestamp]["close"].iloc[0]
			end_price = data.loc[data["timestamp"] == (timestamp + 86400)]["close"].iloc[0]
		except IndexError:
			continue
		media_score = media_scores.loc[media_scores["urlname"] == player_name]["score"].iloc[0]
		score_sell = media_scores.loc[media_scores["urlname"] == player_name]["scoreSell"].iloc[0]
		
		test_data = pd.DataFrame([[start_price, end_price, media_score, score_sell]], columns=["start_price", "end_price", "media_score", "score_sell"])
		predicted_data = model.predict(test_data)[0]
		
		if predicted_data[0] > end_price or predicted_data[1] > end_price:
			buy_price = end_price
			try:
				actual24h = to_currency(data.loc[data["timestamp"] == (timestamp + (86400 * 2))]["close"].iloc[0])
				actual48h = to_currency(data.loc[data["timestamp"] == (timestamp + (86400 * 3))]["close"].iloc[0])
			except IndexError as e:
				print(timestamp, player_name)
				raise(e)
			if predicted_data[0] >= predicted_data[1]:
				sell_at = "actual24h"
				percent_gain = to_currency(((predicted_data[0] - buy_price) / buy_price) * 100)
				gain = to_currency(predicted_data[0] - buy_price)
			else:
				sell_at = "actual48h"
				percent_gain = to_currency(((predicted_data[1] - buy_price) / buy_price) * 100)
				gain = to_currency(predicted_data[1] - buy_price)
			buy_price = to_currency(buy_price)
			append = pd.DataFrame([[player_name, buy_price, predicted_data[0], predicted_data[1], actual24h, actual48h, sell_at, percent_gain, gain]], columns=players_to_buy_columns)
			players_to_buy = players_to_buy.append(append)
		
			if v:
				end_price = to_currency(end_price)
				pred_buy_price = to_currency((max(predicted_data)))
				actual_buy_price = to_currency(max(
					[data.loc[data["timestamp"] == (timestamp + (86400 * 2))]["close"].iloc[0],
					data.loc[data["timestamp"] == (timestamp + (86400 * 3))]["close"].iloc[0]]
				))
				pred_increase = to_currency(pred_buy_price - end_price)
				actual_increase = to_currency(actual_buy_price - end_price)
				pred_percentage = to_currency(pred_increase / end_price * 100)
				actual_percentage = to_currency(actual_increase / end_price * 100)
				if pred_buy_price > end_price:
					if pred_buy_price == predicted_data[0]:
						pred_buy = "24h"
					else:
						pred_buy = "48h"
				else:
					pred_buy = None
				
				if actual_buy_price > end_price:
					if actual_buy_price == predicted_data[0]:
						actual_buy = "24h"
					else:
						actual_buy = "48h"
				else:
					actual_buy = None
					
				player_info = pd.DataFrame([[player_name, pred_increase, actual_increase, pred_percentage, actual_percentage, pred_buy, actual_buy]], columns=print_columns)
				print_info = print_info.append(player_info)
	
	if v:
		for row in print_info.iterrows():
			print(row[1])
		
	if len(players_to_buy) > 0:
		players_to_buy = players_to_buy.sort_values(by="percent_gain", ascending=False)
		spendable = to_currency(current_money / 5)
		max_players_to_buy = 5
		top_index = 0
		top_few = 0
		bottom_index = 0
		for i in range(len(players_to_buy)):
			if players_to_buy.iloc[i]["percent_gain"] > 0.3 and players_to_buy.iloc[i]["actual_gain"] > 0.02:
				bottom_index = i + 1
				top_few = to_currency(sum(players_to_buy.iloc[top_index:bottom_index]["buy_price"]))
				if top_few > spendable:
					break
				elif i == max_players_to_buy:
					bottom_index = max_players_to_buy + top_index + 1
			else:
				bottom_index = i
				top_few = to_currency(sum(players_to_buy.iloc[top_index:bottom_index]["buy_price"]))
				break
			if i >= max_players_to_buy:
				break
				
		if top_few == 0:
			return 0
		
		no_of_shares = spendable // top_few
		if no_of_shares == 0:
			no_of_shares = 1
		spent = top_few * no_of_shares
		players_sold = players_to_buy.iloc[top_index:bottom_index]
		sales = 0
		for i in range(len(players_sold)):
			sales += players_sold.iloc[i].loc[players_sold.iloc[i]["sell_at"]]
		sales *= no_of_shares
		
		return sales - spent
	return 0

	
if __name__ == "__main__":
	no_months = 1
	dates_list = return_dates(no_months)
	
	# train_price_predictor(2, solver="adam")

	money = 1000
	for date in dates_list[0:-3]:
		print(date)
		change = predict_stocks_to_buy(date, money)
		print(f"Actual profit: £{change}")
		print()
		money += change

	print(f"Total money after {no_months} month(s): £{money}")


