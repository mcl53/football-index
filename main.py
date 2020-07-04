import fi_api_calls
import datetime
from dateutil import relativedelta
import os
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
from random import randint
import pickle
from secrets import nn_default, nn_optimal, timezone
import pytz
import file_system


import warnings
warnings.filterwarnings("ignore")

tz = pytz.timezone(timezone)


def return_dates(months_prior=1):
	date = datetime.datetime.now()
	one_month_ago = date + relativedelta.relativedelta(months=-months_prior)
	delta = date - one_month_ago
	dates = []
	
	for i in range(1, delta.days + 1):
		this_date = one_month_ago + datetime.timedelta(days=i)
		this_date_string = convert_date_to_str(this_date)
		dates.append(this_date_string)
	
	return dates


def convert_date_to_str(date):
	year = date.year
	month = "{:02d}".format(date.month)
	day = "{:02d}".format(date.day)
	date_string = f"{year}{month}{day}"
	return date_string
	

def save_media_scores(dates):
	for date in dates:
		exists = os.path.exists(f"media_scores/{date}.csv")
		if not exists:
			media_scores = fi_api_calls.get_media_scores(date)
			media_scores.to_csv(f"media_scores/{date}.csv", index=None)


def read_media_scores(date):
	media_scores = pd.read_csv(f"media_scores/{date}.csv")
	return media_scores


def update_players(players):
	all_player_prices = fi_api_calls.get_player_price_history(players)

	for player in all_player_prices:
		player_name, player_prices = next(iter(player.items()))

		save_player_prices(player_name, player_prices)


def save_player_prices(player_name, player_prices):
	exists = os.path.exists(f"player_prices/{player_name}.csv")
	if exists:
		old_player_prices = file_system.read_player_prices(player_name)
		current_date = datetime.datetime.now()
		current_date.replace(hour=0, minute=0, second=0, microsecond=0)
		current_epoch = datetime.datetime.timestamp(current_date)
		last_download_time = old_player_prices.iloc[len(old_player_prices) - 1]["time"]
		if current_epoch - last_download_time > 86400:
			new_prices_trimmed = player_prices.iloc[len(old_player_prices):]
			player_prices = player_prices.append(new_prices_trimmed)
	
	if len(player_prices) > 0:
		player_prices.to_csv(f"player_prices/{player_name}.csv", index=False)


def compile_data(player, start_date):
	update_players([player])
	
	year = int(start_date[0:4])
	month = int(start_date[4:6])
	day = int(start_date[6:])
	date = datetime.datetime(year, month, day)
	
	try:
		player_prices = fi_api_calls.read_player_prices(player)
	except FileNotFoundError:
		return
	
	dataframe_columns = ["date", "start_price", "end_price", "24h", "48h", "media_score"]
	
	price_change = pd.DataFrame(columns=dataframe_columns)
	
	time_zero = player_prices["time"].iloc[0]
	time_zero_date = datetime.datetime.fromtimestamp(time_zero)
	hours_off = time_zero_date.hour // 4
	time_zero_date = time_zero_date.replace(hour=0)
	
	while date != datetime.datetime.now().date():
		str_date = convert_date_to_str(date)
		try:
			media_scores = read_media_scores(str_date)
		except FileNotFoundError:
			break
		
		for i, name in enumerate(media_scores["player_name"]):
			if name == player:
				diff = date - time_zero_date
				lots_of_4_hours = int(diff.total_seconds() // 14400)
				lots_of_4_hours -= hours_off
				start_price = player_prices["price"].iloc[lots_of_4_hours]
				try:
					end_price = player_prices["price"].iloc[lots_of_4_hours + 6]
					one_day = player_prices["price"].iloc[lots_of_4_hours + 12]
					two_days = player_prices["price"].iloc[lots_of_4_hours + 18]
				except IndexError:
					break
				media_score = media_scores["score"].iloc[i]
				media_day = pd.DataFrame([[str_date, start_price, end_price, one_day, two_days, media_score]], columns=dataframe_columns)
				price_change = price_change.append(media_day, ignore_index=True)
				break
		date += datetime.timedelta(days=1)
	file_name = f"{player}.csv"
	price_change.to_csv(f"price_changes/{file_name}", index=False)
	
	
def read_compiled_data():
	all_player_data = pd.DataFrame(columns=["start_price", "end_price", "24h", "48h", "media_score"])
	
	for r, d, f in os.walk("price_changes"):
		for file in f:
			player_data = pd.read_csv(f"price_changes/{file}", index_col=None)
			player_data = player_data.drop("date", axis=1)
			if player_data.count(axis=1).iloc[0] != 5:
				print("Contains NaN")
				print(file)
			else:
				all_player_data = all_player_data.append(player_data, ignore_index=True)
	
	return all_player_data


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
				data = file_system.read_player_prices(player_name)
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
