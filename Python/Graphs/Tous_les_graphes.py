################################### AFC ####################################################

import pandas as pd
import matplotlib.pyplot as plt
import prince
import os
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import seaborn as sns

################################################################
###               CHARGEMENT DES DONNÉES                     ###
################################################################

# Chargement du fichier nettoyé
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(current_dir, "..", "..", "CSV", "Cleaned_CSV", "raw_tracks_cleaned.csv")
data = pd.read_csv(csv_file)

###############################################################
###              CONVERSION & CATÉGORISATION                ###
###############################################################

# Conversion de la durée "mm:ss" en secondes
def duration_to_seconds(duration_str):
    try:
        minutes, seconds = map(int, duration_str.split(":"))
        return minutes * 60 + seconds
    except:
        return None

data["duration_seconds"] = data["track_duration"].apply(duration_to_seconds)

# Catégorisation de la durée (selon distribution typique des morceaux)
data["duration_category"] = pd.cut(
    data["duration_seconds"],
    bins=[0, 150, 210, 270, 600],
    labels=["Short (<2:30)", "Medium (2:30–3:30)", "Long (3:30–4:30)", "Very long (>4:30)"]
)

# Catégorisation du nombre d’écoutes
data["listens_category"] = pd.qcut(data["track_listens"], q=4,
    labels=["Few listens", "Moderate listens", "Popular", "Very popular"]
)

###############################################################
###                 TABLEAU DE CONTINGENCE                  ###
###############################################################

cross_tab = pd.crosstab(data["duration_category"], data["listens_category"])

###############################################################
###                  ANALYSE FACTORIELLE                   ###
###############################################################

ca = prince.CA(
    n_components=2,
    n_iter=10,
    random_state=42
)
ca = ca.fit(cross_tab)

###############################################################
###                        GRAPHIQUE                        ###
###############################################################

plt.figure(figsize=(10, 8))

# Coordonnées des lignes (durées)
row_coords = ca.row_coordinates(cross_tab)
plt.scatter(row_coords[0], row_coords[1], color="red", s=100, alpha=0.7, label="Track duration")

# Coordonnées des colonnes (écoutes)
col_coords = ca.column_coordinates(cross_tab)
plt.scatter(col_coords[0], col_coords[1], color="blue", s=100, alpha=0.7, label="Track listens")

# Annotation des points
for label, (x, y) in row_coords.iterrows():
    plt.annotate(label, (x, y), xytext=(5, 5), textcoords="offset points", fontsize=10, color="red", fontweight="bold")

for label, (x, y) in col_coords.iterrows():
    plt.annotate(label, (x, y), xytext=(5, 5), textcoords="offset points", fontsize=10, color="blue", fontweight="bold")

plt.title("Track Duration vs Number of Listens", fontsize=14, fontweight="bold")
plt.xlabel("Component 1")
plt.ylabel("Component 2")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
#############################################  ACP   #########################################

df = pd.read_csv("../../CSV/Initial_CSV/raw_echonest.csv", header=2, low_memory=False)
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

#print("\nExplained variance per component:")
#for i, var in enumerate(explained_variance, start=1):
    #print(f" - Component {i}: {var*100:.2f}%")

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

########################################## ACP 2 (BARCHART) ###########################################

#===== LECTURE DES DONNÉES DU FICHIER CSV =====#
data_frame = pd.read_csv('../../CSV/Cleaned_CSV/raw_tracks_cleaned.csv')


#===== FONCTION POUR CONVERTIR LA COLONNE 'TRACK_DURATION' EN MINUTES =====#
def convert_to_minutes(time_str):
    if pd.isna(time_str):
        return np.nan
    try:
        parts = str(time_str).split(':')
        minutes = int(parts[0])
        seconds = int(parts[1]) if len(parts) > 1 else 0
        return minutes + seconds / 60
    except:
        return np.nan

    #===== SÉLECTION DES VARIABLES UTILES =====#
    columns = ['track_listens', 'track_favorites', 'track_interest']
    for column in columns:
        data_frame[column] = pd.to_numeric(data_frame[column], errors = 'coerce')
    X = data_frame[columns].dropna()

    #===== STANDARDISATION DES DONNÉES =====#
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    #===== APC =====#
    acp = PCA(n_components = 2)
    X_acp = acp.fit_transform(X_scaled) 

    #===== CERCLE DE CORRÉLATION =====#
    composantes_principales = acp.components_
    plt.figure(figsize = (10, 10))
    for i, (x, y) in enumerate(zip(composantes_principales[0], composantes_principales[1])):
        plt.arrow(0, 0, x, y, head_width = 0.03, head_length = 0.03, fc = 'purple', ec = 'purple')
        plt.text(x * 1.15, y * 1.15, columns[i], color = 'black', ha = 'center', va = 'center')
    plt.xlim(-1.1, 1.1)
    plt.ylim(-1.1, 1.1)
    circle = plt.Circle((0, 0), 1, color = 'blue', fill = False)
    plt.gca().add_artist(circle)
    plt.gca().set_aspect('equal', 'box')
    plt.title('Correlation circle')
    plt.xlabel(f'Fisrt component ({round(acp.explained_variance_ratio_[0] * 100, 2)}%)')
    plt.ylabel(f'Second component ({round(acp.explained_variance_ratio_[1] * 100, 2)}%)')
    plt.grid(True, linestyle = '--', alpha = 0.7)
    plt.tight_layout()
    plt.show()

def bar_chart(data_frame):
    #===== CONVERTION DE LA COLONNE EN MINUTES =====#
    data_frame['track_duration_min'] = data_frame['track_duration'].apply(convert_to_minutes)
    data_frame = data_frame.dropna(subset = ['track_duration_min'])

    #===== FILTRE POUR AFFICHER SEULEMENT LES SONS DE 10 MINUTES MAXIMUM =====#
    data_frame_filtered = data_frame[data_frame['track_duration_min'] <= 8]

    #===== CALCUL DE LA DURÉE MOYENNE =====#
    mean_duration = data_frame_filtered['track_duration_min'].mean()

    #===== HISTOGRAMME DES DURÉES =====#
    plt.figure(figsize = (10, 5))
    plt.hist(data_frame_filtered['track_duration_min'], bins = 15, color = 'purple', edgecolor = 'black')
    plt.axvline(x = mean_duration, color = 'blue', linestyle = '-', label = f'Average duration: {mean_duration:.1f} min')
    plt.title('Barchart of track durations (up to 8 minutes)')
    plt.xlabel('Track duration (minutes)')
    plt.ylabel('Number of tracks')
    plt.legend()
    plt.grid(True, linestyle = '--', alpha = 0.7)
    plt.tight_layout()
    plt.show()


#===== APPEL DES FONCTIONS =====#
bar_chart(data_frame)

################################################### BarChat ##################################


# Read the CSV file
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(current_dir, "..", "..", "CSV", "Cleaned_CSV", "raw_tracks_cleaned.csv")
df = pd.read_csv(csv_file)

# Calculate lengths of track titles
title_lengths = df['track_title'].str.len()

# Create the plot
plt.figure(figsize=(12, 6))

# Create histogram
sns.histplot(data=title_lengths, bins=30, color='#2ecc71')

# Customize the plot
plt.title('Distribution of Track Title Lengths', fontsize=14, pad=15)
plt.xlabel('Title Length (characters)', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.grid(True, alpha=0.3)

# Add mean line
plt.axvline(x=title_lengths.mean(), color='red', linestyle='--', label=f'Mean: {title_lengths.mean():.1f}')
plt.legend()

# Adjust layout and display
plt.tight_layout()
plt.show()

########################################### BoxPlot ###########################################

df = pd.read_csv("../../CSV/Initial_CSV/tracks.csv", nrows=100000, header=1,low_memory=False)

Q1 = df['duration'].quantile(0.25)
Q3 = df['duration'].quantile(0.75)
IQR = Q3 - Q1

df_filtre = df[(df['duration'] >= Q1 - 1.5 * IQR) & (df['duration'] <= Q3 + 1.5 * IQR)]

#print(f"Lignes conservées : {len(df_filtre)} / {len(df)}")

df_filtre.boxplot(column='duration', by='genre_top', figsize=(12,6))

plt.title("Box plot duration / genders")
plt.xlabel("genres")
plt.ylabel("duration clipped")
plt.grid(True)
plt.show()

########################################### Stacked bar ###########################################

# --- Lecture du CSV avec fusion des deux en-têtes ---
header_df = pd.read_csv("../../CSV/Initial_CSV/tracks.csv", nrows=2)
columns = [f"{header_df.columns[i]}_{header_df.iloc[0, i]}" for i in range(len(header_df.columns))]

df = pd.read_csv("../../CSV/Initial_CSV/tracks.csv", skiprows=2, names=columns, low_memory=False)

# --- Sélection des colonnes utiles ---
date_col = "track.4_date_recorded"
genre_col = "track.7_genre_top"

# --- Conversion de la date ---
df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
df = df.dropna(subset=[date_col, genre_col])

# --- Extraction de l'année et de la décennie ---
df["year"] = df[date_col].dt.year
df = df[df["year"] > 1900]  # ignore les années aberrantes
df["decade"] = (df["year"] // 10) * 10

# --- Groupement par décennie et genre ---
tracks_per_decade = df.groupby(["decade", genre_col]).size().unstack(fill_value=0)
tracks_per_decade = tracks_per_decade.sort_index()

# --- Version normalisée en pourcentage ---
tracks_percent = tracks_per_decade.div(tracks_per_decade.sum(axis=1), axis=0) * 100

# --- Création de la figure avec 2 sous-graphiques ---
fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

# --- Graphique 1 : Brut ---
tracks_per_decade.plot(
    kind="bar",
    stacked=True,
    colormap="tab20",
    ax=axes[0]
)
axes[0].set_title("Distribution of the number of tracks by genre and decade")
axes[0].set_ylabel("Number of tracks")
axes[0].legend(title="Genre", bbox_to_anchor=(1.05, 1), loc="upper left")

# --- Graphique 2 : Normalisé ---
tracks_percent.plot(
    kind="bar",
    stacked=True,
    colormap="tab20",
    ax=axes[1],
    legend=False
)
axes[1].set_title("Percentage distribution of genders by decade")
axes[1].set_ylabel("Percentage (%)")

# --- Améliorations visuelles ---
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

########################################### Line Graph ##################################################

df = pd.read_csv("../../CSV/Cleaned_CSV/new_albums.csv", sep=",", on_bad_lines="warn")

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