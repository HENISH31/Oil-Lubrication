import requests
from django.conf import settings

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

    @staticmethod
    def get_mock_data(license_plate):
        """
        Manual override for specific plates if needed (can also use the Registry model).
        """
        # This mirrors our local registry logic
        return None

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
