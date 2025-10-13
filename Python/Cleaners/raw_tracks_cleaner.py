import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

input_file = os.path.join(current_dir, "..", "..", "CSV", "Initial_CSV", "raw_tracks.csv")
output_file = os.path.join(current_dir, "..", "..", "CSV", "Cleaned_CSV", "raw_tracks_cleaned.csv")

# === CHARGEMENT DES DONNÉES DU FICHIER CSV === #
data_frame = pd.read_csv(input_file)

def cleaner(data_frame):
    # === TRAITEMENT DES VALEURS MANQUANTES === #
    data_frame_cleaned = data_frame.replace(r'^\s*$', None, regex=True) 
    
    # === SUPPRESSION DES BALISES HTML === #
    data_frame_cleaned = data_frame_cleaned.replace(r'<[^<>]*>', '', regex=True)
    
    # === GÉNÉRATION DU FICHIER CSV NETTOYÉ === #
    data_frame_cleaned.to_csv(output_file, index=False, na_rep="NULL")

cleaner(data_frame)  

"""
The Fate of Ophelia = j'aime bien
Opalite = j'aime pas
Honey = pas ouf
Actually Romantic = pas ouf
Wi$h Li$t = j'aime pas
Ruin The Friendship = j'aime pas
CANCELLED! = j'aime bien
Elizabeth Taylor = pas ouf
Wood = j'aime pas
Father Figure = j'aime pas
Eldest Daughter = pas ouf
The Life of a Showgirl = Jaime bien et j'aime pas 
"""