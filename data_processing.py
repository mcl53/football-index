import pandas as pd
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

tp = ThreadPoolExecutor()
threads = []


def json_to_dataframe(json, json_identifiers, columns):
	"""Takes json data and the key values for data within the json and returns a dataframe containing the data.
	Both json_identifiers and columns must be passed a list and the order of these must correspond with each other.
	i.e. json_identifiers = ["name", "price"], columns = ["player_name", "stock_price"]"""
	
	df = pd.DataFrame(columns=columns, index=None)
	for i in json:
		df = df.append({columns[0]: i[json_identifiers[0]], columns[1]: i[json_identifiers[1]]}, ignore_index=True)
		
	return df


def threaded_api_call(func, returns_player_json=False):
	def wrapper(x):
		global tp, threads
		thread = tp.submit(func, x)
		# separate this out into a separate service