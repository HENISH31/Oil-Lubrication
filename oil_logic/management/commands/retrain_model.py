import os
import joblib
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from oil_logic.models import Oil, VehicleQuery, RecommendationFeedback
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler

class Command(BaseCommand):
    help = 'Retrains the AI Oil Recommendation model'

    def add_arguments(self, parser):
        parser.add_argument('--initial', action='store_true', help='Seed with synthetic data for first training')

    def handle(self, *args, **options):
        self.stdout.write("Starting model retraining...")

        if options['initial']:
            self.stdout.write("Seeding synthetic data based on expert rules...")
            self._seed_synthetic_data()

        # Load data from database
        data = self._get_training_data()
        if data.empty:
            self.stdout.write(self.style.ERROR("No training data found. Use --initial to seed."))
            return

        # Prepare features and target
        X = data.drop(columns=['target_oil_id'])
        y = data['target_oil_id']

        # Encoders
        encoders = {}
        categorical_cols = ['brand', 'model', 'engine_type', 'driving_condition']
        for col in categorical_cols:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            encoders[col] = le

        # Scaler
        scaler = StandardScaler()
        numeric_cols = ['year', 'displacement_cc', 'odometer_km']
        X[numeric_cols] = scaler.fit_transform(X[numeric_cols])

        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)

        # Save model and artifacts
        model_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        joblib.dump(model, os.path.join(model_dir, 'oil_recommender.joblib'))
        joblib.dump(scaler, os.path.join(model_dir, 'scaler.joblib'))
        joblib.dump(encoders, os.path.join(model_dir, 'encoders.joblib'))

        self.stdout.write(self.style.SUCCESS("Successfully retrained model and saved to ml_models/"))

    def _get_training_data(self):
        # Fetch from RecommendationFeedback
        feedbacks = RecommendationFeedback.objects.filter(is_helpful=True).select_related('query')
        if not feedbacks.exists():
            return pd.DataFrame()

        rows = []
        for fb in feedbacks:
            q = fb.query
            rows.append({
                'brand': q.brand,
                'model': q.model,
                'year': q.year,
                'engine_type': q.engine_type,
                'displacement_cc': q.displacement_cc,
                'odometer_km': q.odometer_km,
                'driving_condition': q.driving_condition,
                'target_oil_id': fb.selected_oil.id if fb.selected_oil else fb.recommended_oil.id
            })
        return pd.DataFrame(rows)

    def _seed_synthetic_data(self):
        """
        Creates synthetic feedback entries based on existing rule-based logic
        to provide a starting point for the ML model.
        """
        from oil_logic.models import Vehicle
        
        vehicles = Vehicle.objects.all()
        oils = Oil.objects.all()
        
        if not vehicles.exists() or not oils.exists():
            self.stdout.write("Not enough vehicles or oils to seed.")
            return

        for vehicle in vehicles:
            # Create a query
            query = VehicleQuery.objects.create(
                brand=vehicle.brand,
                model=vehicle.model,
                year=vehicle.year,
                engine_type=vehicle.engine_type,
                displacement_cc=vehicle.displacement_cc,
                odometer_km=10000,
                driving_condition='Mixed'
            )
            
            # Use the vehicle's recommended oil as the gold standard for initial training
            if vehicle.recommended_oil:
                RecommendationFeedback.objects.create(
                    query=query,
                    recommended_oil=vehicle.recommended_oil,
                    selected_oil=vehicle.recommended_oil,
                    is_helpful=True,
                    rating=5
                )
        self.stdout.write(f"Created {vehicles.count()} synthetic training samples.")
