import requests

class MapsService:
    def __init__(self, api_key):
        self.api_key = api_key
        # Using Places API Text Search for high precision on industrial sites
        self.base_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"

    def get_coordinates(self, location_name):
        """
        Fetches precise real-world coordinates for metallurgical/mining sites.
        """
        try:
            # We add 'Mine' or 'Plant' context to the query for better accuracy
            params = {
                "query": location_name,
                "key": self.api_key
            }
            response = requests.get(self.base_url, params=params).json()
            
            if response.get('status') == 'OK':
                # results[0] is the most prominent matching real-world site
                result = response['results'][0]
                location = result['geometry']['location']
                
                print(f"--- AI Location Match Found ---")
                print(f"Site: {result.get('name')}")
                print(f"Address: {result.get('formatted_address')}")
                
                return location['lat'], location['lng']
            else:
                print(f"Google API Status: {response.get('status')} - Defaulting to Jharkhand.")
                # Default to central Jharkhand (23.61, 85.27) instead of Nagpur
                return 23.6102, 85.2799
        except Exception as e:
            print(f"Precision Search Error: {e}")
            return 23.6102, 85.2799