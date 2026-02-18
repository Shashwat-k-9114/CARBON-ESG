import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import RobustScaler
import joblib
import json
import warnings
warnings.filterwarnings('ignore')

print("=== LIGHTWEIGHT MODEL TRAINING ===")
print()

# ------------------------------------------------------------
# 1. LOAD DATA (with memory optimization)
# ------------------------------------------------------------
print("1. Loading Data...")

try:
    # Load data with lower precision to save memory
    df = pd.read_csv('data/processed/carbon_training_data_comprehensive.csv')
    
    # Load feature configuration
    with open('data/processed/feature_config.json', 'r') as f:
        feature_config = json.load(f)
    
    # Use float32 to save memory
    X = df[feature_config['all_features']].astype(np.float32)
    y = df[feature_config['target_column']].astype(np.float32)
    
    print(f"   Dataset: {X.shape[0]} samples, {X.shape[1]} features")
    
    # --------------------------------------------------------
    # 2. QUICK FEATURE SELECTION
    # --------------------------------------------------------
    print("\n2. Quick Feature Selection...")
    
    # Simple correlation-based selection
    correlations = X.corrwith(y).abs()
    top_features = correlations.nlargest(50).index.tolist()  # Keep only top 50
    
    if len(top_features) < 10:
        top_features = X.columns[:50].tolist()  # Fallback
        
    X = X[top_features]
    print(f"   Selected top {len(top_features)} features")
    
    # --------------------------------------------------------
    # 3. DATA SPLITTING (smaller test set)
    # --------------------------------------------------------
    print("\n3. Data Splitting...")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.10, random_state=42  # Smaller test set
    )
    
    # Simple scaling
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"   Training: {X_train.shape[0]}, Test: {X_test.shape[0]}")
    
    # --------------------------------------------------------
    # 4. LIGHTWEIGHT MODEL TRAINING
    # --------------------------------------------------------
    print("\n4. Training Lightweight Models...")
    
    # Model 1: Simple Random Forest (NO GridSearch)
    print("   Training Random Forest (light)...")
    rf = RandomForestRegressor(
        n_estimators=50,  # Reduced from 100-300
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features='sqrt',
        random_state=42,
        n_jobs=2,  # Use only 2 cores, not all!
        verbose=0
    )
    rf.fit(X_train_scaled, y_train)
    
    # Model 2: Gradient Boosting (simplified)
    print("   Training Gradient Boosting...")
    gb = GradientBoostingRegressor(
        n_estimators=50,
        learning_rate=0.1,
        max_depth=5,
        subsample=0.8,
        random_state=42,
        verbose=0
    )
    gb.fit(X_train_scaled, y_train)
    
    # Model 3: Simple Linear Model
    print("   Training Ridge Regression...")
    ridge = Ridge(alpha=1.0)
    ridge.fit(X_train_scaled, y_train)
    
    # --------------------------------------------------------
    # 5. SIMPLE ENSEMBLE (average predictions)
    # --------------------------------------------------------
    print("\n5. Creating Simple Ensemble...")
    
    def ensemble_predict(X):
        rf_pred = rf.predict(X) * 0.4
        gb_pred = gb.predict(X) * 0.4
        ridge_pred = ridge.predict(X) * 0.2
        return rf_pred + gb_pred + ridge_pred
    
    # --------------------------------------------------------
    # 6. EVALUATION
    # --------------------------------------------------------
    print("\n6. Model Evaluation...")
    
    models = {
        'Random Forest': rf,
        'Gradient Boosting': gb,
        'Ridge Regression': ridge,
        'Ensemble (weighted)': 'ensemble'
    }
    
    best_model = None
    best_r2 = -np.inf
    
    print("\n   Model Performance:")
    print("   " + "="*50)
    print(f"   {'Model':<20} {'R² Score':<10} {'MAE':<10}")
    print("   " + "-"*50)
    
    for name, model in models.items():
        if name == 'Ensemble (weighted)':
            y_pred = ensemble_predict(X_test_scaled)
        else:
            y_pred = model.predict(X_test_scaled)
        
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        
        print(f"   {name:<20} {r2:<10.4f} {mae:<10.2f}")
        
        if r2 > best_r2:
            best_r2 = r2
            if name == 'Ensemble (weighted)':
                best_model = {'type': 'ensemble', 'rf': rf, 'gb': gb, 'ridge': ridge}
            else:
                best_model = model
            best_model_name = name
    
    print("   " + "="*50)
    
    # --------------------------------------------------------
    # 7. SAVE BEST MODEL
    # --------------------------------------------------------
    print(f"\n7. Saving Best Model ({best_model_name})...")
    
    model_package = {
        'model_type': best_model_name,
        'model': best_model,
        'scaler': scaler,
        'features': top_features,
        'ensemble_weights': [0.4, 0.4, 0.2] if best_model_name == 'Ensemble (weighted)' else None
    }
    
    joblib.dump(model_package, 'models/carbon_model_laptop.pkl', compress=3)  # High compression
    
    print(f"   ✓ Model saved with R² = {best_r2:.4f} ({best_r2*100:.1f}%)")
    
    # Quick feature importance
    if hasattr(best_model, 'feature_importances_'):
        importance = best_model.feature_importances_
        top_5_idx = np.argsort(importance)[-5:][::-1]
        print(f"\n   Top 5 Features:")
        for idx in top_5_idx:
            print(f"     {top_features[idx]}: {importance[idx]:.4f}")
    
    # Performance report
    performance_report = {
        'best_model': best_model_name,
        'r2_score': float(best_r2),
        'features_used': len(top_features),
        'samples_trained': len(X_train)
    }
    
    with open('models/performance_report_laptop.json', 'w') as f:
        json.dump(performance_report, f, indent=2)
    
    print(f"\n   ✓ Lightweight training complete!")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== LAPTOP-FRIENDLY TRAINING COMPLETE ===")