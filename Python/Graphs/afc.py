import pandas as pd
import matplotlib.pyplot as plt
import prince
import os

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