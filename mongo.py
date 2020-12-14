import pymongo
import pandas as pd

client = pymongo.MongoClient("mongodb://127.0.0.1:27017")

db = client["football-index"]
media_scores_collection = db["media-scores"]
players_collection = db["players"]
training_collection = db["training-data"]


def read_player_prices(player):
	try:
		player_prices = players_collection.find_one({"player_name": player})["price_history"]
	except TypeError as e:
		print(player)
		raise e
	
	df = pd.json_normalize(player_prices)
	
	return df


def read_media_scores(date):
	media_scores = media_scores_collection.find_one({"date": date})["scores"]
	
	df = pd.json_normalize(media_scores)
	
	return df


def read_training_data():
	training_data = list(training_collection.find({}, {"_id": 0, "data": 1}))
	new_list = []
	for i in training_data:
		for obj in i["data"]:
			new_list.append(obj)
	
	df = pd.json_normalize(new_list)
	
	return df
	

if __name__ == "__main__":
	test = read_player_prices("aaron-connolly")
	print(test)
	test2 = read_media_scores("20201206")
	print(test2)
	test3 = read_training_data()
	print(test3)
