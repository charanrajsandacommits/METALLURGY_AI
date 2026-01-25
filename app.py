from flask import Flask, render_template, request, jsonify
from services.lca_engine import LCAEngine
from services.maps_service import MapsService
import pandas as pd
import logging
import os

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Initialize Services
ai = LCAEngine()
maps = MapsService('AIzaSyA3OiVMUPo1N79inichJ2ajZmX9J3fmoQY') 

# Define Path for Dataset
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_DATA_PATH = os.path.join(BASE_DIR, 'master_mining_data.csv')
if not os.path.exists(MASTER_DATA_PATH):
    MASTER_DATA_PATH = os.path.join(BASE_DIR, 'data', 'master_mining_data.csv')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/audit', methods=['POST'])
def audit():
    try:
        data = request.get_json()
        if not data: return jsonify({"error": "No data received"}), 400

        site_name = data.get('name', '').strip()
        site_type = data.get('type', 'General').strip() # This is now the Metal Type
        prod = float(data.get('production', 1))
        purity = float(data.get('purity', 0))
        energy = float(data.get('energy', 0))
        water = float(data.get('water', 0))

        lat, lng = None, None

        # 1. CSV Lookup for Coordinates
        if os.path.exists(MASTER_DATA_PATH):
            df = pd.read_csv(MASTER_DATA_PATH)
            match = df[df['facility_name'].str.lower() == site_name.lower()].head(1)
            if match.empty:
                match = df[df['facility_name'].str.lower().str.contains(site_name.lower(), na=False)].head(1)
            
            if not match.empty:
                lat, lng = float(match.iloc[0]['latitude']), float(match.iloc[0]['longitude'])

        # 2. Maps API Fallback
        if lat is None or lng is None:
            lat, lng = maps.get_coordinates(site_name)

        # 3. Final Default Fallback (Jharkhand)
        if lat is None or lng is None:
            lat, lng = 23.3441, 85.3096

        # Dynamic AI Analysis (Passes the site_type)
        res = ai.analyze(site_type, purity, energy, water, prod)
        
        res.update({
            'location': {'lat': lat, 'lng': lng},
            'circularity': round(max(0, 100 - (res['score'] / 1.5)), 1),
            'impact_radius': round(res['score'] * 800, 2)
        })

        return jsonify(res)
    except Exception as e:
        logging.error(f"Audit Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)