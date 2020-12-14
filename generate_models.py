from random import randint
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split
import pickle
from secrets import nn_default, nn_optimal
from mongo import read_training_data

import warnings

warnings.filterwarnings("ignore")


def train_price_predictor(hidden_layer_sizes=nn_default["hidden_layer_sizes"], activation=nn_default["activation"],
						solver=nn_default["solver"], learning_rate=nn_default["learning_rate"], max_iter=nn_default["max_iter"],
						tol=nn_default["tol"]):
	data = read_training_data()
	
	random_state = randint(1, len(data))
	
	X = data.drop(["24h", "48h"], axis=1)
	y = data.drop(["start_price", "end_price", "media_score"], axis=1)
	
	X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.2, random_state=random_state)
	
	network = MLPRegressor(hidden_layer_sizes=hidden_layer_sizes, activation=activation, solver=solver,
						   learning_rate=learning_rate, max_iter=max_iter, tol=tol)
	network.fit(X_train, y_train)
	
	y_pred = network.predict(X_test)
	
	with open("./price_prediction_model.p", "wb") as f:
		pickle.dump(network, f)


if __name__ == "__main__":
	train_price_predictor(nn_optimal["hidden_layer_sizes"])
