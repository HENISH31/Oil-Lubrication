from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

geolocator = Nominatim(user_agent="oilrec_precision_locator")
try:
    location = geolocator.geocode("390001", timeout=10)
    if location:
        print(f"Success: {location.latitude}, {location.longitude}")
        print(f"Address: {location.address}")
    else:
        print("Failed: No location found")
except Exception as e:
    print(f"Error: {e}")
