import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

print("=== UI-ALIGNED MODEL TRAINING v2 (Household Integrated) ===")

# ---------------------------------------------------
# 1. EMISSION FACTORS
# ---------------------------------------------------

country_ef = {
    "India": 0.82,
    "USA": 0.4,
    "UK": 0.23,
    "Germany": 0.35,
    "Australia": 0.7,
    "Canada": 0.15,
    "Other": 0.5
}

energy_multiplier = {
    "grid": 1.0,
    "solar": 0.1,
    "mixed": 0.6
}

vehicle_ef = {
    "none": 0,
    "petrol": 0.19,
    "diesel": 0.21,
    "hybrid": 0.10,
    "electric": 0.05
}

flight_ef = {
    "none": 0,
    "domestic": 300,
    "international": 1500,
    "frequent": 3000
}

diet_ef = {
    "vegan": 1000,
    "vegetarian": 1500,
    "mixed": 2200,
    "non-veg": 2800
}

shopping_ef = {
    "low": 500,
    "medium": 1000,
    "high": 2000
}

# ---------------------------------------------------
# 2. SYNTHETIC DATA GENERATION
# ---------------------------------------------------

n = 20000
data = []

countries = list(country_ef.keys())
vehicles = list(vehicle_ef.keys())
flights = list(flight_ef.keys())
diets = list(diet_ef.keys())
shopping = list(shopping_ef.keys())

for _ in range(n):
    country = np.random.choice(countries)
    electricity = np.random.uniform(50, 800)
    household_size = np.random.randint(1, 6)
    energy = np.random.choice(list(energy_multiplier.keys()))
    vehicle = np.random.choice(vehicles)
    km = np.random.uniform(0, 1500)
    flight = np.random.choice(flights)
    diet = np.random.choice(diets)
    shop = np.random.choice(shopping)
    recycle = np.random.choice([0, 1])

    # Per capita electricity
    per_person_kwh = (electricity * 12) / household_size

    c_elec = per_person_kwh * country_ef[country] * energy_multiplier[energy]
    c_trans = km * 12 * vehicle_ef[vehicle]
    c_flight = flight_ef[flight]
    c_diet = diet_ef[diet]
    c_shop = shopping_ef[shop]
    c_recycle = -200 if recycle == 1 else 0

    total = c_elec + c_trans + c_flight + c_diet + c_shop + c_recycle

    # Add small noise (real-world uncertainty)
    total *= np.random.normal(1.0, 0.04)

    data.append([
        country, electricity, household_size,
        energy, vehicle, km, flight,
        diet, shop, recycle, total
    ])

df = pd.DataFrame(data, columns=[
    "country",
    "electricity_kwh",
    "household_size",
    "energy_source",
    "vehicle_type",
    "vehicle_km",
    "flight_type",
    "diet_type",
    "shopping_freq",
    "recycling",
    "carbon_emission"
])

# One-hot encode
df_encoded = pd.get_dummies(df.drop("carbon_emission", axis=1))
y = df["carbon_emission"]

X_train, X_test, y_train, y_test = train_test_split(
    df_encoded, y, test_size=0.1, random_state=42
)

model = GradientBoostingRegressor(
    n_estimators=150,
    learning_rate=0.07,
    max_depth=4
)

model.fit(X_train, y_train)

pred = model.predict(X_test)

print("R²:", r2_score(y_test, pred))
print("MAE:", mean_absolute_error(y_test, pred))

joblib.dump({
    "model": model,
    "features": list(df_encoded.columns)
}, "models/carbon_model_ui_aligned_v2.pkl")

print("✓ v2 Model Saved Successfully")