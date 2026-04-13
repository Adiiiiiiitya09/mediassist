import pandas as pd
import numpy as np
import pickle
import json
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

df = pd.read_csv('dataset.csv')
sev = pd.read_csv('Symptom-severity.csv')

# Clean whitespace
for col in df.columns:
    df[col] = df[col].astype(str).str.strip().str.replace(' ', '_')

df = df.replace('nan', np.nan)

# Build deduplicated 131-symptom master list
raw_syms = sev['Symptom'].str.strip().tolist()
seen = set()
symptom_list = []

for s in raw_syms:
    if s not in seen and s != 'prognosis':
        seen.add(s)
        symptom_list.append(s)

# Build binary feature matrix (4920 rows x 131 cols)
X = pd.DataFrame(0, index=df.index, columns=symptom_list)

for col in df.columns[1:]:
    for idx, val in df[col].items():
        if pd.notna(val) and str(val) != 'nan' and val in symptom_list:
            X.loc[idx, val] = 1

y = df['Disease'].str.strip()
le = LabelEncoder()
y_enc = le.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
)

model = ExtraTreesClassifier(n_estimators=100, max_depth=15, random_state=42)
model.fit(X_train, y_train)

print(f'Accuracy: {accuracy_score(y_test, model.predict(X_test)):.4f}')

with open('extratrees_model.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

with open('symptom_list.json', 'w') as f:
    json.dump(symptom_list, f)

print('Saved: extratrees_model.pkl  label_encoder.pkl  symptom_list.json')
