import pandas as pd
import numpy as np
import os
import json
import re
import ast
from sklearn.preprocessing import StandardScaler, LabelEncoder

print("=== COMPREHENSIVE DATA PROCESSING FOR HIGH ACCURACY ===")
print("Using all relevant features from your dataset...")
print()

# Create processed directory if it doesn't exist
os.makedirs('data/processed', exist_ok=True)

# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------
def parse_list_column(series):
    """Parse columns with list-like strings"""
    parsed = []
    for val in series:
        if pd.isna(val) or val == '':
            parsed.append([])
        else:
            val_str = str(val).strip()
            # Remove extra quotes and brackets
            val_str = re.sub(r'^["\']+', '', val_str)
            val_str = re.sub(r'["\']+$', '', val_str)
            
            if val_str.startswith('['):
                val_str = val_str[1:]
            if val_str.endswith(']'):
                val_str = val_str[:-1]
            
            if val_str == '':
                parsed.append([])
            else:
                try:
                    # Split by comma and clean
                    items = [item.strip().strip("'\"") for item in val_str.split(',')]
                    parsed.append([item for item in items if item])
                except:
                    parsed.append([])
    return parsed

# ------------------------------------------------------------
# 1. PROCESS CARBON EMISSION DATASET (COMPREHENSIVE)
# ------------------------------------------------------------
print("1. Processing Carbon Emission Dataset (All Features)...")

try:
    # Load the dataset
    df_carbon = pd.read_csv('data/raw/Carbon Emission.csv')
    
    print(f"   Original dataset shape: {df_carbon.shape}")
    print(f"   Original columns: {list(df_carbon.columns)}")
    
    # Display basic stats
    print(f"\n   Data Overview:")
    print(f"   - Target variable 'CarbonEmission': mean={df_carbon['CarbonEmission'].mean():.0f}, std={df_carbon['CarbonEmission'].std():.0f}")
    print(f"   - Missing values per column:")
    for col in df_carbon.columns:
        missing = df_carbon[col].isna().sum()
        if missing > 0:
            print(f"     {col}: {missing} missing ({missing/len(df_carbon)*100:.1f}%)")
    
    # Create comprehensive cleaned dataset
    cleaned_data = pd.DataFrame()
    
    # --------------------------------------------------------
    # VEHICLE & TRANSPORT FEATURES
    # --------------------------------------------------------
    print(f"\n   Processing Vehicle & Transport Features...")
    
    # 1. Vehicle type encoding
    if 'Vehicle Type' in df_carbon.columns:
        df_carbon['Vehicle Type'] = df_carbon['Vehicle Type'].fillna('none')
        vehicle_mapping = {
            'none': 0, '': 0,
            'petrol': 1, 'gasoline': 1,
            'diesel': 2,
            'hybrid': 3,
            'electric': 4, 'ev': 4,
            'lpg': 5
        }
        cleaned_data['vehicle_type_encoded'] = df_carbon['Vehicle Type'].astype(str).str.lower().map(
            lambda x: vehicle_mapping.get(x.strip(), 0)
        ).fillna(0)
    
    # 2. Vehicle distance (log transform for normalization)
    if 'Vehicle Monthly Distance Km' in df_carbon.columns:
        distance = pd.to_numeric(df_carbon['Vehicle Monthly Distance Km'], errors='coerce').fillna(0)
        cleaned_data['vehicle_km'] = distance
        cleaned_data['vehicle_km_log'] = np.log1p(distance)  # Log transform
        
    # 3. Transport mode encoding
    if 'Transport' in df_carbon.columns:
        transport_encoded = pd.get_dummies(df_carbon['Transport'].fillna('unknown'), 
                                          prefix='transport')
        cleaned_data = pd.concat([cleaned_data, transport_encoded], axis=1)
    
    # 4. Air travel frequency (weighted encoding)
    if 'Frequency of Traveling by Air' in df_carbon.columns:
        flight_weights = {
            'never': 0,
            'rarely': 1,
            'frequently': 3,
            'very frequently': 5
        }
        cleaned_data['flight_freq_score'] = df_carbon['Frequency of Traveling by Air'].astype(str).str.lower().map(
            lambda x: flight_weights.get(x.strip(), 0)
        ).fillna(0)
    
    # --------------------------------------------------------
    # ENERGY & ELECTRICITY FEATURES
    # --------------------------------------------------------
    print(f"   Processing Energy & Electricity Features...")
    
    # 1. Heating energy source (categorical to numerical)
    if 'Heating Energy Source' in df_carbon.columns:
        # Carbon intensity factors (kg CO2 per unit)
        heating_carbon_intensity = {
            'electricity': 0.5,
            'coal': 0.8,
            'natural gas': 0.4,
            'wood': 0.3,
            'none': 0,
            'nan': 0
        }
        cleaned_data['heating_carbon_factor'] = df_carbon['Heating Energy Source'].astype(str).str.lower().map(
            lambda x: heating_carbon_intensity.get(x.strip(), 0.5)
        )
    
    # 2. Electronic device usage (composite score)
    tv_hours = pd.to_numeric(df_carbon.get('How Long TV PC Daily Hour', 0), errors='coerce').fillna(3)
    internet_hours = pd.to_numeric(df_carbon.get('How Long Internet Daily Hour', 0), errors='coerce').fillna(4)
    
    cleaned_data['electronic_hours_total'] = tv_hours + internet_hours
    cleaned_data['electronic_hours_weighted'] = tv_hours * 1.5 + internet_hours * 1.0
    
    # 3. Energy efficiency (binary + categorical)
    if 'Energy efficiency' in df_carbon.columns:
        efficiency_map = {
            'no': 0,
            'sometimes': 0.5,
            'yes': 1
        }
        cleaned_data['energy_efficiency_score'] = df_carbon['Energy efficiency'].astype(str).str.lower().map(
            lambda x: efficiency_map.get(x.strip(), 0)
        ).fillna(0)
    
    # --------------------------------------------------------
    # LIFESTYLE & CONSUMPTION FEATURES
    # --------------------------------------------------------
    print(f"   Processing Lifestyle & Consumption Features...")
    
    # 1. Diet (carbon intensity)
    if 'Diet' in df_carbon.columns:
        diet_carbon = {
            'vegan': 1.0,
            'vegetarian': 1.5,
            'pescatarian': 2.0,
            'omnivore': 2.5
        }
        cleaned_data['diet_carbon_factor'] = df_carbon['Diet'].astype(str).str.lower().map(
            lambda x: diet_carbon.get(x.strip(), 2.5)
        ).fillna(2.5)
    
    # 2. Monthly grocery bill (log transform)
    if 'Monthly Grocery Bill' in df_carbon.columns:
        grocery = pd.to_numeric(df_carbon['Monthly Grocery Bill'], errors='coerce').fillna(150)
        cleaned_data['grocery_bill'] = grocery
        cleaned_data['grocery_bill_log'] = np.log1p(grocery)
    
    # 3. New clothes monthly (consumption indicator)
    if 'How Many New Clothes Monthly' in df_carbon.columns:
        clothes = pd.to_numeric(df_carbon['How Many New Clothes Monthly'], errors='coerce').fillna(5)
        cleaned_data['new_clothes_monthly'] = clothes
        cleaned_data['clothes_consumption_score'] = pd.cut(clothes, 
                                                         bins=[0, 5, 10, 20, 100],
                                                         labels=[1, 2, 3, 4]).astype(float)
    
    # 4. Shower frequency (water/energy use)
    if 'How Often Shower' in df_carbon.columns:
        shower_map = {
            'less frequently': 1,
            'daily': 2,
            'more frequently': 3,
            'twice a day': 4
        }
        cleaned_data['shower_freq_score'] = df_carbon['How Often Shower'].astype(str).str.lower().map(
            lambda x: shower_map.get(x.strip(), 2)
        ).fillna(2)
    
    # --------------------------------------------------------
    # WASTE & RECYCLING FEATURES
    # --------------------------------------------------------
    print(f"   Processing Waste & Recycling Features...")
    
    # 1. Recycling (parse list column)
    if 'Recycling' in df_carbon.columns:
        recycling_lists = parse_list_column(df_carbon['Recycling'])
        # Count different recycling types
        recycling_counts = [len(items) for items in recycling_lists]
        cleaned_data['recycling_types_count'] = recycling_counts
        
        # Binary: recycles anything
        cleaned_data['recycles_any'] = (np.array(recycling_counts) > 0).astype(int)
        
        # Specific recycling types
        recycling_types = ['Paper', 'Plastic', 'Glass', 'Metal']
        for r_type in recycling_types:
            cleaned_data[f'recycles_{r_type.lower()}'] = [
                1 if r_type in items else 0 
                for items in recycling_lists
            ]
    
    # 2. Waste generation
    if 'Waste Bag Size' in df_carbon.columns and 'Waste Bag Weekly Count' in df_carbon.columns:
        size_map = {'small': 5, 'medium': 10, 'large': 20, 'extra large': 30}
        bag_size = df_carbon['Waste Bag Size'].astype(str).str.lower().map(
            lambda x: size_map.get(x.strip(), 10)
        ).fillna(10)
        
        bag_count = pd.to_numeric(df_carbon['Waste Bag Weekly Count'], errors='coerce').fillna(2)
        
        cleaned_data['weekly_waste_volume'] = bag_size * bag_count
        cleaned_data['monthly_waste_score'] = cleaned_data['weekly_waste_volume'] * 4  # Approx monthly
    
    # --------------------------------------------------------
    # COOKING & DEMOGRAPHIC FEATURES
    # --------------------------------------------------------
    print(f"   Processing Cooking & Demographic Features...")
    
    # 1. Cooking appliances (energy intensive?)
    if 'Cooking_With' in df_carbon.columns:
        cooking_lists = parse_list_column(df_carbon['Cooking_With'])
        # Energy intensive appliances
        energy_intensive_appliances = ['Oven', 'Grill', 'Airfryer']
        
        cleaned_data['cooking_appliance_count'] = [len(items) for items in cooking_lists]
        cleaned_data['energy_intensive_appliances'] = [
            sum(1 for item in items if item in energy_intensive_appliances)
            for items in cooking_lists
        ]
    
    # 2. Social activity (proxy for travel/consumption)
    if 'Social Activity' in df_carbon.columns:
        social_map = {
            'never': 1,
            'sometimes': 2,
            'often': 3
        }
        cleaned_data['social_activity_score'] = df_carbon['Social Activity'].astype(str).str.lower().map(
            lambda x: social_map.get(x.strip(), 2)
        ).fillna(2)
    
    # 3. Body Type & Sex (demographic factors)
    if 'Body Type' in df_carbon.columns:
        body_dummies = pd.get_dummies(df_carbon['Body Type'].fillna('unknown'), 
                                     prefix='body_type')
        cleaned_data = pd.concat([cleaned_data, body_dummies], axis=1)
    
    if 'Sex' in df_carbon.columns:
        cleaned_data['is_male'] = (df_carbon['Sex'].str.lower() == 'male').astype(int)
        cleaned_data['is_female'] = (df_carbon['Sex'].str.lower() == 'female').astype(int)
    
    # --------------------------------------------------------
    # TARGET VARIABLE
    # --------------------------------------------------------
    # Keep original CarbonEmission as target
    if 'CarbonEmission' in df_carbon.columns:
        cleaned_data['carbon_emission'] = pd.to_numeric(
            df_carbon['CarbonEmission'],
            errors='coerce'
        )
        
        # Remove extreme outliers (keep 99% of data)
        lower = cleaned_data['carbon_emission'].quantile(0.005)
        upper = cleaned_data['carbon_emission'].quantile(0.995)
        initial_count = len(cleaned_data)
        cleaned_data = cleaned_data[
            (cleaned_data['carbon_emission'] >= lower) & 
            (cleaned_data['carbon_emission'] <= upper)
        ]
        removed = initial_count - len(cleaned_data)
        print(f"   Removed {removed} extreme outliers ({removed/initial_count*100:.1f}%)")
        
        print(f"\n   Target Statistics:")
        print(f"   - Mean: {cleaned_data['carbon_emission'].mean():.0f}")
        print(f"   - Std: {cleaned_data['carbon_emission'].std():.0f}")
        print(f"   - Min: {cleaned_data['carbon_emission'].min():.0f}")
        print(f"   - Max: {cleaned_data['carbon_emission'].max():.0f}")
    
    # --------------------------------------------------------
    # FEATURE ENGINEERING: INTERACTION TERMS
    # --------------------------------------------------------
    print(f"\n   Creating Interaction Features...")
    
    # Interaction: Vehicle distance * vehicle type
    if 'vehicle_km' in cleaned_data.columns and 'vehicle_type_encoded' in cleaned_data.columns:
        cleaned_data['vehicle_km_type_interaction'] = cleaned_data['vehicle_km'] * cleaned_data['vehicle_type_encoded']
    
    # Interaction: Diet * Grocery bill
    if 'diet_carbon_factor' in cleaned_data.columns and 'grocery_bill' in cleaned_data.columns:
        cleaned_data['diet_grocery_interaction'] = cleaned_data['diet_carbon_factor'] * cleaned_data['grocery_bill'] / 100
    
    # Composite lifestyle score
    lifestyle_components = []
    for col in ['social_activity_score', 'shower_freq_score', 'new_clothes_monthly']:
        if col in cleaned_data.columns:
            lifestyle_components.append(cleaned_data[col])
    
    if lifestyle_components:
        cleaned_data['lifestyle_composite'] = pd.concat(lifestyle_components, axis=1).mean(axis=1)
    
    # --------------------------------------------------------
    # FINAL CLEANUP
    # --------------------------------------------------------
    # Fill any remaining NaN values
    cleaned_data = cleaned_data.fillna(0)
    
    # Remove duplicate columns if any
    cleaned_data = cleaned_data.loc[:, ~cleaned_data.columns.duplicated()]
    
    print(f"\n   Final Dataset Shape: {cleaned_data.shape}")
    print(f"   Number of features: {len(cleaned_data.columns) - 1}")  # minus target
    print(f"   Feature columns: {[col for col in cleaned_data.columns if col != 'carbon_emission']}")
    
    # Save processed data
    cleaned_data.to_csv('data/processed/carbon_training_data_comprehensive.csv', index=False)
    print(f"\n   ✓ Saved comprehensive training data with {len(cleaned_data)} rows")
    
    # Display feature correlation with target
    if 'carbon_emission' in cleaned_data.columns:
        correlations = cleaned_data.corr()['carbon_emission'].abs().sort_values(ascending=False)
        print(f"\n   Top 10 features correlated with carbon emission:")
        for feature, corr in correlations.iloc[1:11].items():  # Skip target itself
            print(f"     {feature}: {corr:.3f}")
    
except Exception as e:
    print(f"   ✗ Error processing dataset: {e}")
    import traceback
    traceback.print_exc()

# ------------------------------------------------------------
# 2. SAVE FEATURE CONFIGURATION FOR MODEL TRAINING
# ------------------------------------------------------------
print("\n2. Saving Feature Configuration...")

try:
    if 'cleaned_data' in locals():
        # Identify feature types
        numeric_features = []
        categorical_features = []
        
        for col in cleaned_data.columns:
            if col == 'carbon_emission':
                continue
            if cleaned_data[col].dtype in ['int64', 'float64']:
                if cleaned_data[col].nunique() < 10:  # Few unique values
                    categorical_features.append(col)
                else:
                    numeric_features.append(col)
        
        feature_config = {
            'all_features': [col for col in cleaned_data.columns if col != 'carbon_emission'],
            'numeric_features': numeric_features,
            'categorical_features': categorical_features,
            'target_column': 'carbon_emission'
        }
        
        import json
        with open('data/processed/feature_config.json', 'w') as f:
            json.dump(feature_config, f, indent=2)
        
        print(f"   ✓ Saved feature configuration")
        print(f"   - Numeric features: {len(numeric_features)}")
        print(f"   - Categorical features: {len(categorical_features)}")
        
except Exception as e:
    print(f"   ✗ Error saving config: {e}")

print("\n=== COMPREHENSIVE DATA PROCESSING COMPLETE ===")