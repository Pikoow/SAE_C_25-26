import random
import pandas as pd
import numpy as np
import csv

random.seed(42)
np.random.seed(42)

N_USERS = 1000

# =========================
# TRACK CATALOG WITH LANGUAGE
# =========================
tracks_by_genre = {
    "Rap": [
        ("Booba - DKR", "FR"),
        ("Nekfeu - On verra", "FR"),
        ("Orelsan - Basique", "FR"),
        ("Kendrick Lamar - HUMBLE.", "EN"),
        ("Travis Scott - SICKO MODE", "EN"),
        ("PNL - Au DD", "FR"),
        ("Damso - Macarena", "FR")
    ],
    "Pop": [
        ("Dua Lipa - Levitating", "EN"),
        ("Taylor Swift - Blank Space", "EN"),
        ("Adele - Hello", "EN"),
        ("The Weeknd - Blinding Lights", "EN"),
        ("Angèle - Balance ton quoi", "FR")
    ],
    "Rock": [
        ("Arctic Monkeys - Do I Wanna Know?", "EN"),
        ("Coldplay - Viva La Vida", "EN"),
        ("Radiohead - Creep", "EN"),
        ("Muse - Uprising", "EN"),
        ("Noir Désir - Le vent nous portera", "FR")
    ],
    "Electro": [
        ("Daft Punk - One More Time", "FR"),
        ("Justice - D.A.N.C.E.", "FR"),
        ("David Guetta - Titanium", "EN"),
        ("Calvin Harris - I'm Not Alone", "EN")
    ],
    "Jazz": [
        ("Miles Davis - So What", "EN"),
        ("John Coltrane - Naima", "EN")
    ],
    "Classique": [
        ("Beethoven - Symphonie n°5", "DE"),
        ("Mozart - Requiem", "DE"),
        ("Bach - Air sur la corde de sol", "DE")
    ],
    "Reggae": [
        ("Bob Marley - No Woman No Cry", "EN")
    ],
    "RnB": [
        ("Usher - Yeah!", "EN"),
        ("Beyoncé - Crazy In Love", "EN")
    ],
    "Indie": [
        ("Phoenix - Lisztomania", "FR"),
        ("Tame Impala - The Less I Know The Better", "EN")
    ]
}

all_genres = list(tracks_by_genre.keys())

# =========================
# OTHER POOLS
# =========================
ages = list(range(16, 61))
listening_durations = [30, 60, 120, 240, 360]
avg_durations = [0.75, 2.25, 4.0, 5.0, "Ne se prononce pas"]
statuses = ["Étudiant", "Actif", "Sans emploi", "Autre"]
genders = ["Homme", "Femme", "Non-binaire"]
jobs = ["Primaire", "Secondaire", "Tertiaire", "other", "pas de pref"]
hours = ["matin", "midi", "soir", "nuit"]
platforms = ["Spotify", "Deezer", "Apple Music", "Youtube", "Youtube Music"]
tags = ["Découvrir régulièrement", "Toujours les mêmes musiques", "Ne se prononce pas"]

def random_subset(pool, min_n=1, max_n=3):
    return random.sample(pool, random.randint(min_n, max_n))

# =========================
# DATA GENERATION
# =========================
users = []

for uid in range(1, N_USERS + 1):
    fav_genres = random_subset(all_genres, 1, 3)

    listened_tracks = []
    listened_languages = set()

    for g in fav_genres:
        tracks = random.sample(
            tracks_by_genre[g],
            random.randint(1, min(3, len(tracks_by_genre[g])))
        )
        for title, lang in tracks:
            listened_tracks.append(title)
            listened_languages.add(lang)

    users.append({
        "user_id": uid,
        "user_age": random.choice(ages),
        "user_listening_duration": random.choice(listening_durations),
        "user_average_duration": random.choice(avg_durations),
        "user_status": random.choice(statuses),
        "user_favorite_hour": random_subset(hours, 1, 4),
        "user_favorite_genre": ";".join(fav_genres),
        "user_favorite_languages": list(listened_languages),
        "user_favorite_platforms": random_subset(platforms, 1, 3),
        "user_gender": random.choice(genders),
        "user_job": random.choice(jobs),
        "user_tags": f"{random.choice(tags)}, {random.choice(['Oui','Non'])}",
        "listened_tracks": list(set(listened_tracks))
    })

df = pd.DataFrame(users)

# EXPORT CSV PROPRE
df.to_csv(
    "synthetic_users_1000_real_tracks.csv",
    index=False,
    sep=",",
    quoting=csv.QUOTE_ALL,
    encoding="utf-8"
)

print("Dataset cohérent généré avec langues corrélées")
