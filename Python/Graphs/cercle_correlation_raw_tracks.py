import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def cercle_de_correlation():

    #===== LECTURE DES DONNÉES DU FICHIER CSV =====#
    data_frame = pd.read_csv("../../CSV/Cleaned_CSV/raw_tracks_cleaned.csv")

    #===== SÉLECTION DES VARIABLES UTILES =====#
    columns = ["track_listens", "track_favorites", "track_interest"]
    for column in columns:
        data_frame[column] = pd.to_numeric(data_frame[column], errors = "coerce")
    X = data_frame[columns].dropna()

    #===== STANDARDISATION DES DONNÉES =====#
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    #===== APC =====#
    acp = PCA(n_components = 2)
    X_acp = acp.fit_transform(X_scaled) 

    #===== CERCLE DE CORRÉLATION =====#
    composantes_principales = acp.components_
    for i, (x, y) in enumerate(zip(composantes_principales[0], composantes_principales[1])):
        plt.arrow(0, 0, x, y, head_width = 0.03, head_length = 0.03, fc = 'purple', ec = 'purple')
        plt.text(x * 1.15, y * 1.15, columns[i], color = 'black', ha = 'center', va = 'center')
    plt.xlim(-1.1, 1.1)
    plt.ylim(-1.1, 1.1)
    circle = plt.Circle((0, 0), 1, color = 'red', fill = False)
    plt.gca().add_artist(circle)
    plt.gca().set_aspect('equal', 'box')
    plt.title("Cercle de corrélation (ACP)")
    plt.xlabel(f"Première Composante Principale ({round(acp.explained_variance_ratio_[0] * 100, 2)}%)")
    plt.ylabel(f"Deuxième Composante Principale ({round(acp.explained_variance_ratio_[1] * 100, 2)}%)")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

cercle_de_correlation()