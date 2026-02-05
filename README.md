# Setup BASE

## 1. Installer Postgres sur sa machine

Allez sur `https://www.enterprisedb.com/downloads/postgres-postgresql-downloads`.  
Téléchargez la dernière version.  
/!\ Attention : Lors de l'installation mettez un mot de passe et retenez le bien.

## 2. Modification des fichiers

Créer un fichier `.env` à la racine et complétez le à l'aide de la template.
Copiez la template et remplacez les "votre ..." par vos informations.
Pas besoin de mettre de guillemets.

Template :  
POSTGRES_DBNAME=votre nom de db  
POSTGRES_USER=votre nom de user  
POSTGRES_PASSWORD=votre password  
POSTGRES_PORT=votre port  

## 3. Création de la base

Lancez le script `setup_db.py`.

/!\ Attention : Vous devez avoir dans le dossier `script_peuplement` :
- raw_albums_cleaned.csv
- raw_artists_cleaned.csv
- tracks_clean.csv
- genre_clean.csv
- raw_echonest.csv
- raw_tracks.csv
- questionnaire.csv
- clean_echonest.csv  
- aatracks_clean_test.csv  
(Utilisez le script `cleanFinale.py` et les csv des professeurs)

/!\ Nouveau ! Vous devez avoir le csv `aatracks_clean_test.csv` à l'aide du cleaner `cleantesttracks.py`.

## 4. Lancement de l'API

Lancez le script : `API/scripts/main.py`