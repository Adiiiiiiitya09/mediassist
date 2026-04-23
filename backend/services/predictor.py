import pickle
import json
import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz
import os

# Get the backend directory path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ML_DIR = os.path.join(BASE_DIR, 'ml')

# Load model and data
with open(os.path.join(ML_DIR, 'extratrees_model.pkl'), 'rb') as f:
    MODEL = pickle.load(f)

with open(os.path.join(ML_DIR, 'label_encoder.pkl'), 'rb') as f:
    LE = pickle.load(f)

with open(os.path.join(ML_DIR, 'symptom_list.json')) as f:
    SYMPTOM_LIST = json.load(f)

desc_df = pd.read_csv(os.path.join(ML_DIR, 'symptom_Description.csv'))
prec_df = pd.read_csv(os.path.join(ML_DIR, 'symptom_precaution.csv'))


def map_to_vector(extracted_symptoms):
    vector = [0] * len(SYMPTOM_LIST)
    matched = 0

    for sym in extracted_symptoms:
        norm = sym.lower().strip().replace(' ', '_')

        # Fix Bug 4: use token_sort_ratio + partial_ratio instead of plain
        # fuzz.ratio, and lower threshold from 70 → 60 so short terms like
        # "fever" correctly map to "high_fever" / "mild_fever"
        res_token = process.extractOne(norm, SYMPTOM_LIST, scorer=fuzz.token_sort_ratio)
        res_partial = process.extractOne(norm, SYMPTOM_LIST, scorer=fuzz.partial_ratio)

        # Pick whichever scorer produced the higher score
        best = None
        best_score = 0
        for res in (res_token, res_partial):
            if res and res[1] > best_score:
                best = res
                best_score = res[1]

        if best and best_score >= 60:
            vector[SYMPTOM_LIST.index(best[0])] = 1
            matched += 1

    return np.array(vector).reshape(1, -1), matched


def predict(structured_json, interview_quality):
    # Fix Bug 3: merge both symptom lists so associated_symptoms are not ignored
    primary = [s['name'] for s in structured_json.get('symptoms', []) if s.get('name')]
    associated = structured_json.get('associated_symptoms', [])
    all_symptoms = list(dict.fromkeys(primary + associated))  # deduplicate, preserve order

    vector, matched = map_to_vector(all_symptoms)
    proba = MODEL.predict_proba(vector)[0]
    top5_idx = np.argsort(proba)[-5:][::-1]
    top5_prob = np.sort(proba)[-5:][::-1]

    diseases = LE.classes_
    quality_mult = {'high': 1.0, 'medium': 0.85, 'low': 0.65}.get(interview_quality, 0.65)

    # Fix Bug 5: remove the redundant coverage multiplier; quality_mult alone
    # reflects interview completeness without unfairly penalising short symptom lists
    score = round(min(float(top5_prob[0]) * quality_mult * 100, 99.0), 1)

    tier = 'High' if score >= 80 else 'Medium' if score >= 50 else 'Low'
    color = 'green' if tier == 'High' else 'yellow' if tier == 'Medium' else 'red'

    top5 = []
    for i in range(5):
        d = diseases[top5_idx[i]]
        dr = desc_df[desc_df['Disease'].str.strip() == d.strip()]
        pr = prec_df[prec_df['Disease'].str.strip() == d.strip()]

        top5.append({
            'disease': d,
            'probability': round(float(top5_prob[i]) * 100, 1),
            'description': dr['Description'].values[0] if len(dr) else 'N/A',
            'precautions': list(pr.iloc[0, 1:].dropna()) if len(pr) else []
        })

    return {
        'score': score,
        'tier': tier,
        'color': color,
        'matched_symptoms': matched,
        'top5': top5
    }