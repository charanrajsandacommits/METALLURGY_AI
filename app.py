# =============================================================================
# app.py — Metallurgy AI v2.0
# Changes from v1.0:
#   1. Google Maps API key loaded from environment (not hardcoded)
#   2. ML engine (XGBoost + SHAP) trained at startup and added to audit response
#   3. All original response fields preserved — interface unchanged
# =============================================================================

from flask import Flask, render_template, request, jsonify
from services.lca_engine import LCAEngine
from services.maps_service import MapsService
import pandas as pd
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# ── API Key from environment (set this in Render dashboard) ──────────────────
API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
if not API_KEY:
    logging.warning("GOOGLE_MAPS_API_KEY not set. Map features may not work.")

# ── Rule-based LCA engine (original — unchanged) ─────────────────────────────
ai   = LCAEngine()
maps = MapsService(API_KEY)

# ── Dataset path (same logic as original) ────────────────────────────────────
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
MASTER_DATA_PATH = os.path.join(BASE_DIR, 'master_mining_data.csv')
if not os.path.exists(MASTER_DATA_PATH):
    MASTER_DATA_PATH = os.path.join(BASE_DIR, 'data', 'master_mining_data.csv')

# ── ML engine: train at startup (no .pkl needed — safe for Render free tier) ─
ML_AVAILABLE = False
ml_model     = None
ml_encoders  = None
ml_scaler    = None
ml_metrics   = None

try:
    from services.ml_engine import train_and_return, explain_prediction
    ml_model, ml_encoders, ml_scaler, ml_metrics = train_and_return()
    ML_AVAILABLE = True
    logging.info("[OK] ML engine ready — XGBoost + SHAP loaded.")
except Exception as e:
    logging.warning(f"[WARN] ML engine unavailable, using rule-based only. Reason: {e}")


# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    # api_key passed to template so index.html uses {{ api_key }} — not hardcoded
    return render_template('index.html', api_key=API_KEY)


@app.route('/audit', methods=['POST'])
def audit():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        site_name = data.get('name', '').strip()
        site_type = data.get('type', 'General').strip()
        prod      = float(data.get('production', 1))
        purity    = float(data.get('purity', 0))
        energy    = float(data.get('energy', 0))
        water     = float(data.get('water', 0))

        lat, lng = None, None

        # 1. CSV Lookup for Coordinates (same as original)
        if os.path.exists(MASTER_DATA_PATH):
            df    = pd.read_csv(MASTER_DATA_PATH)
            match = df[df['facility_name'].str.lower() == site_name.lower()].head(1)
            if match.empty:
                match = df[df['facility_name'].str.lower()
                           .str.contains(site_name.lower(), na=False)].head(1)
            if not match.empty:
                lat = float(match.iloc[0]['latitude'])
                lng = float(match.iloc[0]['longitude'])

        # 2. Maps API Fallback (same as original)
        if lat is None or lng is None:
            lat, lng = maps.get_coordinates(site_name)

        # 3. Final Default Fallback — Jharkhand (same as original)
        if lat is None or lng is None:
            lat, lng = 23.3441, 85.3096

        # ── Rule-based LCA analysis (original — fully preserved) ──────────────
        res = ai.analyze(site_type, purity, energy, water, prod)

        res.update({
            'location':      {'lat': lat, 'lng': lng},
            'circularity':   round(max(0, 100 - (res['score'] / 1.5)), 1),
            'impact_radius': round(res['score'] * 800, 2)
        })

        # ── ML + SHAP layer (additive — does NOT affect any existing fields) ──
        if ML_AVAILABLE:
            try:
                res['ml_prediction'] = explain_prediction(
                    ml_model, ml_encoders, ml_scaler,
                    site_type, purity, energy, water, prod
                )
            except Exception as ml_err:
                logging.warning(f"ML prediction failed for this input: {ml_err}")
                res['ml_prediction'] = None
        else:
            res['ml_prediction'] = None

        return jsonify(res)

    except Exception as e:
        logging.error(f"Audit Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
