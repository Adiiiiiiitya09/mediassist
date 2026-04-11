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

# Build deduplicated 131-symptom master list (optimized)
raw_syms = sev['Symptom'].str.strip().tolist()
# Remove duplicates while preserving order
symptom_list = list(dict.fromkeys(
    s for s in raw_syms if s and s.lower() != 'prognosis'
))
logger.info(f'Built symptom list: {len(symptom_list)} unique symptoms')

# Build binary feature matrix (4920 rows x 131 cols)
X = pd.DataFrame(0, index=df.index, columns=symptom_list)

# Build binary feature matrix (4920 rows x 131 cols) - vectorized
X = pd.DataFrame(0, index=df.index, columns=symptom_list, dtype=np.uint8)

# Vectorized approach instead of nested loops
for col in df.columns[1:]:
    mask = df[col].notna() & (df[col] != 'nan')
    valid_symptoms = df.loc[mask, col]
    valid_symptoms = valid_symptoms[valid_symptoms.isin(symptom_list)]
    X.loc[valid_symptoms.index, valid_symptoms.values] = 1

logger.info(f'Feature matrix shape: {X.shape}')
le = LabelEncoder()
y_enc = le.fit_transform(y)

from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report

logger.info(f'Train set: {X_train.shape}, Test set: {X_test.shape}')
    X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
)

model = ExtraTreesClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print(f'Accuracy: {accuracy_score(y_test, model.predict(X_test)):.4f}')

with open('extratrees_model.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

with open('symptom_list.json', 'w') as f:
    json.dump(symptom_list, f)

print('Saved: extratrees_model.pkl  label_encoder.pkl  symptom_list.json')
