import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Read the CSV file
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_file = os.path.join(current_dir, "..", "..", "CSV", "Cleaned_CSV", "raw_tracks_cleaned.csv")
df = pd.read_csv(csv_file)

# Calculate lengths of track titles
title_lengths = df['track_title'].str.len()

# Create the plot
plt.figure(figsize=(12, 6))

# Create histogram
sns.histplot(data=title_lengths, bins=30, color='#2ecc71')

# Customize the plot
plt.title('Distribution of Track Title Lengths', fontsize=14, pad=15)
plt.xlabel('Title Length (characters)', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.grid(True, alpha=0.3)

# Add mean line
plt.axvline(x=title_lengths.mean(), color='red', linestyle='--', label=f'Mean: {title_lengths.mean():.1f}')
plt.legend()

# Adjust layout and display
plt.tight_layout()
plt.show()