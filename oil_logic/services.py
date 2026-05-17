import requests
from django.conf import settings
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

class VehicleLookupService:
    """
    Service to handle vehicle registration data lookup from external APIs.
    """
    
    @staticmethod
    def lookup_by_plate(license_plate):
        """
        Main entry point for looking up a vehicle.
        Integrates with RapidAPI Vahan Provider.
        """
        api_key = getattr(settings, 'VEHICLE_API_KEY', None)
        api_host = getattr(settings, 'VEHICLE_API_HOST', 'vahan-api.p.rapidapi.com')
        
        # Security: Don't make external calls if key is default/placeholder
        if not api_key or 'YourRapid' in api_key:
            return VehicleLookupService.get_mock_data(license_plate)

        url = f"https://{api_host}/vahan"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": api_host
        }
        
        try:
            response = requests.get(url, headers=headers, params={"plate": license_plate.replace(" ", "")}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Adapt API response to our internal format
                return {
                    'brand': data.get('manufacturer', 'Unknown'),
                    'model': data.get('model', 'Unknown'),
                    'year': data.get('reg_date', '2020')[:4], # Extract year from YYYY-MM-DD
                    'type': data.get('vehicle_type', 'Car'),
                    'engine_type': data.get('fuel_type', 'Petrol'),
                    'reg_date': data.get('reg_date'),
                    'puc_expiry': data.get('puc_expiry', '2025-12-31'),
                    'owner_name': data.get('owner_name', 'Verified Owner'),
                    'is_real': True
                }
        except Exception as e:
            print(f"API Lookup Failed: {e}")
        
        return VehicleLookupService.get_mock_data(license_plate)

    @staticmethod
    def get_mock_data(license_plate):
        """
        Returns high-quality simulated data for development if no API key is present.
        """
        # Simulated responses for common test plates
        sim_db = {
            "MH12AB1234": {
                'brand': 'Maruti Suzuki', 'model': 'Swift VXI', 'year': '2022',
                'type': 'Car', 'engine_type': 'Petrol', 'reg_date': '2022-05-15',
                'puc_expiry': '2025-05-15', 'owner_name': 'Rahul Sharma', 'is_real': False
            },
            "KA01HH9999": {
                'brand': 'BMW', 'model': '3 Series', 'year': '2023',
                'type': 'Car', 'engine_type': 'Petrol', 'reg_date': '2023-01-10',
                'puc_expiry': '2026-01-10', 'owner_name': 'Anita Desai', 'is_real': False
            }
        }
        return sim_db.get(license_plate.replace(" ", "").upper())

class AIAgentService:
    """
    Core engine for GlideAdvisor AI.
    Handles context retrieval from Shop/Academy and interacts with LLM.
    """
    
    @staticmethod
    def get_response(user_message, user=None):
        """
        Process user message and return an AI response.
        In a real scenario, this would call an LLM (OpenAI/Gemini/Claude).
        """
        message_lower = user_message.lower()
        
        # simulated logic based on known keywords
        if 'viscosity' in message_lower:
            return "Viscosity is the most critical property of engine oil. It's the oil's resistance to flow. For example, in 5W-30, '5W' represents cold-start performance, and '30' represents high-temperature protection. Check our **Academy** for a deep dive!"
        
        if 'synthetic' in message_lower or 'mineral' in message_lower:
            return "Synthetic oils are lab-engineered for molecular uniformity, offering 3x more protection than mineral oils. They handle extreme heat much better and prevent sludge. I always recommend **Full Synthetic** for modern engines."
        
        if 'hello' in message_lower or 'hi' in message_lower:
            return "Hello! I'm GlideAdvisor. I can help with oil recommendations, technical specs, or managing your garage. What's on your mind?"
            
        if 'price' in message_lower or 'cost' in message_lower:
            return "Our premium oils range from $25 to $75. The **Amsoil Signature Series** is our top-tier choice for maximum performance, while **Shell Helix** offers great value. Check the **Shop** for live pricing!"

        if 'change' in message_lower and ('when' in message_lower or 'interval' in message_lower):
            return "For most modern synthetic oils, a change every 10,000 to 12,000 KM is ideal. However, if you drive in 'Severe Conditions' (short city trips), I recommend every 7,500 KM. You can track this in your **Garage**!"

        return "That's an interesting question! As a technical advisor, I recommend checking our **Academy** for specialized theory or using our **Recommender** to find the exact match for your vehicle. Can I help you with a specific viscosity or brand?"

    @staticmethod
    def analyze_recommendation(vehicle_data, oil_data):
        """
        Expert Analysis: Compares DB results with LLM global knowledge.
        Uses Groq (Llama-3) for ultra-fast reasoning.
        """
        api_key = getattr(settings, 'GROQ_API_KEY', None)
        if not api_key or 'YourGroq' in api_key:
            return "Based on database metrics, this oil matches your vehicle's manufacturer specifications perfectly. (Connect Groq API for expert reasoning)"

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""
        Vehicle: {vehicle_data.get('brand')} {vehicle_data.get('model')} ({vehicle_data.get('year')})
        Condition: {vehicle_data.get('driving_condition')}, Odometer: {vehicle_data.get('odometer_km')} KM
        Recommended Oil: {oil_data.get('brand')} {oil_data.get('viscosity')} ({oil_data.get('oil_type')})
        
        As a senior automotive engineer, explain in 2-3 concise sentences why this specific oil is the best technical choice for this vehicle under these conditions. Mention viscosity or engine protection.
        """

        payload = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": "You are a senior automotive lubrication expert. Be technical yet concise."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 150
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            print(f"LLM Consultation Failed: {e}")
        
        return "This oil provides optimized lubrication and thermal stability tailored to your engine's specific wear profile and driving environment."

class GeocodingService:
    """
    Utility to convert address/zip to lat/lng using OpenStreetMap Nominatim.
    """
    @staticmethod
    def geocode(query):
        geolocator = Nominatim(user_agent="oilrec_precision_locator")
        try:
            location = geolocator.geocode(query, timeout=10)
            if location:
                return {
                    'lat': location.latitude,
                    'lng': location.longitude,
                    'address': location.address
                }
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding Error: {e}")
        return None

class GarageLocatorService:
    """
    Service to find the 'bestest' garage shops near a location.
    Integrates with SerpApi for real-world data, OSM for free search, or provides curated simulations.
    """
    
    @staticmethod
    def search_best_garages(query, lat=None, lng=None):
        print(f"DEBUG: Starting garage search for: {query} (Lat: {lat}, Lng: {lng})")
        # 1. If we don't have lat/lng, try geocoding first
        if not lat or not lng:
            geo_data = GeocodingService.geocode(query)
            if geo_data:
                lat, lng = geo_data['lat'], geo_data['lng']
                print(f"DEBUG: Geocoded to: {lat}, {lng}")
        
        # 2. Try SerpApi if key is available
        api_key = getattr(settings, 'SERPAPI_API_KEY', None)
        if api_key and 'your_serpapi_key' not in api_key and len(api_key) > 20:
            print("DEBUG: Attempting SerpApi search...")
            results = GarageLocatorService.search_serpapi(query, lat, lng)
            if results: return results

        # 3. Fallback to OpenStreetMap Overpass API (Free)
        if lat and lng:
            print("DEBUG: Attempting OSM Overpass search...")
            osm_results = GarageLocatorService.search_osm(lat, lng, radius_km=20)
            if osm_results and len(osm_results) > 0:
                print(f"DEBUG: Found {len(osm_results)} real results via OSM.")
                return osm_results

        # 4. Final fallback to simulation
        print("DEBUG: No real data found. Falling back to simulation.")
        return GarageLocatorService.get_simulated_garages(query)

    @staticmethod
    def search_osm(lat, lng, radius_km=20):
        """
        Queries OpenStreetMap Overpass API for car repair/garages.
        """
        overpass_url = "http://overpass-api.de/api/interpreter"
        # Overpass QL: search for car_repair, garages, or fuel stations with repair services
        radius_meters = radius_km * 1000
        query = f"""
        [out:json][timeout:25];
        (
          node["shop"="car_repair"](around:{radius_meters},{lat},{lng});
          way["shop"="car_repair"](around:{radius_meters},{lat},{lng});
          node["craft"="car_repair"](around:{radius_meters},{lat},{lng});
          way["craft"="car_repair"](around:{radius_meters},{lat},{lng});
          node["amenity"="garage"](around:{radius_meters},{lat},{lng});
          way["amenity"="garage"](around:{radius_meters},{lat},{lng});
          node["amenity"="fuel"]["service:repair"="yes"](around:{radius_meters},{lat},{lng});
          node["amenity"="car_service"](around:{radius_meters},{lat},{lng});
        );
        out center;
        """
        try:
            response = requests.get(overpass_url, params={'data': query}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                results = []
                for i, element in enumerate(data.get('elements', [])):
                    tags = element.get('tags', {})
                    lat_res = element.get('lat') or element.get('center', {}).get('lat')
                    lng_res = element.get('lon') or element.get('center', {}).get('lon')
                    
                    results.append({
                        'name': tags.get('name', 'Independent Garage'),
                        'address': tags.get('addr:full') or f"{tags.get('addr:street', '')} {tags.get('addr:city', '')}".strip() or "Nearby Location",
                        'rating': 4.0 + (i % 10) / 10, # OSM doesn't have ratings, simulate for UI
                        'reviews': 10 + (i * 7) % 50,
                        'is_bestest': i == 0,
                        'type': tags.get('shop', 'Auto Repair'),
                        'source': 'osm',
                        'lat': lat_res,
                        'lng': lng_res,
                        'directions_url': f"https://www.google.com/maps/dir/?api=1&destination={lat_res},{lng_res}"
                    })
                return results[:15]
        except Exception as e:
            print(f"OSM Overpass Search Failed: {e}")
        return None

    @staticmethod
    def search_serpapi(query, lat, lng):
        """
        Uses SerpApi Google Local Search for high-precision real data.
        """
        api_key = getattr(settings, 'SERPAPI_API_KEY', None)
        if not api_key: return None
        
        url = "https://serpapi.com/search"
        params = {
            "engine": "google_local",
            "q": f"automotive oil change garage {query}",
            "api_key": api_key,
            "num": 10
        }
        
        # If we have coordinates, use 'll' for precise local search
        if lat and lng:
            params["ll"] = f"@{lat},{lng},14z" # @lat,lng,zoom
        else:
            params["location"] = query # fallback to text location

        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"DEBUG: SerpApi Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                local_results = data.get('local_results', [])
                print(f"DEBUG: Found {len(local_results)} results via SerpApi.")
                if not local_results:
                    # Try a broader search if no local results
                    params["q"] = f"car repair {query}"
                    response = requests.get(url, params=params, timeout=10)
                    local_results = response.json().get('local_results', [])
                    print(f"DEBUG: Broad search found {len(local_results)} results.")

                local_results.sort(key=lambda x: x.get('rating', 0), reverse=True)
                
                formatted_results = []
                for i, res in enumerate(local_results[:10]):
                    gps = res.get('gps_coordinates', {})
                    lat_res = gps.get('latitude') or gps.get('lat')
                    lng_res = gps.get('longitude') or gps.get('lng')
                    
                    formatted_results.append({
                        'name': res.get('title'),
                        'address': res.get('address') or res.get('vicinity', 'Address not available'),
                        'rating': res.get('rating') or 4.0,
                        'reviews': res.get('reviews') or 0,
                        'is_bestest': i == 0,
                        'type': res.get('type', 'Auto Repair Shop'),
                        'source': 'google_serp',
                        'lat': lat_res,
                        'lng': lng_res,
                        'thumbnail': res.get('thumbnail'),
                        'directions_url': f"https://www.google.com/maps/dir/?api=1&destination={lat_res},{lng_res}" if lat_res else f"https://www.google.com/maps/search/?api=1&query={res.get('title')}"
                    })
                return formatted_results
            else:
                print(f"DEBUG: SerpApi Error: {response.text}")
        except Exception as e:
            print(f"DEBUG: SerpApi Exception: {e}")
        return None

    @staticmethod
    def get_simulated_garages(query):
        # ... implementation from previous turn, but improved with directions_url ...
        clean_query = query.strip()
        is_pincode = clean_query.isdigit() and len(clean_query) == 6
        if is_pincode:
            pincode_map = {'390001': 'Vadodara', '110001': 'Delhi', '400001': 'Mumbai', '560001': 'Bangalore'}
            city = pincode_map.get(clean_query, f"Zone {clean_query[:2]}")
        else:
            city = query.split(',')[0].strip().title()
        
        return [
            {
                'name': f"{city} Elite Automotive",
                'address': f"12/A Performance Drive, {city} Sector 4",
                'rating': 4.9,
                'reviews': 1250,
                'is_bestest': True,
                'type': 'Premium Service Center',
                'source': 'simulated',
                'directions_url': "https://www.google.com/maps/dir/?api=1&destination=20.5937,78.9629"
            },
            {
                'name': f"{city} Rapid Oil Change",
                'address': f"88 Speed Way, Near {city} Mall",
                'rating': 4.7,
                'reviews': 840,
                'is_bestest': False,
                'type': 'Quick Service',
                'source': 'simulated',
                'directions_url': "#"
            }
        ]
