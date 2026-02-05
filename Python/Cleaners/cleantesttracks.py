import os
import re
import unicodedata
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.set_option('future.no_silent_downcasting', True)

def clean_tracks():
    CSV_INPUT = "./tracks.csv"
    CSV_OUTPUT = "aatracks_clean_test.csv"

    df_raw = pd.read_csv(CSV_INPUT, header=None)

    header1, header2, header3 = df_raw.iloc[0].fillna(""), df_raw.iloc[1].fillna(""), df_raw.iloc[2].fillna("")

    new_cols = []
    for a, b, c in zip(header1, header2, header3):
        combined = f"{a}_{b}_{c}".strip("_")
        combined = re.sub(r"_+", "_", combined).lower()
        new_cols.append(combined)

    df = df_raw.iloc[3:].reset_index(drop=True)
    df.columns = [re.sub(r"^_+|_+$", "", c.replace("unnamed", "").lower()) for c in new_cols]

    track_cols = [c for c in df.columns if c.startswith("") or c == "track_id"]
    df_track = df[track_cols].copy()

    def clean_value(v):
        if pd.isna(v):
            return None
        if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
            return ",".join(x.strip().strip("'").strip('"') for x in v[1:-1].split(","))
        return v.strip() if isinstance(v, str) else v

    df_track = df_track.applymap(clean_value)
    df_track = df_track[df_track["track_id"].notna()]
    df_track["track_id"] = df_track["track_id"].astype(int)
    df_track.to_csv(CSV_OUTPUT, index=False, encoding="utf-8")

def main():

    print("\n=== CLEAN TRACKS ===")
    clean_tracks()

    print("\n✅ Tous les CSV ont ete nettoyes avec succès !")


if __name__ == "__main__":
    main()