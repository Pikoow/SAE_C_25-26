import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import os

EXPECTED_COLUMNS = 19

current_dir = os.path.dirname(os.path.abspath(__file__))

input_file = os.path.join(current_dir, "..", "..", "CSV", "Initial_CSV", "raw_albums.csv")
output_file = os.path.join(current_dir, "..", "..", "CSV", "Cleaned_CSV", "raw_albums_cleaned.csv")

df = pd.read_csv(input_file, sep=",", on_bad_lines="warn")
new_df = pd.DataFrame(df)

pattern_clean = re.compile(
    r"<\s*/?\s*(p|br|div|span|b|i|u|em|strong|ul|a|li|font|table|tbody|tr|thead|td|font-face|center|iframe|col|img|h4|h3|h2|ol|sup|blockquote|hr|w|m|xml)\b[^>]*>|[\t\n\]+]|[\*]|",
    flags=re.IGNORECASE
)

new_df["album_information"] = (
    new_df["album_information"]
    .fillna("")
    .astype(str)
    .str.replace(pattern_clean, "", regex=True)
)

pattern_quotes = re.compile(r"(?<=\w)""|""(?=\w)", flags=re.IGNORECASE | re.VERBOSE)

def ligne_valide(row):
    ligne = str(row)
    # if (len(row.columns) != EXPECTED_COLUMNS) :
    #     return False
    if (isinstance(row['album_comments'], int) or (isinstance(row['album_listens'], int)) or (isinstance(row['album_id'], str))) :
        return False
    return True

new_df["album_information"] = new_df["album_information"].str.replace(r"<\/?p[^>]*>", "", regex=True)

new_df.drop(df[df.apply(ligne_valide, axis=1)].index, inplace=True)

new_df.to_csv(output_file, sep=",", index=False, encoding="utf-8")