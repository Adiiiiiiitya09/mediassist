import pandas as pd
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

df = pd.read_csv('dataset.csv')
sev = pd.read_csv('Symptom-severity.csv')

# Clean whitespace — Fix Bug 1: collapse double underscores produced by
# symptoms like " dischromic _patches" → "dischromic__patches" → "dischromic_patches"
for col in df.columns:
    df[col] = (df[col].astype(str).str.strip()
                       .str.replace(' ', '_')
                       .str.replace(r'_+', '_', regex=True))

df = df.replace('nan', np.nan)

# Build deduplicated 131-symptom master list
# Apply the same normalization to the severity file so names always match
raw_syms = (sev['Symptom'].str.strip()
                           .str.replace(' ', '_')
                           .str.replace(r'_+', '_', regex=True)
                           .tolist())
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

model = ExtraTreesClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 Score:  {f1:.4f}")