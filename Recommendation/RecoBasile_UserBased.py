import pandas as pd
import ast

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("synthetic_users_1000_real_tracks.csv")

# =========================
# UTILS
# =========================

# Parse des listes stockées en string comme FR;EN;DE en ensemble
def parse_list(value):
    try:
        return set(ast.literal_eval(value))
    except:
        return set()

# similarite Jaccard entre deux ensembles utilisés pour genres et langues
def jaccard(set1, set2):
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

# =========================
# USER INPUT
# =========================
print("=== Recommandation musicale user-based ==")

# saisie des préférences utilisateur
age = int(input("Entrez votre âge : "))

print("\nGenres disponibles : Rap, Pop, Rock, Electro, Jazz, Classique, Reggae, RnB, Indie")
genres_input = input("Entrez vos genres favoris (séparés par ;) : ")
user_genres = set(genres_input.split(";"))

print("\nLangues disponibles : FR, EN, DE, ES")
languages_input = input("Entrez vos langues favorites (séparées par ; FR;DE;etc...) : ")
user_languages = set(languages_input.split(";"))

# =========================
# SIMILARITY COMPUTATION
# =========================

# pré-calcul de la différence d'âge max pour normalisation
max_age_diff = df["user_age"].max() - df["user_age"].min()

best_score = -1
best_user = None

for _, row in df.iterrows():
    # Similarité d'âge (normalisée entre 0 et 1)
    age_sim = 1 - abs(age - row["user_age"]) / max_age_diff

    row_genres = set(row["user_favorite_genre"].split(";"))
    # Similarité de genres (Jaccard)
    genre_sim = jaccard(user_genres, row_genres)

    row_languages = parse_list(row["user_favorite_languages"])
    # Similarité de langues (Jaccard)
    lang_sim = jaccard(user_languages, row_languages)

    # Score finale pondéré
    score = 0.4 * age_sim + 0.3 * genre_sim + 0.3 * lang_sim

    # selection du meilleur utilisateur
    if score > best_score:
        best_score = score
        best_user = row

# =========================
# OUTPUT
# =========================
print("\nUtilisateur le plus similaire trouvé")
print(f"Score de similarité : {best_score:.2f}")
print(f"Âge : {best_user['user_age']}")
print(f"Genres : {best_user['user_favorite_genre']}")
print(f"Langues : {best_user['user_favorite_languages']}")

# Extraction des musiques écoutées par l'utilisateur similaire
tracks = parse_list(best_user["listened_tracks"])

print("\nMusiques recommandées :")
for t in tracks:
    print(f"- {t}")

import psutil, os; 

print(f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.Process(os.getpid()).memory_info().rss/1024**2:.2f} MB")

