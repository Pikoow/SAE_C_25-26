import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

df = pd.read_csv("raw_echonest.csv", header=2, low_memory=False)
df.columns = df.columns.str.strip()

features = ["acousticness", "danceability", "energy", "instrumentalness", "speechiness", "tempo"]

df = df.dropna(subset=features)

for col in features:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=features)

X = StandardScaler().fit_transform(df[features])

pca = PCA()
X_pca = pca.fit_transform(X)

explained_variance = pca.explained_variance_ratio_
components = np.arange(1, len(explained_variance) + 1)

plt.figure(figsize=(8, 5))
plt.bar(components, explained_variance, alpha=0.7, color="royalblue", edgecolor="black")
plt.plot(components, explained_variance, marker="o", color="black", linewidth=1)

plt.title("Explained Variance by Principal Component (PCA)", fontsize=13)
plt.xlabel("Principal Component", fontsize=12)
plt.ylabel("Explained Variance Ratio", fontsize=12)
plt.xticks(components)
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()

print("\nExplained variance per component:")
for i, var in enumerate(explained_variance, start=1):
    print(f" - Component {i}: {var*100:.2f}%")

def correlation_circle(pca, axis_x, axis_y, features):
    pcs = pca.components_
    xs = pcs[axis_x, :]
    ys = pcs[axis_y, :]

    fig, ax = plt.subplots(figsize=(6, 6))

    circle = plt.Circle((0, 0), 1, color="gray", fill=False, linestyle="--")
    ax.add_artist(circle)

    for i, feature in enumerate(features):
        ax.arrow(0, 0, xs[i], ys[i],
                 head_width=0.03, head_length=0.03, fc="red", ec="red")
        ax.text(xs[i]*1.1, ys[i]*1.1, feature, color="black", ha="center", va="center")

    ax.axhline(0, color="gray", linestyle="--")
    ax.axvline(0, color="gray", linestyle="--")

    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-1.1, 1.1)
    ax.set_xlabel(f"PC{axis_x+1} ({pca.explained_variance_ratio_[axis_x]*100:.2f} %)")
    ax.set_ylabel(f"PC{axis_y+1} ({pca.explained_variance_ratio_[axis_y]*100:.2f} %)")
    ax.set_title(f"Correlation Circle: PC{axis_x+1} vs PC{axis_y+1}")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.show()

correlation_circle(pca, 0, 1, features)  
correlation_circle(pca, 0, 2, features)  
correlation_circle(pca, 1, 2, features) 

X_cluster = df[["instrumentalness", "energy", "tempo"]].values
k = 10

kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(X_cluster)

cluster_summary = df.groupby("cluster").agg({
    "tempo": "mean",
    "instrumentalness": "mean",
    "energy": "mean"
}).reset_index()

plt.figure(figsize=(10, 6))

norm = plt.Normalize(cluster_summary["energy"].min(), cluster_summary["energy"].max())
cmap = plt.cm.viridis

scatter = plt.scatter(
    cluster_summary["tempo"],
    cluster_summary["instrumentalness"],
    c=cluster_summary["energy"],
    cmap=cmap,
    s=400,
    edgecolors="black",
    alpha=0.85
)

cbar = plt.colorbar(scatter, label="Energy", orientation="vertical", pad=0.02)
cbar.ax.tick_params(labelsize=10)

plt.title("Relationship Between Energy, Instrumentalness, and Tempo", fontsize=14)
plt.xlabel("Tempo (BPM)", fontsize=12)
plt.ylabel("Instrumentalness", fontsize=12)
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()
