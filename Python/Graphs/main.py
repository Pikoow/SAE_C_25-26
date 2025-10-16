import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import prince
import seaborn as sns

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


# ===== LECTURE DES DONNÉES DEPUIS LES DIFFÉRENTS FICHIERS CSV ===== #

df_echonest = pd.read_csv("../../CSV/Initial_CSV/raw_echonest.csv", header=2, low_memory=False)
df_raw_tracks = pd.read_csv("../../CSV/Cleaned_CSV/raw_tracks_cleaned.csv", low_memory=False)
df_tracks_box_plot = pd.read_csv("../../CSV/Initial_CSV/tracks.csv", header=1, low_memory=False)
df_albums = pd.read_csv("../../CSV/Cleaned_CSV/raw_albums_cleaned.csv", sep=",", on_bad_lines="warn", low_memory=False)


# ===== BOX PLOT DURATION / GENRE ===== #

def box_plot_duration_genre(df):

    # Calcul des quartiles et de l'IQR pour filtrer les valeurs abberrantes
    Q1 = df['duration'].quantile(0.25)
    Q3 = df['duration'].quantile(0.75)
    IQR = Q3 - Q1

    # Filtrage des durées dans une plage raisonnable
    df_filtre = df[(df['duration'] >= Q1 - 1.5 * IQR) & (df['duration'] <= Q3 + 1.5 * IQR)]
    print(f"Lignes conservées : {len(df_filtre)} / {len(df)}")

    # Création du boxplot
    df_filtre.boxplot(column='duration', by='genre_top', figsize=(12,6))
    plt.title("Box plot duration / genders")
    plt.xlabel("genres")
    plt.ylabel("duration clipped")
    plt.grid(True)
    plt.show()


# ===== STACK BAR DURATION / NUMBER OF TRACKS ===== #

def bar_chart_duration_nbtracks(df):

    def convert_to_minutes(duration):
        if (pd.isna(duration)):
            return np.nan
        try:
            parts = str(duration).split(':')
            minutes = int(parts[0])
            seconds = int(parts[1]) if (len(parts) > 1) else 0
            return minutes + seconds / 60
        except:
            return np.nan

    # Application de la conversion sur la colonne 'track_duration'
    df['track_duration_min'] = df['track_duration'].apply(convert_to_minutes)

    # Suppression des valeurs manquantes
    df = df.dropna(subset = ['track_duration_min'])

    # Filtrage des morceaux trop longs (> 8 min)
    df_filtered = df[df['track_duration_min'] <= 8]

    # Calcul de la durée moyenne
    mean_duration = df_filtered['track_duration_min'].mean()

    # Création de l'histogramme
    plt.figure(figsize = (10, 5))
    plt.hist(df_filtered['track_duration_min'], bins = 15, color = 'purple', edgecolor = 'black')
    plt.axvline(x = mean_duration, color = 'blue', linestyle = '-', label = f'Average duration: {mean_duration:.1f} min')
    plt.title('Barchart of track durations (up to 8 minutes)')
    plt.xlabel('Track duration (minutes)')
    plt.ylabel('Number of tracks')
    plt.legend()
    plt.grid(True, linestyle = '--', alpha = 0.7)
    plt.tight_layout()
    plt.show()


# ===== PLOT AVERAGE NUMBER OF TRACKS PER ALBUM PER YEAR ===== #

def plot_avg_track_nb_per_years(df):

    # Extraction de l'année à partir de la date de sortie
    df["album_year"] = pd.to_datetime(df["album_date_released"]).dt.year

    # Suppression des lignes avec années ou nombres de pistes manquants
    df = df.dropna(subset=["album_year", "album_tracks"])

    # Calcul du nombre moyen de pistes par année
    tracks_by_year = df.groupby("album_year")["album_tracks"].mean()

    # Tracé de la courbe
    plt.figure(figsize=(13,5))
    plt.plot(tracks_by_year.index, tracks_by_year.values, marker="o")
    plt.title("Evolution of the average number of tracks in albums through the years")
    plt.xlabel("Years where an album got published")
    plt.ylabel("Average track number per albums")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.show()


# ===== BAR CHART TRACK TILTLES / LENGTH ===== #

def bar_chart_track_titles_length(df):
    title_lengths = df['track_title'].str.len()

    plt.figure(figsize=(12, 6))
    sns.histplot(data=title_lengths, bins=30, color='#2ecc71')
    plt.title('Distribution of Track Title Lengths', fontsize=14, pad=15)
    plt.xlabel('Title Length (characters)', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.axvline(x=title_lengths.mean(), color='red', linestyle='--', label=f'Mean: {title_lengths.mean():.1f}')
    plt.legend()
    plt.tight_layout()
    plt.show()


# ===== STACK BAR NUMBER OF TRACKS PER DECADES / GENRES ===== #

def stack_bar_number_of_tracks_per_decennies_genres():

    # Lecture des deux premières lignes pour générer des noms de colonnes corrects
    header_df = pd.read_csv("../../CSV/Initial_CSV/tracks.csv", nrows=2)
    columns = [f"{header_df.columns[i]}_{header_df.iloc[0, i]}" for i in range(len(header_df.columns))]

    # Lecture complète avec les nouveaux noms de colonnes
    df = pd.read_csv("../../CSV/Initial_CSV/tracks.csv", skiprows=2, names=columns, low_memory=False)

    date_col = "track.4_date_recorded"
    genre_col = "track.7_genre_top"

    # Conversion des dates et filtrage des valeurs manquantes
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, genre_col])

    # Extraction de l'année et de la décennie
    df["year"] = df[date_col].dt.year
    df = df[df["year"] > 1900]  
    df["decade"] = (df["year"] // 10) * 10

    # Comptage des morceaux par décennie et genre
    tracks_per_decade = df.groupby(["decade", genre_col]).size().unstack(fill_value=0)
    tracks_per_decade = tracks_per_decade.sort_index()

    # Conversion en pourcentage
    tracks_percent = tracks_per_decade.div(tracks_per_decade.sum(axis=1), axis=0) * 100

    # Tracé des deux graphes (absolu + pourcentage)
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    tracks_per_decade.plot(
        kind="bar",
        stacked=True,
        colormap="tab20",
        ax=axes[0]
    )
    axes[0].set_title("Distribution of the number of tracks by genre and decade")
    axes[0].set_ylabel("Number of tracks")
    axes[0].legend(title="Genre", bbox_to_anchor=(1.05, 1), loc="upper left")

    tracks_percent.plot(
        kind="bar",
        stacked=True,
        colormap="tab20",
        ax=axes[1],
        legend=False
    )
    axes[1].set_title("Percentage distribution of genders by decade")
    axes[1].set_ylabel("Percentage (%)")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


# ===== ANALYSE EN COMPOSANTES PRINCIPALES (ACP) ===== #

def pca_analysis(df):

    # Nettoyage des noms de colonnes
    df.columns = df.columns.str.strip()

    # Sélection des variables utilisées pour l'ACP
    features = ["acousticness", "danceability", "energy", "instrumentalness", "speechiness", "tempo"]

    # Suppression des lignes avec valeurs manquantes
    df = df.dropna(subset=features)

    # Conversion en numérique
    for col in features:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=features)

    # Standardisation des données
    X = StandardScaler().fit_transform(df[features])

    # Application de l'ACP
    pca = PCA()
    X_pca = pca.fit_transform(X)

    # Récupération de la variance expliquée par chaque composante
    explained_variance = pca.explained_variance_ratio_
    components = np.arange(1, len(explained_variance) + 1)

    # Visualisation de la variance expliquée
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

    # Affichage des valeurs numériques de la variance expliquée
    print("\nExplained variance per component:")
    for i, var in enumerate(explained_variance, start=1):
        print(f" - Component {i}: {var*100:.2f}%")

    # Cercle de corrélation ---
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

    # Tracés de plusieurs paires de composantes principales
    correlation_circle(pca, 0, 1, features)  
    correlation_circle(pca, 0, 2, features)  
    correlation_circle(pca, 1, 2, features) 

    # Clustering KMeans sur un sous-ensemble de variables ---
    X_cluster = df[["instrumentalness", "energy", "tempo"]].values
    k = 10
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(X_cluster)

    # Moyenne des variables par cluster
    cluster_summary = df.groupby("cluster").agg({
        "tempo": "mean",
        "instrumentalness": "mean",
        "energy": "mean"
    }).reset_index()

    # Visualisation des clusters
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


# ==== ANALYSE FACTORIELLE DES CORRESPONDANCES (AFC) ===== #

def afc_analysis(df):

    # Conversion d'une durée "MM:SS" en secondes
    def duration_to_seconds(duration_str):
        try:
            minutes, seconds = map(int, duration_str.split(":"))
            return minutes * 60 + seconds
        except:
            return None

    # Transformation de la durée
    df["duration_seconds"] = df["track_duration"].apply(duration_to_seconds)

    # Catégorisation de la durée en intervalles
    df["duration_category"] = pd.cut(
        df["duration_seconds"],
        bins=[0, 150, 210, 270, 600],
        labels=["Short (<2:30)", "Medium (2:30–3:30)", "Long (3:30–4:30)", "Very long (>4:30)"]
    )

    # Catégorisation de la popularité en 4 quartiles
    df["listens_category"] = pd.qcut(df["track_listens"], q=4,
        labels=["Few listens", "Moderate listens", "Popular", "Very popular"]
    )

    # Table de contingence durée × popularité
    cross_tab = pd.crosstab(df["duration_category"], df["listens_category"])

    # Application de l'AFC avec 2 composantes
    ca = prince.CA(
        n_components=2,
        n_iter=10,
        random_state=42
    )
    ca = ca.fit(cross_tab)

    # Récupération des coordonnées des lignes et colonnes
    plt.figure(figsize=(10, 8))

    row_coords = ca.row_coordinates(cross_tab)
    plt.scatter(row_coords[0], row_coords[1], color="red", s=100, alpha=0.7, label="Track duration")

    col_coords = ca.column_coordinates(cross_tab)
    plt.scatter(col_coords[0], col_coords[1], color="blue", s=100, alpha=0.7, label="Track listens")

    # Annotation des points sur le graphique
    for label, (x, y) in row_coords.iterrows():
        plt.annotate(label, (x, y), xytext=(5, 5), textcoords="offset points", fontsize=10, color="red", fontweight="bold")

    for label, (x, y) in col_coords.iterrows():
        plt.annotate(label, (x, y), xytext=(5, 5), textcoords="offset points", fontsize=10, color="blue", fontweight="bold")

    # Mise en forme du graphe
    plt.title("Track Duration vs Number of Listens", fontsize=14, fontweight="bold")
    plt.xlabel("Component 1")
    plt.ylabel("Component 2")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()


# ===== APPELS DES FONCTIONS ===== #

box_plot_duration_genre(df_tracks)
bar_chart_duration_nbtracks(df_raw_tracks)
plot_avg_track_nb_per_years(df_albums)
bar_chart_track_titles_length(df_raw_tracks)
stack_bar_number_of_tracks_per_decennies_genres()
pca_analysis(df_echonest)
afc_analysis(df_raw_tracks)
