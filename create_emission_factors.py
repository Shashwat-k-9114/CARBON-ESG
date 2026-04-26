import joblib
import os

print("Creating scientifically calibrated emission factors...")

# Annual emission factors (kg CO2 per year unless stated)

emission_factors = {

    # kg CO2 per kWh
    'electricity': {
        'USA': 0.4,
        'UK': 0.18,
        'Canada': 0.12,
        'Australia': 0.5,
        'Germany': 0.3,
        'France': 0.05,
        'India': 0.7,
        'China': 0.6,
        'Japan': 0.4,
        'Brazil': 0.08,
        'South Africa': 0.8,
        'Other': 0.5
    },

    # kg CO2 per km
    'vehicle': {
        'petrol': 0.18,
        'diesel': 0.21,
        'none': 0
    },

    # Approximate annual emissions from flights
    'flights': {
        'none': 0,
        'short': 300,     # 1–2 short trips per year
        'medium': 900,    # few regional flights
        'long': 2000      # intercontinental
    },

    # Annual diet-based emissions (scientifically realistic range)
    'diet': {
        'veg': 1800,
        'mixed': 2500,
        'non-veg': 3200
    },

    # Embedded consumption emissions per year
    'shopping': {
        'low': 800,
        'medium': 1400,
        'high': 2200
    },

    # Recycling impact per year
    'recycling': {
        'yes': -300,
        'no': 0
    }
}

os.makedirs('models', exist_ok=True)
joblib.dump(emission_factors, 'models/emission_factors.pkl')

print("✓ Calibrated emission factors saved to models/emission_factors.pkl")