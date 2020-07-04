import datetime
import os
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from random import randint
import pickle
from secrets import nn_default, nn_optimal, timezone
from file_system import read_player_prices, save_media_scores, read_media_scores, update_players
from utils import return_dates

import warnings
warnings.filterwarnings("ignore")

import pytz
tz = pytz.timezone(timezone)


def train_network(data, hidden_layer_sizes, activation=nn_default["activation"], solver=nn_default["solver"], learning_rate=nn_default["learning_rate"], max_iter=nn_default["max_iter"], tol=nn_default["tol"], v=False):
	random_state = randint(1, len(data))
	
	X_24 = data.drop(["24h", "48h"], axis=1)
	y_24 = data.drop(["start_price", "end_price", "48h", "media_score"], axis=1)
	X_24_train, X_24_test, y_24_train, y_24_test = train_test_split(X_24, y_24, train_size=0.2, random_state=random_state)
	network_24 = MLPRegressor(hidden_layer_sizes=hidden_layer_sizes, activation=activation, solver=solver, learning_rate=learning_rate, max_iter=max_iter, tol=tol)
	network_24.fit(X_24_train, y_24_train)
	y_24_pred = network_24.predict(X_24_test)
	y_24_train_pred = network_24.predict(X_24_train)
	
	X_48 = data.drop(["24h", "48h"], axis=1)
	y_48 = data.drop(["start_price", "end_price", "24h", "media_score"], axis=1)
	X_48_train, X_48_test, y_48_train, y_48_test = train_test_split(X_48, y_48, train_size=0.2, random_state=random_state)
	X_48_train.insert(2, "24h", y_24_train_pred, True)
	X_48_test.insert(2, "24h", y_24_pred, True)
	network_48 = MLPRegressor(hidden_layer_sizes=hidden_layer_sizes, activation=activation, solver=solver, learning_rate=learning_rate, max_iter=max_iter, tol=tol)
	network_48.fit(X_48_train, y_48_train)
	y_48_pred = network_48.predict(X_48_test)
	
	if v:
		total = 0
		money = 100
	
	for i in range(len(y_24_pred)):
		if v:
			print(f"24h pred {y_24_pred[i]}, 48h pred {y_48_pred[i]}, actual 24h {y_24_test['24h'].iloc[i]}, actual 48h {y_48_test['48h'].iloc[i]}")
			print(f"Buy price: {X_24_test['end_price'].iloc[i]}")
			if y_24_pred[i] > X_24_test["end_price"].iloc[i] or y_48_pred[i] > X_24_test["end_price"].iloc[i]:
				if y_48_pred[i] > y_24_pred[i]:
					sale_price = y_48_test["48h"].iloc[i]
				else:
					sale_price = y_24_test["24h"].iloc[i]
				money_made = sale_price - X_24_test["end_price"].iloc[i]
				money += money_made
				if money_made > 0:
					total += 1
			else:
				if X_24_test["end_price"].iloc[i] >= y_24_test["24h"].iloc[i] and X_24_test["end_price"].iloc[i] >= y_48_test["48h"].iloc[i]:
					total += 1
		
	if v:
		percentage = total / len(y_24_pred) * 100
		print()
		print(f"Percentage correct guesses 24 hours = {percentage}%")
		print(f"Money made = {money}")
	
	with open("./24h_predictor.p", "wb") as f1:
		pickle.dump(network_24, f1)
	
	with open("./48h_predictor.p", "wb") as f2:
		pickle.dump(network_48, f2)
	
	# return round(money, 2)


def predict_stocks_to_buy(date, current_money):
	
	year = int(date[0:4])
	month = int(date[4:6])
	day = int(date[6:])
	date_obj = datetime.datetime(year, month, day)
	global tz
	tz_aware = tz.localize(date_obj, is_dst=None)
	timestamp = datetime.datetime.timestamp(date_obj) + tz_aware.tzinfo._dst.seconds
	
	if not os.path.exists(f"media_scores/{date}"):
		save_media_scores([date])
	
	media_scores = read_media_scores(date)
	
	with open("24h_predictor.p", "rb") as f:
		model_24 = pickle.load(f)
		
	with open("48h_predictor.p", "rb") as f:
		model_48 = pickle.load(f)

	update_players(media_scores["player_name"])
	
	players_to_buy_columns = ["player", "buy_price", "predicted24h", "predicted48h", "actual24h", "actual48h", "sell_at", "percent_gain"]
	players_to_buy = pd.DataFrame(columns=players_to_buy_columns)
	
	for player_name in media_scores["player_name"]:
		if os.path.exists(f"player_prices/{player_name}.csv"):
			try:
				data = read_player_prices(player_name)
				start_price = data.loc[data["time"] == timestamp]["price"].iloc[0]
				end_price = data.loc[data["time"] == (timestamp + 86400)]["price"].iloc[0]
				media_score = media_scores.loc[media_scores["player_name"] == player_name]["score"].iloc[0]
			except ValueError:
				continue
			except IndexError as e:
				print(e)
				continue
			
			test_data_24 = pd.DataFrame([[start_price, end_price, media_score]], columns=["start_price", "end_price", "media_score"])
			predicted_data_24 = model_24.predict(test_data_24)
			predicted_data_24 = round(predicted_data_24[0], 2)
			test_data_48 = pd.DataFrame([[start_price, end_price, predicted_data_24, media_score]], columns=["start_price", "end_price", "24h", "media_score"])

			predicted_data_48 = model_48.predict(test_data_48)
			predicted_data_48 = round(predicted_data_48[0], 2)
			
			if predicted_data_24 > end_price or predicted_data_48 > end_price:
				buy_price = end_price
				actual24h = data.loc[data["time"] == (timestamp + (86400 * 2))]["price"].iloc[0]
				actual48h = data.loc[data["time"] == (timestamp + (86400 * 3))]["price"].iloc[0]
				if predicted_data_24 >= predicted_data_48:
					sell_at = "actual24h"
					percent_gain = ((predicted_data_24 - buy_price) / buy_price) * 100
				else:
					sell_at = "actual48h"
					percent_gain = ((predicted_data_48 - buy_price) / buy_price) * 100
				append = pd.DataFrame([[player_name, buy_price, predicted_data_24, predicted_data_48, actual24h, actual48h, sell_at, percent_gain]], columns=players_to_buy_columns)
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
	for date in dates_list:
		if int(date) > 20200701:
			break
		print(date)
		change = predict_stocks_to_buy(date, money)
		print(f"Actual profit: £{change}")
		print()
		money += change

	print(f"Total money after {no_months} month: £{money}")
