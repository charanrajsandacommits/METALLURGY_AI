# =============================================================================
# ml_engine.py — XGBoost + SHAP Explainability Layer
# Place this file inside your  services/  folder
#
# Key design for Render free tier:
#   - Model is RETRAINED at startup from test_cases.csv (no .pkl file needed)
#   - This avoids the ephemeral filesystem problem where saved files get wiped
#   - Training takes ~3 seconds on 94 rows — acceptable for cold start
# =============================================================================

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix, ConfusionMatrixDisplay
from sklearn.utils.class_weight import compute_class_weight
import xgboost as xgb
import shap

warnings.filterwarnings('ignore')

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'test_cases.csv')
PLOT_DIR  = os.path.join(BASE_DIR, '..', 'static', 'ml_plots')
os.makedirs(PLOT_DIR, exist_ok=True)

FEATURES = [
    'production', 'energy', 'water', 'purity',
    'energy_intensity', 'water_intensity',
    'energy_water_ratio', 'low_purity_flag',
    'type_encoded'
]


# =============================================================================
# INTERNAL HELPERS
# =============================================================================

def _build_features(df, le_type, fit=False):
    """Add derived features and encode metal type."""
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.startswith('Unnamed')]

    df['energy_intensity']   = df['energy']  / df['production'].clip(lower=1)
    df['water_intensity']    = df['water']   / df['production'].clip(lower=1)
    df['energy_water_ratio'] = df['energy']  / df['water'].clip(lower=1)
    df['low_purity_flag']    = (df['purity'] < 40).astype(int)

    if fit:
        df['type_encoded'] = le_type.fit_transform(df['type'].str.strip())
    else:
        known = set(le_type.classes_)
        df['type'] = df['type'].apply(lambda x: x if x in known else le_type.classes_[0])
        df['type_encoded'] = le_type.transform(df['type'].str.strip())

    return df[FEATURES].values


def _save_shap_plots(model, X_scaled, encoders):
    """Generate and save SHAP summary + bar plots to static/ml_plots/."""
    try:
        explainer   = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_scaled)

        # Summary (beeswarm)
        plt.figure(figsize=(10, 7))
        shap.summary_plot(shap_values, X_scaled,
                          feature_names=FEATURES,
                          class_names=encoders['zone'].classes_,
                          show=False)
        plt.title("SHAP Summary — Feature Impact on Zone Classification",
                  fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, 'shap_summary.png'), dpi=150, bbox_inches='tight')
        plt.close()

        # Bar (mean |SHAP|)
        plt.figure(figsize=(9, 6))
        shap.summary_plot(shap_values, X_scaled,
                          feature_names=FEATURES,
                          plot_type='bar',
                          class_names=encoders['zone'].classes_,
                          show=False)
        plt.title("SHAP Feature Importance — Mean |SHAP| per Class",
                  fontsize=13, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, 'shap_bar.png'), dpi=150, bbox_inches='tight')
        plt.close()

        print("[ML] SHAP plots saved to static/ml_plots/")
    except Exception as e:
        print(f"[ML] SHAP plot generation skipped: {e}")


def _save_confusion_matrix(y_test, y_pred, zone_names):
    """Save confusion matrix plot."""
    try:
        cm  = confusion_matrix(y_test, y_pred)
        fig, ax = plt.subplots(figsize=(7, 5))
        ConfusionMatrixDisplay(confusion_matrix=cm,
                               display_labels=zone_names).plot(ax=ax, colorbar=False, cmap='Blues')
        ax.set_title("Confusion Matrix — Zone Classification (XGBoost, 20% hold-out)",
                     fontsize=11, fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(PLOT_DIR, 'confusion_matrix.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print("[ML] Confusion matrix saved to static/ml_plots/")
    except Exception as e:
        print(f"[ML] Confusion matrix skipped: {e}")


# =============================================================================
# PUBLIC API — called by app.py
# =============================================================================

def train_and_return():
    """
    Trains XGBoost on test_cases.csv and returns
    (model, encoders, scaler, metrics_dict).

    Called once at app startup — no .pkl files needed.
    """
    # ── Load data ──────────────────────────────────────────────────────
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.startswith('Unnamed')]
    df = df.dropna(subset=['zone_status'])
    df['type']        = df['type'].str.strip()
    df['zone_status'] = df['zone_status'].str.strip()

    # ── Encoders ───────────────────────────────────────────────────────
    le_type = LabelEncoder()
    le_zone = LabelEncoder()

    X = _build_features(df, le_type, fit=True)
    y = le_zone.fit_transform(df['zone_status'].values)

    encoders = {'type': le_type, 'zone': le_zone}

    # ── Scale ──────────────────────────────────────────────────────────
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ── Class weights (handles 83 Red / 6 Green / 5 Orange imbalance) ─
    classes = np.unique(y)
    weights = compute_class_weight('balanced', classes=classes, y=y)
    sample_weights = np.array([weights[lbl] for lbl in y])

    # ── Train / test split ─────────────────────────────────────────────
    X_tr, X_te, y_tr, y_te, sw_tr, _ = train_test_split(
        X_scaled, y, sample_weights,
        test_size=0.2, random_state=42, stratify=y
    )

    # ── XGBoost model ──────────────────────────────────────────────────
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='mlogloss',
        random_state=42,
        verbosity=0
    )
    model.fit(X_tr, y_tr, sample_weight=sw_tr)

    # ── Metrics ────────────────────────────────────────────────────────
    y_pred    = model.predict(X_te)
    acc       = accuracy_score(y_te, y_pred)
    report    = classification_report(y_te, y_pred,
                                      target_names=le_zone.classes_,
                                      zero_division=0)

    cv        = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_scaled, y, cv=cv,
                                scoring='accuracy', n_jobs=-1)

    metrics = {
        'test_accuracy':  round(acc * 100, 1),
        'cv_mean':        round(cv_scores.mean() * 100, 1),
        'cv_std':         round(cv_scores.std()  * 100, 1),
        'report':         report
    }

    print("\n" + "="*52)
    print("  Metallurgy AI — XGBoost Training Complete")
    print("="*52)
    print(f"  Hold-out Accuracy : {metrics['test_accuracy']}%")
    print(f"  CV Accuracy (5-fold): {metrics['cv_mean']}% ± {metrics['cv_std']}%")
    print("="*52)

    # ── Save plots (non-blocking) ──────────────────────────────────────
    _save_shap_plots(model, X_scaled, encoders)
    _save_confusion_matrix(y_te, y_pred, le_zone.classes_)

    return model, encoders, scaler, metrics


def explain_prediction(model, encoders, scaler,
                        site_type, purity, energy, water, production):
    """
    Returns ML zone prediction + SHAP top-5 feature drivers
    for a single site audit call.
    """
    le_type = encoders['type']
    le_zone = encoders['zone']

    # Encode input
    known    = set(le_type.classes_)
    type_str = site_type.strip() if site_type.strip() in known else le_type.classes_[0]
    type_enc = le_type.transform([type_str])[0]

    prod_f  = max(float(production), 1.0)
    enrg_f  = float(energy)
    watr_f  = float(water)

    x_row = np.array([[
        prod_f, enrg_f, watr_f, float(purity),
        enrg_f / prod_f,
        watr_f / prod_f,
        enrg_f / max(watr_f, 1.0),
        int(float(purity) < 40),
        type_enc
    ]])
    x_scaled = scaler.transform(x_row)

    # Predict
    pred_class = model.predict(x_scaled)[0]
    pred_proba = model.predict_proba(x_scaled)[0]
    zone_label = le_zone.inverse_transform([pred_class])[0]

    # SHAP for this row
    explainer = shap.TreeExplainer(model)
    sv        = explainer.shap_values(x_scaled)   # shape: (n_classes, 1, n_features)
    # sv shape can vary — handle safely
    if isinstance(sv, list):
        sv_pred = sv[pred_class][0] if pred_class < len(sv) else sv[0][0]
    else:
        sv_pred = sv[0]

    top_drivers = sorted(
        zip(FEATURES, sv_pred),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:5]

    return {
        'ml_zone':       zone_label,
        'ml_confidence': round(float(max(pred_proba)) * 100, 1),
        'top_drivers': [
            {
                'feature':   f,
                'shap_value': round(float(v), 4),
                'direction':  'increases risk' if v > 0 else 'reduces risk'
            }
            for f, v in top_drivers
        ],
        'class_proba': {
            cls: round(float(p) * 100, 1)
            for cls, p in zip(le_zone.classes_, pred_proba)
        }
    }
