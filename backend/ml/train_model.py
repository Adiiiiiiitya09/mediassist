
import pandas as pd
import numpy as np
import pickle
import json
import logging
from pathlib import Path
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define data paths
DATA_DIR = Path('data')
MODEL_DIR = Path('models')
MODEL_DIR.mkdir(exist_ok=True)

try:
    df = pd.read_csv(DATA_DIR / 'dataset.csv')
    sev = pd.read_csv(DATA_DIR / 'Symptom-severity.csv')
except FileNotFoundError as e:
    logger.error(f"Dataset file not found: {e}")
    exit(1)

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
X = pd.DataFrame(0, index=df.index, columns=symptom_list, dtype=np.int8)

for col in df.columns[1:]:
    for idx, val in df[col].items():
        if pd.notna(val) and str(val) != 'nan' and val in symptom_list:
            X.loc[idx, val] = 1

y = df['Disease'].str.strip()
le = LabelEncoder()
y_enc = le.fit_transform(y)

logger.info(f"Dataset shape: {X.shape}")
logger.info(f"Number of classes: {len(np.unique(y_enc))}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
)

# Train model with improved parameters
model = ExtraTreesClassifier(
    n_estimators=150,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    n_jobs=-1,  # Use all available cores
    random_state=42
)
model.fit(X_train, y_train)

# Evaluate model
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

logger.info(f'Accuracy: {accuracy:.4f}')
logger.info(f'\nClassification Report:\n{classification_report(y_test, y_pred, target_names=le.classes_)}')

# Save model artifacts
try:
    with open(MODEL_DIR / 'extratrees_model.pkl', 'wb') as f:
        pickle.dump(model, f)
    
    with open(MODEL_DIR / 'label_encoder.pkl', 'wb') as f:
        pickle.dump(le, f)
    
    with open(MODEL_DIR / 'symptom_list.json', 'w') as f:
        json.dump(symptom_list, f, indent=2)
    
    logger.info(f'✓ Models saved to {MODEL_DIR}')
except Exception as e:
    logger.error(f"Error saving models: {e}")
