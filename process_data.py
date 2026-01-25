import pandas as pd
import geopandas as gpd
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, 'data', 'global_mining')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'master_mining_data.csv')

def generate_master():
    print(f"Checking for input directory: {INPUT_DIR}")
    
    gpkg_path = os.path.join(INPUT_DIR, 'facilities.gpkg')
    csv_path = os.path.join(INPUT_DIR, 'minerals.csv')

    if not os.path.exists(gpkg_path) or not os.path.exists(csv_path):
        print("❌ ERROR: Required files missing in data/global_mining")
        return

    print("✅ Files found! Calculating coordinates from Polygons...")

    # 1. Load Locations
    gdf = gpd.read_file(gpkg_path)

    # FIX: Get the center point of the Polygon to extract Lat/Long
    # We use .to_crs to ensure the math is correct, then back to GPS coords
    centroids = gdf.geometry.centroid
    gdf['latitude'] = centroids.y
    gdf['longitude'] = centroids.x

    # 2. Load Production
    df_prod = pd.read_csv(csv_path)

    # 3. Merge on 'facility_id'
    # Filtering for 2021 (or the latest available year)
    merged = pd.merge(gdf, df_prod[df_prod['year'] == 2021], on='facility_id')

    if merged.empty:
        print("⚠️ Warning: No matching data found for year 2021. Trying 2020...")
        merged = pd.merge(gdf, df_prod[df_prod['year'] == 2020], on='facility_id')

    # 4. Save
    cols_to_save = ['facility_name', 'country', 'commodity', 'latitude', 'longitude', 'production', 'unit']
    # Filter only for columns that exist to prevent new errors
    existing_cols = [c for c in cols_to_save if c in merged.columns]
    
    merged[existing_cols].to_csv(OUTPUT_FILE, index=False)
    
    print(f"🎉 SUCCESS! Master dataset created with {len(merged)} records.")
    print(f"Location: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_master()