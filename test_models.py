import joblib
import numpy as np
import pandas as pd
import os

print("Testing ML Models...")
print()

# Load the model package
model_path = 'models/carbon_model_laptop.pkl'
if os.path.exists(model_path):
    print(f"1. Loading Carbon Model from {model_path}...")
    try:
        model_package = joblib.load(model_path)
        
        # Check what's in the package
        print(f"   Package contains: {list(model_package.keys())}")
        
        # Get the model
        if isinstance(model_package, dict):
            if 'model' in model_package:
                model = model_package['model']
                print(f"   Model type: {type(model).__name__}")
            else:
                model = model_package
                print(f"   Model type: {type(model).__name__}")
        else:
            model = model_package
            print(f"   Model type: {type(model).__name__}")
        
        # Get the number of features expected
        if hasattr(model, 'n_features_in_'):
            n_features = model.n_features_in_
            print(f"   Model expects {n_features} features")
            
            # Create a test input with the right number of features
            # Using zeros for all features except the first few that we know
            test_input = np.zeros((1, n_features))
            
            # Set some realistic values for key features (based on your feature list)
            # These indices are approximate - adjust based on your feature list
            test_input[0, 0] = 1   # vehicle_type_encoded (petrol)
            test_input[0, 1] = 500 # vehicle_km
            test_input[0, 2] = np.log1p(500) # vehicle_km_log
            test_input[0, 3] = 1   # transport_private
            test_input[0, 5] = 1   # flight_freq_score (frequently)
            test_input[0, 11] = 2.5 # diet_carbon_factor (non-veg)
            test_input[0, 12] = 200 # grocery_bill
            
            prediction = model.predict(test_input)
            print(f"\n   Test prediction: {prediction[0]:.2f} kg CO2e")
            print("   ✓ Carbon Model working!")
            
            # Print feature names if available
            if 'features' in model_package:
                print(f"\n   Top 5 features used:")
                features = model_package['features']
                if hasattr(model, 'feature_importances_'):
                    importances = model.feature_importances_
                    top_indices = np.argsort(importances)[-5:][::-1]
                    for i, idx in enumerate(top_indices[:5]):
                        print(f"     {i+1}. {features[idx]}: {importances[idx]:.4f}")
        else:
            print("   Could not determine number of features")
            
    except Exception as e:
        print(f"   ✗ Error loading carbon model: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"1. Model file not found at {model_path}")

print("\n2. Creating ESG Model...")
# Create a simple ESG model for testing
try:
    from sklearn.tree import DecisionTreeClassifier
    
    # Create synthetic ESG data
    np.random.seed(42)
    X_esg = np.random.rand(100, 8)
    y_esg = np.random.choice(['Low', 'Medium', 'High'], 100, p=[0.3, 0.4, 0.3])
    
    esg_model = DecisionTreeClassifier(max_depth=5, random_state=42)
    esg_model.fit(X_esg, y_esg)
    
    # Save it
    joblib.dump(esg_model, 'models/esg_model.pkl')
    print("   ✓ Created and saved esg_model.pkl")
    
    # Test it
    test_esg = np.random.rand(1, 8)
    esg_risk = esg_model.predict(test_esg)
    print(f"   Test ESG Risk prediction: {esg_risk[0]}")
    
except Exception as e:
    print(f"   ✗ Error creating ESG model: {e}")

print("\n✓ Test complete!")