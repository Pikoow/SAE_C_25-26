import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt

EXPECTED_COLUMNS = 19

df = pd.read_csv("../../CSV/Initial_CSV/raw_albums.csv", sep=",", on_bad_lines="warn")
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

# new_df["album_information"] = (
#     new_df["album_information"]
#     .fillna("")
#     .astype(str)
#     .str.replace("\"\"", "\"", regex=False)
# )
pattern_quotes = re.compile(r"(?<=\w)""|""(?=\w)", flags=re.IGNORECASE | re.VERBOSE)

def ligne_valide(row):
    ligne = str(row)
    # if (len(row.columns) != EXPECTED_COLUMNS) :
    #     return False
    if (isinstance(row['album_comments'], int) or (isinstance(row['album_listens'], int)) or (isinstance(row['album_id'], str))) :
        return False
    return True


print(df.loc[0],"\n\n\n")
print(df)

new_df["album_information"] = new_df["album_information"].str.replace(r"<\/?p[^>]*>", "", regex=True)

# new_df["album_information"] = new_df["album_information"].str.replace(r"'{2,}", "'", regex=True)
# new_df["album_information"] = new_df["album_information"].str.replace(r'"{2,}', '"', regex=True)


new_df.drop(df[df.apply(ligne_valide, axis=1)].index, inplace=True)

new_df.to_csv("../../CSV/Cleaned_CSV/raw_albums_cleaned.csv", sep=",", index=False, encoding="utf-8")

# Compter les occurrences de guillemet simple
print('cases avec "" :', df['album_information'].str.contains("\"\"", regex=False).sum())
print(repr(df['album_information'].iloc[10]))
# df.drop()

# print(df.loc[0],"\n\n\n")
# print(df)

#tags & genre ?