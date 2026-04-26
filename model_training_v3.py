"""
Carbon Footprint ML Model - v5 (Max Accuracy)
- Includes 6 advanced fields for granular emission estimation
- XGBoost with hyperparameter tuning
"""
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

# ---------------------------------------------------
# Emission factors (extended)
# ---------------------------------------------------
country_ef = {
    "India": 0.67, "USA": 0.38, "UK": 0.23,
    "Germany": 0.35, "Australia": 0.70, "Canada": 0.15, "Other": 0.50
}
energy_multiplier = {"grid": 1.0, "solar": 0.1, "mixed": 0.6}
vehicle_ef = {"none": 0, "petrol": 0.19, "diesel": 0.21, "hybrid": 0.10, "electric": 0.05}
flight_emission_map = {0: 0, 1: 300, 2: 1500, 3: 3000}
diet_ef = {"veg": 1000, "mixed": 2200, "non-veg": 2800}
shopping_ef = {"low": 500, "medium": 1000, "high": 2000}
recycle_effect = {"yes": -200, "no": 0}

# New emission factors
home_type_mult = {"apartment": 0.8, "house": 1.0, "shared": 0.6}
heating_ef = {"electric": 0.4, "gas": 0.2, "oil": 0.3, "heatpump": 0.1, "none": 0}  # kg CO2/kWh equivalent
meat_emission_per_serving = 7.0  # kg CO2e per meat-containing meal (average)
food_waste_mult = {"rarely": 1.0, "sometimes": 1.1, "often": 1.2}

# ---------------------------------------------------
# Synthetic data generation (70k samples)
# ---------------------------------------------------
np.random.seed(42)
n = 50000

countries = list(country_ef.keys())
energy_sources = list(energy_multiplier.keys())
vehicles = list(vehicle_ef.keys())
flight_cats = [0, 1, 2, 3]
public_transport_opts = ["never", "sometimes", "often", "always"]
diets = list(diet_ef.keys())
shopping_levels = list(shopping_ef.keys())
recycle_opts = ["yes", "no"]

home_types = list(home_type_mult.keys())
heating_sources = list(heating_ef.keys())
food_waste_opts = list(food_waste_mult.keys())

data = []
for _ in range(n):
    country = np.random.choice(countries)
    household_size = np.random.randint(1, 6)
    electricity = np.random.uniform(50, 800)
    energy = np.random.choice(energy_sources)
    vehicle = np.random.choice(vehicles)
    km = 0.0 if vehicle == "none" else np.random.uniform(0, 1500)
    flights = np.random.choice(flight_cats, p=[0.4, 0.3, 0.2, 0.1])
    public_trans = np.random.choice(public_transport_opts)
    diet = np.random.choice(diets)
    shop = np.random.choice(shopping_levels)
    recycle = np.random.choice(recycle_opts)

    # New fields
    home_type = np.random.choice(home_types, p=[0.3, 0.5, 0.2])
    heating = np.random.choice(heating_sources, p=[0.4, 0.3, 0.1, 0.1, 0.1])
    meat_freq = np.random.poisson(lam=3 if diet=="non-veg" else 1 if diet=="mixed" else 0)
    meat_freq = min(7, max(0, meat_freq))
    food_waste = np.random.choice(food_waste_opts, p=[0.3, 0.5, 0.2])
    veh_efficiency = np.random.uniform(8, 20) if vehicle != "none" else 0  # km/L
    renewable_pct = np.random.beta(2, 5) * 100 if energy == "grid" else 0

    # ----- Rule‑based calculation with new fields -----
    # Electricity (adjusted for home type and renewable %)
    base_elec_per_capita = electricity * 12 / household_size
    home_adjusted_elec = base_elec_per_capita * home_type_mult[home_type]
    country_factor = country_ef[country]
    if energy == "grid":
        effective_ef = country_factor * (1 - renewable_pct/100) + (0.1 * renewable_pct/100)
    else:
        effective_ef = country_factor * energy_multiplier[energy]
    elec_emission = home_adjusted_elec * effective_ef

    # Heating (annual kWh equivalent based on home type)
    heating_kwh = 4000 if home_type == "house" else 2500 if home_type == "apartment" else 1500
    heating_kwh /= household_size  # per capita
    heating_emission = heating_kwh * heating_ef[heating]

    # Transport
    if vehicle != "none":
        # Use vehicle efficiency if available, else fallback
        fuel_consumption_L_per_km = 1 / veh_efficiency if veh_efficiency > 0 else 0.08
        vehicle_emission = km * 12 * fuel_consumption_L_per_km * 2.3  # 2.3 kg CO2/L petrol
    else:
        vehicle_emission = 0

    flight_emission = flight_emission_map[flights]

    # Diet (base + meat frequency adjustment)
    base_diet = diet_ef[diet]
    meat_extra = meat_freq * 52 * meat_emission_per_serving  # weekly servings * 52 weeks * 7 kg/serving
    diet_emission = base_diet + meat_extra
    diet_emission *= food_waste_mult[food_waste]

    shopping_emission = shopping_ef[shop]
    recycle_credit = recycle_effect[recycle]

    total = (elec_emission + heating_emission + vehicle_emission + flight_emission +
             diet_emission + shopping_emission + recycle_credit)
    total *= np.random.normal(1.0, 0.02)  # 2% noise

    # Store all raw and engineered features
    data.append([
        country, electricity, household_size, energy,
        vehicle, km, flights, public_trans, diet, shop, recycle,
        home_type, heating, meat_freq, food_waste, veh_efficiency, renewable_pct,
        # Engineered features (same as will be generated in calculator)
        base_elec_per_capita, home_adjusted_elec, country_factor, effective_ef,
        heating_kwh, heating_emission,
        vehicle_emission, flight_emission, diet_emission, shopping_emission, recycle_credit,
        total
    ])

columns = [
    "country", "electricity_kwh", "household_size", "energy_source",
    "vehicle_type", "vehicle_km", "flights_per_year", "public_transport",
    "diet_type", "shopping_freq", "recycling",
    "home_type", "heating_source", "meat_frequency", "food_waste",
    "vehicle_efficiency", "renewable_percent",
    "elec_per_capita_base", "elec_per_capita_home_adj", "country_ef", "effective_elec_ef",
    "heating_kwh_per_capita", "heating_emission_raw",
    "vehicle_emission_raw", "flight_emission_raw", "diet_emission_raw",
    "shopping_emission_raw", "recycle_credit", "carbon_emission"
]

df = pd.DataFrame(data, columns=columns)

# ---------------------------------------------------
# Prepare features for model
# ---------------------------------------------------
X = df.drop("carbon_emission", axis=1)
y = df["carbon_emission"]

categorical_cols = ["country", "energy_source", "vehicle_type", "public_transport",
                    "diet_type", "shopping_freq", "recycling", "home_type",
                    "heating_source", "food_waste"]
X_encoded = pd.get_dummies(X, columns=categorical_cols, drop_first=False)

X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.15, random_state=42)

# XGBoost tuning (same as before, but with more estimators)
# xgb_model = xgb.XGBRegressor(objective='reg:squarederror', random_state=42, n_jobs=1)
# param_dist = {
#     'n_estimators': [300, 500, 700],
#     'max_depth': [5, 7, 9],
#     'learning_rate': [0.01, 0.03, 0.05],
#     'subsample': [0.7, 0.8, 0.9],
#     'colsample_bytree': [0.7, 0.8, 0.9],
#     'gamma': [0, 0.1],
#     'reg_alpha': [0, 0.1, 1],
#     'reg_lambda': [1, 2]
# }
# X_tune, _, y_tune, _ = train_test_split(X_train, y_train, train_size=15000, random_state=42)
# random_search = RandomizedSearchCV(xgb_model, param_dist, n_iter=40, cv=3,
#                                    scoring='r2', n_jobs=-1, random_state=42, verbose=1)
# random_search.fit(X_tune, y_tune)
# best_model = random_search.best_estimator_
# best_model.fit(X_train, y_train)

best_model = xgb.XGBRegressor(
    objective='reg:squarederror',
    n_estimators=300,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.9,
    colsample_bytree=0.9,
    gamma=0.1,
    reg_alpha=0.1,
    reg_lambda=2,
    random_state=42,
    n_jobs=1
)
best_model.fit(X_train, y_train)



y_pred = best_model.predict(X_test)
print(f"Test R²: {r2_score(y_test, y_pred):.4f}")
print(f"Test MAE: {mean_absolute_error(y_test, y_pred):.1f} kg CO₂e")

joblib.dump({"model": best_model, "features": list(X_encoded.columns)},
            "models/carbon_model_v3.pkl")
print("Model saved: models/carbon_model_v3.pkl")