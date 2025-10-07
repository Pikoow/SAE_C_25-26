import pandas as pd

#=== CHARGEMENT DES DONNÉES DU FICHIER CSV ===#
data_frame = pd.read_csv("../../CSV/Inital_CSV/raw_tracks.csv")

def cleaner(data_frame):

    #=== TRAITEMENT DES VALEURS MANQUANTES ===#
    data_frame_cleaned = data_frame.replace(r'^\s*$', None, regex=True) 
    
    #=== SUPPRESSION DES BALISES HTML ===#
    data_frame_cleaned = data_frame_cleaned.replace(r'<[^<>]*>', '', regex=True)
    
    #=== GÉNÉRATION DU FICHIER CSV NETTOYÉ
    data_frame_cleaned.to_csv("../../CSV/Cleaned_CSV/raw_tracks_cleaned.csv", index=False, na_rep="NULL") #

cleaner(data_frame)