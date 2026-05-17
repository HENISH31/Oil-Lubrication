import os
import joblib
import pandas as pd
from django.core.management.base import BaseCommand
from django.conf import settings
from oil_logic.models import Oil, VehicleQuery, RecommendationFeedback
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, top_k_accuracy_score
import numpy as np
import json

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

        # Split data for evaluation (Use stratification to ensure all classes are in both sets)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)
        
        # Top-k accuracy (Top 3)
        try:
            top_3_acc = top_k_accuracy_score(y_test, y_proba, k=3, labels=model.classes_)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Top-3 calculation error: {e}"))
            top_3_acc = accuracy_score(y_test, y_pred)

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'top_3_accuracy': top_3_acc,
            'precision': precision_score(y_test, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_test, y_pred, average='weighted', zero_division=0),
            'f1': f1_score(y_test, y_pred, average='weighted', zero_division=0),
            'sample_size': len(data),
            'timestamp': pd.Timestamp.now().isoformat(),
            'feature_importance': dict(zip(X.columns, model.feature_importances_.tolist()))
        }

        # Save model and artifacts
        model_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        joblib.dump(model, os.path.join(model_dir, 'oil_recommender.joblib'))
        joblib.dump(scaler, os.path.join(model_dir, 'scaler.joblib'))
        joblib.dump(encoders, os.path.join(model_dir, 'encoders.joblib'))
        
        with open(os.path.join(model_dir, 'metrics.json'), 'w') as f:
            json.dump(metrics, f, indent=4)

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

        import random
        driving_conditions = ['City', 'Highway', 'Off-road', 'Mixed']
        mileage_ranges = [5000, 25000, 75000, 125000, 175000]

        for vehicle in vehicles:
            # Create multiple variants per vehicle to show how conditions change the recommendation
            for _ in range(2):
                cond = random.choice(driving_conditions)
                odo = random.choice(mileage_ranges)
                
                # Create a query
                query = VehicleQuery.objects.create(
                    brand=vehicle.brand,
                    model=vehicle.model,
                    year=vehicle.year,
                    engine_type=vehicle.engine_type,
                    displacement_cc=vehicle.displacement_cc,
                    odometer_km=odo,
                    driving_condition=cond
                )
                
                # Use a slightly shifted logic for synthetic ground truth if needed, 
                # or just use the recommended oil as base.
                RecommendationFeedback.objects.create(
                    query=query,
                    recommended_oil=vehicle.recommended_oil,
                    selected_oil=vehicle.recommended_oil,
                    is_helpful=True,
                    rating=5
                )
        self.stdout.write(f"Created {vehicles.count() * 2} synthetic training samples with variance.")
