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
        Currently defaults to a simulated response, but can be configured
        to use real providers like RapidAPI or API Setu.
        """
        api_key = getattr(settings, 'VEHICLE_API_KEY', None)
        
        # If no API key is configured, we can return None or use dummy data logic
        if not api_key:
            return None

        # Example: RapidAPI Vahan Provider Integration
        # url = "https://vahan-api.p.rapidapi.com/vahan"
        # headers = {
        #     "X-RapidAPI-Key": api_key,
        #     "X-RapidAPI-Host": "vahan-api.p.rapidapi.com"
        # }
        # response = requests.get(url, headers=headers, params={"plate": license_plate})
        # if response.status_code == 200:
        #     return response.json()
        
        return None

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
