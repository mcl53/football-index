import matplotlib.pyplot as plt
from file_system import read_all_data
import pandas as pd
from decimal import Decimal, ROUND_UP
import numpy as np

all_data = read_all_data()

media_scores = all_data.loc["media_score"]
price_changes_24 = pd.DataFrame(columns=["price_change"])
for row in all_data.iterrows():
	price_change_before = Decimal(row[1]["start_price"] - row[1]["end_price"]).quantize(Decimal(".01"), rounding=ROUND_UP)
	price_change_after = Decimal(row[1]["48h"] - row[1]["end_price"]).quantize(Decimal(".01"), rounding=ROUND_UP)
	price_change = price_change_after - price_change_before
	row_change = pd.DataFrame([[price_change]], columns=["price_change"])
	price_changes_24 = price_changes_24.append(row_change)

fig, ax = plt.subplots()

ax.scatter(price_changes_24, media_scores, alpha=0.7)
ax.set_xlabel("48 Hour Price Change")
ax.set_ylabel("Media Score")
ax.grid(True)

print(media_scores, media_scores.shape)
print(price_changes_24, price_changes_24.shape)
print(np.corrcoef(price_changes_24, media_scores))

plt.show()
