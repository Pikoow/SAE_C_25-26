import matplotlib.pyplot as plt
import pandas as pd


df = pd.read_csv("/home/etudiant/Documents/SAE/tracks.csv", nrows=100000, header=1)

Q1 = df['duration'].quantile(0.25)
Q3 = df['duration'].quantile(0.75)
IQR = Q3 - Q1

df_filtre = df[(df['duration'] >= Q1 - 1.5 * IQR) & (df['duration'] <= Q3 + 1.5 * IQR)]

print(f"Lignes conservées : {len(df_filtre)} / {len(df)}")

df_filtre.boxplot(column='duration', by='genre_top', figsize=(12,6))

plt.title("Box plot duration / genders")
plt.xlabel("genres")
plt.ylabel("duration clipped")
plt.grid(True)
plt.show()

