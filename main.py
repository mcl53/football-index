import datetime
import os
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from random import randint
import pickle
from secrets import nn_default, nn_optimal, timezone
from utils import return_dates
from file_system import read_media_scores, read_player_prices

import warnings
warnings.filterwarnings("ignore")

import pytz
tz = pytz.timezone(timezone)


def predict_stocks_to_buy(date, current_money):
	
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

	players_to_buy_columns = ["player", "buy_price", "predicted24h", "predicted48h", "actual24h", "actual48h", "sell_at", "percent_gain"]
	players_to_buy = pd.DataFrame(columns=players_to_buy_columns)
	
	for player_name in media_scores["urlname"]:
			data = read_player_prices(player_name)
			start_price = data.loc[data["timestamp"] == timestamp]["close"].iloc[0]
			end_price = data.loc[data["timestamp"] == (timestamp + 86400)]["close"].iloc[0]
			media_score = media_scores.loc[media_scores["urlname"] == player_name]["score"].iloc[0]
			
			test_data = pd.DataFrame([[start_price, end_price, media_score]], columns=["start_price", "end_price", "media_score"])
			predicted_data = model.predict(test_data)[0]
			
			if predicted_data[0] > end_price or predicted_data[1] > end_price:
				buy_price = end_price
				try:
					actual24h = data.loc[data["timestamp"] == (timestamp + (86400 * 2))]["close"].iloc[0]
					actual48h = data.loc[data["timestamp"] == (timestamp + (86400 * 3))]["close"].iloc[0]
				except IndexError as e:
					print(timestamp, player_name)
					raise(e)
				if predicted_data[0] >= predicted_data[1]:
					sell_at = "actual24h"
					percent_gain = ((predicted_data[0] - buy_price) / buy_price) * 100
				else:
					sell_at = "actual48h"
					percent_gain = ((predicted_data[1] - buy_price) / buy_price) * 100
				append = pd.DataFrame([[player_name, buy_price, predicted_data[0], predicted_data[1], actual24h, actual48h, sell_at, percent_gain]], columns=players_to_buy_columns)
				players_to_buy = players_to_buy.append(append)
				
	if len(players_to_buy) > 0:
		players_to_buy = players_to_buy.sort_values(by="percent_gain", ascending=False)
		spendable = current_money / 5
		max_players_to_buy = 20
		top_index = 0
		top_few = 0
		bottom_index = 0
		for i in range(len(players_to_buy)):
			if players_to_buy.iloc[i]["percent_gain"] > 0:
				bottom_index = i + 1
				top_few = sum(players_to_buy.iloc[top_index:bottom_index]["buy_price"])
				if top_few > spendable:
					break
				elif i == max_players_to_buy:
					bottom_index = max_players_to_buy + top_index + 1
			else:
				bottom_index = i
				top_few = sum(players_to_buy.iloc[top_index:bottom_index]["buy_price"])
				break
			if i >= max_players_to_buy:
				break
				
		if top_few == 0:
			return 0
		
		no_of_shares = spendable // top_few
		if no_of_shares == 0:
			no_of_shares = 1
		spent = top_few * no_of_shares
		# print()
		# print(f"Money spent: £{spent}")
		# predicted_sales = sum(players_to_buy.iloc[0:length]["predicted48h"]) * no_of_shares
		# print(f"Predicted profit: £{predicted_sales - spent}")
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
	# save_media_scores(dates_list)
	# for date in dates_list:
	# 	print(date)
	# 	test_scores = read_media_scores(date)
	# 	save_player_prices(test_scores["player_name"])
	# 	for i in range(len(test_scores)):
	# 		compile_data(test_scores["player_name"].iloc[i], date)
	
	# all_data = read_compiled_data()
	# average_money = 0
	#
	# no_of_iterations = 1
	#
	# for i in range(no_of_iterations):
	# 	money = train_network(all_data, nn_optimal["hidden_layer_sizes"], solver=nn_optimal["solver"], activation=nn_optimal["activation"], max_iter=nn_optimal["max_iter"], tol=nn_optimal["tol"])
	# 	if i == 0:
	# 		average_money = money
	# 	else:
	# 		average_money += money
	# average_money /= no_of_iterations
	# print()
	# print(f"Average money after training = £{'{0:.2f}'.format(average_money)}")
	# train_network(all_data, nn_optimal["hidden_layer_sizes"], solver=nn_optimal["solver"], activation=nn_optimal["activation"], max_iter=nn_optimal["max_iter"], tol=nn_optimal["tol"])
	# dates_list = dates_list[0:len(dates_list) // 2]
	money = 1000
	for date in dates_list[0:-3]:
		print(date)
		change = predict_stocks_to_buy(date, money)
		print(f"Actual profit: £{change}")
		print()
		money += change
	
	print(f"Total money after {no_months} month: £{money}")
