# OilRec: Premium Vehicle Lubrication Management System

## 🚀 Overview
OilRec is a sophisticated, AI-driven platform designed to simplify vehicle maintenance for owners. It provides precise oil recommendations based on vehicle specifications and driving habits, integrates a full e-commerce experience for purchasing lubricants, and offers a cinematic "Garage" dashboard to track vehicle health.

---

## 🛠️ Technology Stack
- **Backend Framework**: [Django 5.2.6](https://www.djangoproject.com/)
- **Frontend**: Vanilla HTML5, CSS3 (Modern cinematic UI), JavaScript (including Three.js for 3D elements)
- **Database**: SQLite (Development) / PostgreSQL (Production)
- **AI/ML Engine**: Scikit-learn, Pandas, NumPy (Hybrid recommendation logic)
- **Payments**: Razorpay Integration
- **Vehicle Data**: Vahan API via RapidAPI
- **Authentication**: Django-Allauth (Google OAuth & Email-based login)

---

## 📂 Project Structure
```text
OILREC/
├── core/               # Project-level configuration (settings, urls, wsgi)
├── oil_logic/          # Main Application logic
│   ├── models.py       # Database schemas (Oil, Vehicle, Maintenance, etc.)
│   ├── views.py        # Controller logic and API endpoints
│   ├── ai_engine.py    # Hybrid AI Recommendation logic
│   ├── services.py     # External API integrations (Vahan, AI Chat)
│   ├── templates/      # HTML templates (Cinematic UI)
│   └── static/         # App-specific assets
├── ml_models/          # Trained ML model files and training datasets
├── static/             # Global static files (Global CSS, Design System)
├── templates/          # Base templates and shared components
├── manage.py           # Django management script
└── requirements.txt    # Project dependencies
```

---

## ✨ Key Features

### 1. Hybrid AI Recommendation Engine
Uses a mixture of hard-coded manufacturer rules and machine learning to suggest the perfect oil.
- **Inputs**: Brand, Model, Year, Odometer, Driving Conditions, Atmosphere.
- **Outputs**: Primary, Premium, and Economy oil options.
- **Logic Location**: `oil_logic/ai_engine.py` and `oil_logic/views.py` (Refined recommendations).

### 2. The Digital Garage
A visual dashboard for managing personal vehicles.
- **License Plate Lookup**: Instantly add vehicles using their plate number (Vahan API).
- **Oil Life Tracker**: Real-time calculation of remaining oil life based on usage.
- **Service Records**: Maintain a digital history of all past maintenance.

### 3. Smart Shop & Payments
- **Dynamic Pricing**: Prices adjust based on selected volume (1L, 4L, 5L).
- **Razorpay Integration**: Secure payment gateway for seamless transactions.
- **Order Tracking**: Detailed purchase history and automated email confirmations.

### 4. OilBot (AI Assistant)
An interactive chat interface that provides maintenance advice and answers technical lubrication questions.

---

## 🔧 How to Add New Features

### Adding a New Model (Data Structure)
1. Open `oil_logic/models.py`.
2. Define your class (e.g., `class Feedback(models.Model):`).
3. Run `python manage.py makemigrations` and `python manage.py migrate`.

### Adding a New Page
1. **Template**: Create a new `.html` file in `oil_logic/templates/oil_logic/`.
2. **View**: Add a function in `oil_logic/views.py` to render the template.
3. **URL**: Register the path in `oil_logic/urls.py`.

### Improving the AI Recommendation
- Modify the `predict` method in `oil_logic/ai_engine.py`.
- Add new training data to `ml_models/` and retrain using the provided scripts (if applicable).

### Adding External APIs
- Create a new service in `oil_logic/services.py` to handle the API calls (following the pattern of `VehicleLookupService`).

---

## 🚢 Deployment
The project is configured for easy deployment on **Render** or **Heroku**:
- `Procfile`: Defines the web process.
- `build.sh`: Script to install dependencies and run migrations.
- `runtime.txt`: Specifies the Python version.
- `whitenoise`: Handles static file serving in production.

---

## 🔒 Environment Variables
Ensure the following are set in your `.env` file:
- `SECRET_KEY`: Django security key.
- `DEBUG`: Set to `False` in production.
- `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`: For payments.
- `VEHICLE_API_KEY`: For license plate lookup.
