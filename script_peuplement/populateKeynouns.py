import re
import psycopg2 
from psycopg2 import sql
from psycopg2.extras import Json
from nltk.stem import PorterStemmer
from dotenv import load_dotenv
import os

load_dotenv()

import en_core_web_sm
# import locale

# print("\n\n","ENCODING","\n\n\n", locale.getpreferredencoding(False))

nlp = en_core_web_sm.load()

stemmer = PorterStemmer()

DB_CONFIG = {
    "host": "localhost",
    "dbname": "postgres",
    "user": "postgres",
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": 5432
}

STOP_WORDS = {
    "The","An","A","In","On","At","This","That",
    "And","Or","With","Without","Upon","Of","For","From",
    "We","If","It","So","As","They"
}

INSTRUMENT_WORDS = {
    "guitar","piano","violin","flute","drum","drums"
}

# liste de nom (titre même éventuellement)
# liste d'instruments
# liste de genre

empty = 0

def get_album_info(album_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT album_information
        FROM sae.album
        WHERE album_id = %s;
    """, (album_id,))

    row = cur.fetchone()
    # print("row \n\n",row)
    cur.close()
    conn.close()

    if row:
        # print("sigma boy \n\n\n",row[0])
        return row[0]  # album_information
    else :
        return ""

def extract_names_groups(extracted_text) :
    if not extracted_text:
        print("c'est vide")
        global empty
        empty = empty +1
        return []
    bag_of_sentences = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][A-Za-z]+)*)\b', extracted_text)
    bag_of_names = []
    
    # print("\n\n",bag_of_sentences)
    # print("nlp start \n\n")
    
    for h in bag_of_sentences :
        word = nlp(h)
        
        # print([(w.text, w.pos_) for w in word])
        
        if any(token.pos_ == "PROPN" for token in word):
            if bag_of_names.__contains__(h) :
                print('already in')
                continue
            else :
                bag_of_names.append(h)
            
            # PROPN pour les noms
            # print("c'est cool")
            
    print(bag_of_names)
    return bag_of_names

def extract_other(extracted_text) :
    # print([(w.text, w.pos_) for w in doc])
    # bag_of_sentences = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][A-Za-z]+)*)\b', extracted_text)
    # bag_of_sentences = stemmer.stem(bag_of_sentences)
    # print("\n after\n",bag_of_sentences)
    
    
    if not extracted_text:
        return []
    bag_of_nouns = []
    bag_of_sentences = extracted_text
    print("\finfos : \n",bag_of_sentences)
    print("nlp start but nouns \n\n")
    doc = nlp(bag_of_sentences)
    # NOUN pour les noms commun
    for token in doc:
        if token.pos_ == "NOUN" :
            if bag_of_nouns.__contains__(token.text) :
                print('already in')
                continue
            else :
                bag_of_nouns.append(token.text)
            # print("\nc'est cool",token.text,token.pos_,"\n")
        else :
            continue
            # print(token.text,token.pos_)
    return bag_of_nouns

# doc = nlp("This is a sentence.")
# print([(w.text, w.pos_) for w in doc])
            

def vector_names(album_id):
    try:
        # Établir la connexion
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        info = get_album_info(album_id)
        bon = extract_names_groups(info)
        if not bon :
            print("rien n'a été trouvé.")
            return []

        query = f"""
        UPDATE sae.album
        SET album_keynames = %s
        WHERE album_id = %s;
        """
        
        print("\n ATTENTION (bag of names) \n",bon)
        
        cursor.execute(query,(Json(bon),album_id))
        conn.commit()
        # albums = cursor.fetchall()
        # print("\n\n\n Krekkov mentionned (supposed good albums) \n\n\n",albums)
                       
        cursor.close()
        conn.close()
        return "tkt ça a marché"

    except psycopg2.OperationalError as e:
        print(f"Erreur de connexion: {e}")
    except psycopg2.Error as e:
        print(f"Erreur SQL: {e}")
        
def vector_nouns(album_id):
    try:
        # Établir la connexion
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        info = get_album_info(album_id)
        bon = extract_other(info)
        if not bon :
            print("rien n'a été trouvé.")
            return []

        query = f"""
        UPDATE sae.album
        SET album_keynouns = %s
        WHERE album_id = %s;
        """
        
        print("\n ATTENTION (bag of nouns) \n",bon)
        # print("\n ATTENTION (bag of nouns version json) \n",Json(bon))
        
        cursor.execute(query,(Json(bon),album_id))
        conn.commit()
        
        cursor.close()
        conn.close()
        return "tkt ça a marché"

    except psycopg2.OperationalError as e:
        print(f"Erreur de connexion: {e}")
    except psycopg2.Error as e:
        print(f"Erreur SQL: {e}")


def get_album_ids():
    # print("ouais on est la")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("""
        SELECT album_id
        FROM sae.album
    """, )

    row = cur.fetchall()
    # print("row \n\n",row)
    cur.close()
    conn.close()

    if row:
        # print("sigma boy \n\n\n",row[0])
        return row  # album_ids
    elif row == [] :
        print("c'est vide")
        return []
    return "ça marche pas je crois"

def create_missing_column() :
    # Établir la connexion
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        query = """
        ALTER TABLE sae.album
        ADD COLUMN IF NOT EXISTS album_keynames VARCHAR(65000);
        """
        cursor.execute(query)
        
        query2 = """
        ALTER TABLE sae.album
        ADD COLUMN IF NOT EXISTS album_keynouns VARCHAR(65000);
        """
        cursor.execute(query2)
        
        conn.close()
        print("colomn added (or not)")
        return ""
    
def check_keys(id) :
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
        SELECT album_keynames,album_keynouns
        FROM sae.album
        WHERE album_id = %s
    """
    print("c'est l'id qu'on utilise : ",id,"de type : ",type(id))
    cur.execute(query,id)
    row = cur.fetchall()
    print("keys :  \n\n",row)
    cur.close()
    conn.close()

    if row:
        # print("sigma boy \n\n\n",row[0])
        return row  # album_ids
    return "ça marche pas je crois"

def main() : 
    albums_ids = get_album_ids()
    # print("\n\n album ids here \n\n",albums_ids)
    nb_id = len(albums_ids)
    print("number of album ids : ",nb_id)
    create_missing_column()
    test_subjects = []
    for t in albums_ids :
        # print(t)
        test_subjects.append(t)
    for id in test_subjects :
        vector_names(id)
        vector_nouns(id)
        print(id[0], " done")
        check_keys(id)
    global empty
    print("c'est fini ! \n",empty," albums n'ont pas d'information\n",)
    
if __name__ == "__main__":
    main()
    
# après a partir d'un id d'album
# on établit un score de similarité
# qui prends les noms et les nouns
# les plus élevé en premier
# on en récupère une dizaine
# on affiche le score
# si c'est 0, je pense que j'affiche rien