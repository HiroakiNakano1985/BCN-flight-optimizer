import pandas as pd

files = [
    "data/bcn_flight_dataset_till_PRG.csv",
    "data/bcn_flight_dataset_till_IST.csv",
    "data/bcn_flight_dataset_remaining.csv",
]

dfs = []

for i, f in enumerate(files):
    if i == 0:
        df = pd.read_csv(f)          # with header
    else:
        df = pd.read_csv(f, header=0)  # without header
    dfs.append(df)

merged = pd.concat(dfs, ignore_index=True)
merged.to_csv("data/bcn_flight_dataset_full.csv", index=False)

print("Saved merged dataset to bcn_flight_dataset_full.csv")