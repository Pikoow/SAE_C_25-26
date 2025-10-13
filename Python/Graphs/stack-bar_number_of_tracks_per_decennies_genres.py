import pandas as pd
import matplotlib.pyplot as plt

# --- Lecture du CSV avec fusion des deux en-têtes ---
header_df = pd.read_csv("tracks.csv", nrows=2)
columns = [f"{header_df.columns[i]}_{header_df.iloc[0, i]}" for i in range(len(header_df.columns))]

df = pd.read_csv("tracks.csv", skiprows=2, names=columns, low_memory=False)

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
