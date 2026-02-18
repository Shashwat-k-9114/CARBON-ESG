import joblib
import os

print("Creating emission factors...")

# Create default emission factors
emission_factors = {
    'electricity': {
        'USA': 0.4,
        'UK': 0.177,
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
    'vehicle': {
        'petrol': 0.18,
        'diesel': 0.21,
        'none': 0
    },
    'flights': {
        'none': 0,
        'short': 500,
        'medium': 1500,
        'long': 4000
    },
    'diet': {
        'veg': 400,
        'mixed': 600,
        'non-veg': 800
    },
    'shopping': {
        'low': 100,
        'medium': 150,
        'high': 250
    },
    'recycling': {
        'yes': -100,
        'no': 0
    }
}

# Save the file
os.makedirs('models', exist_ok=True)
joblib.dump(emission_factors, 'models/emission_factors.pkl')
print("✓ Created models/emission_factors.pkl")