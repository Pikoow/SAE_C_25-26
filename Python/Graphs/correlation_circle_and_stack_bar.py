import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


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


def correlation_circle(data_frame):
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
correlation_circle(data_frame)
bar_chart(data_frame)