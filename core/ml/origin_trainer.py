"""Basic LightGBM trainer scaffold for origin inference.

Functions:
- extract_training_data(): collect labeled examples from OriginLabel and products
- train_model(output_dir, min_samples_per_class=10, test_size=0.2): trains and saves model and artifacts
- predict_products(model_dir, queryset, apply=False): load model and predict; optionally apply suggestions

This module intentionally raises clear errors when optional packages (lightgbm, scikit-learn) are missing.
"""
from __future__ import annotations

import os
import json
import logging
from typing import List, Tuple, Dict, Any
from pathlib import Path
from collections import Counter
from datetime import datetime

from django.utils import timezone
from django.db.models import Q

from core.models import Product, OriginLabel

logger = logging.getLogger(__name__)

# Optional dependencies
try:
    import lightgbm as lgb
except Exception as e:
    lgb = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    import joblib
except Exception:
    TfidfVectorizer = None
    LabelEncoder = None
    train_test_split = None
    classification_report = None
    joblib = None


def _ensure_ml_available():
    missing = []
    if lgb is None:
        missing.append('lightgbm')
    if TfidfVectorizer is None or LabelEncoder is None or joblib is None:
        missing.append('scikit-learn and joblib')
    if missing:
        raise RuntimeError(
            'Missing required ML packages: %s. Please `pip install lightgbm scikit-learn joblib`.' % ', '.join(missing)
        )


def _product_text(p: Product) -> str:
    parts = [p.name or '']
    if p.description:
        parts.append(p.description)
    if p.keywords_for_ai:
        parts.append(p.keywords_for_ai)
    if getattr(p, 'vendor', None) and getattr(p.vendor, 'location_country', None):
        parts.append(str(p.vendor.location_country))
    return ' \n '.join(parts)


def extract_training_data(min_samples_per_class: int = 5) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """Collect training examples from OriginLabel where label_country is set.

    Returns: (texts, labels, info)
    info includes counts per class and total examples
    """
    labels_qs = OriginLabel.objects.filter(label_country__isnull=False).select_related('product')
    texts = []
    labels = []

    for ol in labels_qs:
        texts.append(_product_text(ol.product))
        labels.append(ol.label_country)

    counts = Counter(labels)
    info = {'total': len(labels), 'counts': dict(counts)}

    # Filter classes with too few examples
    valid_classes = {c for c, cnt in counts.items() if cnt >= min_samples_per_class}
    if not valid_classes:
        raise RuntimeError(f'Not enough labeled examples. Class counts: {info["counts"]}')

    filtered_texts = []
    filtered_labels = []
    for t, lab in zip(texts, labels):
        if lab in valid_classes:
            filtered_texts.append(t)
            filtered_labels.append(lab)

    info['filtered_total'] = len(filtered_labels)
    info['filtered_counts'] = dict(Counter(filtered_labels))

    return filtered_texts, filtered_labels, info


def train_model(output_dir: str = 'core/ml/models', min_samples_per_class: int = 5, test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
    """Train a LightGBM classifier using TF-IDF features. Saves model, vectorizer, and label encoder to output_dir.

    Returns a summary dict with metrics and paths.
    """
    _ensure_ml_available()

    texts, labels, info = extract_training_data(min_samples_per_class=min_samples_per_class)

    vectorizer = TfidfVectorizer(min_df=1, max_features=20000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(texts)

    le = LabelEncoder()
    y = le.fit_transform(labels)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)

    lgb_train = lgb.Dataset(X_train, label=y_train)
    lgb_eval = lgb.Dataset(X_test, label=y_test, reference=lgb_train)

    params = {
        'objective': 'multiclass',
        'num_class': len(le.classes_),
        'metric': 'multi_logloss',
        'verbosity': -1,
        'seed': random_state,
    }

    num_round = 100
    model = lgb.train(params, lgb_train, num_boost_round=num_round, valid_sets=[lgb_train, lgb_eval], early_stopping_rounds=10, verbose_eval=False)

    preds_proba = model.predict(X_test)
    preds = preds_proba.argmax(axis=1)

    report = classification_report(y_test, preds, target_names=list(le.classes_), output_dict=True)

    # Save artifacts
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / 'origin_lightgbm.txt'
    vect_path = out_dir / 'origin_vectorizer.joblib'
    enc_path = out_dir / 'origin_label_encoder.joblib'
    meta_path = out_dir / 'train_metadata.json'

    model.save_model(str(model_path))
    joblib.dump(vectorizer, str(vect_path))
    joblib.dump(le, str(enc_path))

    meta = {
        'trained_at': datetime.utcnow().isoformat() + 'Z',
        'num_classes': len(le.classes_),
        'classes': list(le.classes_),
        'report': report,
        'params': params,
    }
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    summary = {
        'model_path': str(model_path),
        'vectorizer_path': str(vect_path),
        'label_encoder_path': str(enc_path),
        'meta_path': str(meta_path),
        'report': report,
        'info': info,
    }
    logger.info('Training complete: %s', summary)
    return summary


def predict_products(model_dir: str = 'core/ml/models', only_missing: bool = True, limit: int = 0, apply: bool = False, min_confidence: float = 0.5, queryset=None) -> Dict[str, Any]:
    """Load trained artifacts and generate predictions for products.

    If apply=True, persist suggestions to Product.suggested_origin_country and related fields.
    If `queryset` is provided, predictions will be run on that queryset (useful for admin actions).
    Returns summary dict with counts and sample predictions.
    """
    _ensure_ml_available()

    out_dir = Path(model_dir)
    vect_path = out_dir / 'origin_vectorizer.joblib'
    enc_path = out_dir / 'origin_label_encoder.joblib'
    model_path = out_dir / 'origin_lightgbm.txt'
    meta_path = out_dir / 'train_metadata.json'

    if not (vect_path.exists() and enc_path.exists() and model_path.exists()):
        raise RuntimeError('Model artifacts not found in %s' % model_dir)

    vectorizer = joblib.load(str(vect_path))
    le = joblib.load(str(enc_path))
    booster = lgb.Booster(model_file=str(model_path))

    if queryset is not None:
        qs = queryset.select_related('vendor')
        if only_missing:
            qs = qs.filter(origin_country__isnull=True)
        if limit and limit > 0:
            qs = qs[:limit]
    else:
        qs = Product.objects.all().select_related('vendor')
        if only_missing:
            qs = qs.filter(origin_country__isnull=True)
        if limit and limit > 0:
            qs = qs[:limit]

    applied = 0
    suggested = 0
    samples = []

    for p in qs:
        txt = _product_text(p)
        X = vectorizer.transform([txt])
        proba = booster.predict(X)
        # proba shape: (1, num_classes)
        if proba.ndim == 2:
            probs = proba[0]
        else:
            probs = proba
        idx = int(probs.argmax())
        conf = float(probs[idx])
        country = le.inverse_transform([idx])[0]

        metadata = {'model': 'lightgbm', 'confidence': conf, 'model_dir': str(out_dir)}

        # Only suggest if confidence >= min_confidence
        if conf >= min_confidence:
            suggested += 1
            if apply:
                p.suggested_origin_country = country
                p.origin_confidence = conf
                p.origin_inferred_by = 'ml'
                p.origin_inference_metadata = metadata
                p.origin_inferred_at = timezone.now()
                p.origin_inference_status = 'suggested'
                p.save(update_fields=['suggested_origin_country', 'origin_confidence', 'origin_inferred_by', 'origin_inference_metadata', 'origin_inferred_at', 'origin_inference_status'])
                applied += 1
        samples.append({'product_id': p.id, 'predicted_country': country, 'confidence': conf})

    summary = {'checked': qs.count() if hasattr(qs, 'count') else len(samples), 'suggested': suggested, 'applied': applied, 'samples': samples[:20]}
    logger.info('Prediction summary: %s', summary)
    return summary
