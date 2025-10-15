import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("new_albums.csv", sep=",", on_bad_lines="warn")

# on ajoute une colonne fictive "album year" pour récupérer
# uniquement l'année de date de sortie des albums
df["album_year"] = pd.to_datetime(df["album_date_released"]).dt.year

# Pour retirer toutes les années vide
df = df.dropna(subset=["album_year", "album_tracks"])

# Moyenne des tracks par années
tracks_by_year = df.groupby("album_year")["album_tracks"].mean()
# print(tracks_by_year)

# Graphique
plt.figure(figsize=(13,5))
plt.plot(tracks_by_year.index, tracks_by_year.values, marker="o")
plt.title("Évolution du nombre moyen de morceaux par album")
plt.xlabel("Année de sortie")
plt.ylabel("Nombre moyen de morceaux")
plt.grid(True, linestyle="--", alpha=0.6)
plt.show()