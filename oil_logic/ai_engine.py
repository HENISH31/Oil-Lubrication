import os
import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from .models import Oil, VehicleQuery, RecommendationFeedback
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler

class AIOilRecommender:
    def __init__(self):
        self.model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'oil_recommender.joblib')
        self.scaler_path = os.path.join(settings.BASE_DIR, 'ml_models', 'scaler.joblib')
        self.encoder_path = os.path.join(settings.BASE_DIR, 'ml_models', 'encoders.joblib')
        self.model = None
        self.scaler = None
        self.encoders = {}
        self._load_model()

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.encoders = joblib.load(self.encoder_path)
            except Exception as e:
                print(f"Error loading model: {e}")

    def is_available(self):
        return self.model is not None

    def preprocess_query(self, query_data):
        """
        Convert raw query data into featured vector.
        """
        # Expected features: brand, model, year, engine_type, displacement_cc, odometer_km, driving_condition
        df = pd.DataFrame([query_data])
        
        # Enforce column order to match training data
        cols = ['brand', 'model', 'year', 'engine_type', 'displacement_cc', 'odometer_km', 'driving_condition']
        
        # Ensure all columns exist, fill missing with defaults
        for col in cols:
            if col not in df.columns:
                df[col] = 0 if col in ['year', 'displacement_cc', 'odometer_km'] else 'Unknown'
        df = df[cols]
        
        # Categorical encoding
        for col, le in self.encoders.items():
            if col in df.columns:
                try:
                    df[col] = le.transform(df[col].astype(str))
                except:
                    df[col] = 0 # Fallback for unknown
        
        # Scaling
        numeric_cols = ['year', 'displacement_cc', 'odometer_km']
        df[numeric_cols] = self.scaler.transform(df[numeric_cols])
        
        return df

    def predict(self, query_data):
        """
        Predict the best oil ID.
        """
        if not self.is_available():
            return None, 0.0
            
        features = self.preprocess_query(query_data)
        probs = self.model.predict_proba(features)[0]
        max_prob_idx = np.argmax(probs)
        prediction = self.model.classes_[max_prob_idx]
        confidence = probs[max_prob_idx]
        
        return prediction, confidence

    def predict_with_alternatives(self, query_data, top_n=3):
        if not self.is_available():
            return []
            
        features = self.preprocess_query(query_data)
        probs = self.model.predict_proba(features)[0]
        
        # Get top N indices
        top_indices = np.argsort(probs)[-top_n:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'oil_id': self.model.classes_[idx],
                'confidence': probs[idx]
            })
        return results

    def get_explanation(self, query_data, oil):
        """
        Generate a human-readable explanation for the recommendation.
        """
        explanation = f"Based on your {query_data.get('brand')} {query_data.get('model')}'s "
        explanation += f"mileage of {query_data.get('odometer_km')} KM and {query_data.get('driving_condition')} driving conditions, "
        explanation += f"we recommend {oil.brand} {oil.viscosity}. "
        
        if oil.oil_type == 'Synthetic':
            explanation += "The full synthetic formula provides superior protection for high-performance engines and longer drain intervals."
        elif '100k' in str(query_data.get('odometer_km', '')):
            explanation += "This higher viscosity oil helps protect older engine components and reduce consumption."
        else:
            explanation += f"This {oil.oil_type} oil meets the API {oil.api_rating} standards required for your vehicle."
            
        return explanation
