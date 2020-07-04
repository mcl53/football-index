import requests
import os
import pandas as pd
import datetime
import threading
import time
import queue
import concurrent.futures
from data_processing import json_to_dataframe
from secrets import x_access_token, top_players_endpoint, top_players_extra_params, media_scores_endpoint, media_scores_extra_params, price_history_endpoint

current_api_calls = 0
first_call = 0


def send_request(url):
	global current_api_calls, first_call
	
	"""Check to see if max API calls have been reached first.
	If we have wait until at least 1 minute after to make another 100.
	Do this first because here we set API calls to 0 and then next get the start time for the next 100."""
	if current_api_calls == 100:
		current_api_calls = 0
		last_call = time.time()
		while last_call < first_call + 60:
			last_call = time.time()
	# Take the time of the first API call
	if current_api_calls == 0:
		first_call = time.time()
		
	current_api_calls += 1
	
	params = {
		"Accept": "application/json",
		"x-access-token": x_access_token
	}
	
	r = requests.get(url=url, params=params)

	return r


def get_top_players(no_players):
	# Max no of players that the API will return
	if no_players > 200:
		no_players = 200
	
	url = f"{top_players_endpoint}{no_players}{top_players_extra_params}"
	
	r = send_request(url)
	
	# Using r.json()["items"] as all json data is wrapped in an "items" key
	player_data = json_to_dataframe(r.json()["items"], ["name", "price"], ["player_name", "price"])
	
	return player_data


def get_media_scores(date_string=None):
	if date_string is None:
		date = datetime.datetime.now()
		year = date.year
		month = "{:02d}".format(date.month)
		day = "{:02d}".format(date.day)
		
		date_string = f"{year}{month}{day}"
	
	url = f"{media_scores_endpoint}{date_string}{media_scores_extra_params}"
	
	r = send_request(url)
	
	# Using r.json()["items"] as all json data is wrapped in an "items" key
	media_data = json_to_dataframe(r.json()["items"], ["name", "score"], ["player_name", "score"])
	
	return media_data


def get_player_price_history(player_names):
	threads = []
	url = price_history_endpoint
	all_urls = []
	
	for player_name in player_names:

		individual_names = player_name.split(" ")
		name_id = ""
		for i, name in enumerate(individual_names):
			name_id += name.lower()
			if i < len(individual_names) - 1:
				name_id += "-"
	
		full_url = url + name_id
		all_urls.append({player_name: full_url})
	
	thread_executor = concurrent.futures.ThreadPoolExecutor()
	for i in all_urls:
		key, val = next(iter(i.items()))
		t = thread_executor.submit(send_request, val)
		threads.append({key: t})
		
	for thread in threads:
		key, val = next(iter(thread.items()))
		while not val.done():
			continue
	
	process_executor = concurrent.futures.ProcessPoolExecutor()
	processes = []
	for thread in threads:
		key, val = next(iter(thread.items()))
		p = process_executor.submit(convert_player_json_to_data_frame, key, val.result().json())
		processes.append(p)
	
	for process in processes:
		while not process.done():
			continue
	
	return_vals = []
	for process in processes:
		result = process.result()
		if len(next(iter(result.values()))) > 0:
			return_vals.append(result)
	
	return return_vals
	
	
def convert_player_json_to_data_frame(player_name, data):
	player_price = pd.DataFrame(columns=["time", "price"])
	try:
		for i in data["days"]:
			if i["close"] != 0:
				time = i["timestamp"]
				price = i["close"]
				player_price = player_price.append({"time": time, "price": price}, ignore_index=True)
	except KeyError:
		# print(name_id)
		pass
	
	return {player_name: player_price}


if __name__ == "__main__":
	top_players = get_top_players(100)
	# print(get_player_price_history("Harry Kane"))
	threads = []
	thread_q = queue.Queue()
	for i, name in enumerate(top_players["player_name"]):
		t = threading.Thread(target=get_player_price_history, args=(name, i, thread_q,))
		threads.append(t)
	
	start_time_threads = time.time()
	for i, thread in enumerate(threads):
		print(f"thread {i} started")
		thread.start()
		
	for thread in threads:
		thread.join()
	end_time_threads = time.time()
	print(f"Threads completed in {end_time_threads - start_time_threads} seconds")
	
	futures = []
	start_time_processes = time.time()
	process_pool = concurrent.futures.ProcessPoolExecutor()
	for item in list(thread_q.queue):
		key, val = next(iter(item.items()))
		running_process = process_pool.submit(convert_player_json_to_data_frame, key, val)
		futures.append(running_process)
	
	for i, future in enumerate(futures):
		while not future.done():
			continue
	end_time_processes = time.time()
	print(f"Time for processes to process was {end_time_processes - start_time_processes} seconds")
