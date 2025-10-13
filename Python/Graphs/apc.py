import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import numpy as np

fichier_csv = "raw_echonest.csv"
df = pd.read_csv(fichier_csv, skiprows=2)

df = df.dropna(axis=1, how='all')
if "track_id" in df.columns:
    df = df.dropna(subset=["track_id"])

colonnes_interessantes = ["danceability", "energy", "tempo"]
df = df[[c for c in colonnes_interessantes if c in df.columns]].dropna()

for c in colonnes_interessantes:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df.dropna()

X = df[["danceability", "energy", "tempo"]].values
k = 10
kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(X)

resume_clusters = df.groupby("cluster").agg({
    "tempo": "mean",
    "danceability": "mean",
    "energy": "mean"
}).reset_index()

plt.figure(figsize=(10, 6))

norm = plt.Normalize(resume_clusters["energy"].min(), resume_clusters["energy"].max())
cmap = plt.cm.viridis

scatter = plt.scatter(
    resume_clusters["tempo"],
    resume_clusters["danceability"],
    c=resume_clusters["energy"],
    cmap=cmap,
    s=400,
    edgecolors="black",
    alpha=0.85
)

cbar = plt.colorbar(scatter, label="Energy", orientation="vertical", pad=0.02)
cbar.ax.tick_params(labelsize=10)

plt.title("Corrélation Energy,Danceability and Tempo", fontsize=14)
plt.xlabel("Tempo (BPM)", fontsize=12)
plt.ylabel("Danceability", fontsize=12)
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()
