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
ADMIN_EMAIL=email du compte admin  
ADMIN_PASSWORD=mot de passe du compte admin  
ADMIN_FIRST=prénom du compte admin  
ADMIN_LAST=nom de famille du compte admin  

## 3. Création de la base

Lancez le script `setup_db.py`.

Téléchargez les fichiers csv depuis ce Google Drive : `https://drive.google.com/drive/folders/1DtQ8-IXiZsam_DDopiSt9yS9ogjt6_sH?usp=sharing`.  
Et déposez les dans `/script_peuplement`.  

Vous devez bien avoir :  
- raw_albums_cleaned.csv
- raw_artists_cleaned.csv
- tracks_clean.csv
- genre_clean.csv
- raw_echonest.csv
- raw_tracks.csv
- questionnaire.csv
- clean_echonest.csv  
- aatracks_clean_test.csv  

## 4. Création de l'admin
Lancer le script `seed_admin.py`. 

## 5. Lancement de l'API

Lancez le script : `python API/scripts/main.py`.  
Cela peut prendre un temps plus au moins important.

## 6. Lancement du server node

Dans une console séparée lancez le script du server `node API/web/node-auth/server.js`.  

Vous pouvez accéder au site à l'adresse `localhost:3000/accueil.html`.