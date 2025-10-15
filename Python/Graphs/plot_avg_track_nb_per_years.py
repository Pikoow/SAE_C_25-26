import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("new_albums.csv", sep=",", on_bad_lines="warn")

# We are creating a new column "album year" that claims
# the year of the albums release date
df["album_year"] = pd.to_datetime(df["album_date_released"]).dt.year

# To clean all the years without data (if there are)
df = df.dropna(subset=["album_year", "album_tracks"])

# The average tracks per album per year
tracks_by_year = df.groupby("album_year")["album_tracks"].mean()
# print(tracks_by_year)

# The graph
plt.figure(figsize=(13,5))
plt.plot(tracks_by_year.index, tracks_by_year.values, marker="o")
plt.title("Evolution of the average number of tracks in albums through the years")
plt.xlabel("Years where an album got published")
plt.ylabel("Average track number per albums")
plt.grid(True, linestyle="--", alpha=0.6)
plt.show()
