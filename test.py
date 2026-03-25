import pandas as pd

df = pd.read_csv("Subject Details.csv")

# Clean column names
df.columns = df.columns.str.strip()

age_group = {
    "young": [],
    "middle": [],
    "older": []
}

for _, row in df.iterrows():
    
    subject = row["Subject"]          # already S01, S02...
    age = row["Age (Years)"]

    # Convert S01 → 1, S02 → 2
    subject_num = int(subject.replace("S", ""))

    if 19 <= age <= 35:
        age_group["young"].append(subject_num)

    elif 36 <= age <= 55:
        age_group["middle"].append(subject_num)

    elif age >= 56:
        age_group["older"].append(subject_num)

print(age_group)