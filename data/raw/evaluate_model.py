import pandas as pd
import numpy as np
import os, sys, re
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score,
                              classification_report, confusion_matrix, accuracy_score)
from sklearn.preprocessing import RobustScaler

print("=" * 60)
print("CARBON ESG PLATFORM - FULL EVALUATION REPORT")
print("=" * 60)

# ─────────────────────────────────────────────
# AUTO-DETECT CSV PATH (works on any OS)
# ─────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
candidates = [
    os.path.join(script_dir, 'Carbon_Emission.csv'),
    os.path.join(script_dir, 'Carbon Emission.csv'),
    os.path.join(script_dir, 'data', 'raw', 'Carbon_Emission.csv'),
    os.path.join(script_dir, 'data', 'raw', 'Carbon Emission.csv'),
]
csv_path = next((p for p in candidates if os.path.exists(p)), None)
if csv_path is None:
    print("\n  ERROR: Cannot find Carbon_Emission.csv")
    print("  Put it in the same folder as this script and re-run.\n")
    sys.exit(1)

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def parse_list_col(series):
    out = []
    for v in series:
        if pd.isna(v) or str(v).strip() == '':
            out.append([])
            continue
        s = re.sub(r"^[\"']+|[\"']+$", '', str(v).strip()).strip('[]')
        try:
            items = [i.strip().strip("'\"") for i in s.split(',')]
            out.append([i for i in items if i])
        except:
            out.append([])
    return out

# ─────────────────────────────────────────────
# PART 1 – INDIVIDUAL MODEL (REGRESSION)
# ─────────────────────────────────────────────
print("\n[1/2] INDIVIDUAL CARBON FOOTPRINT MODEL")
print("-" * 60)

df = pd.read_csv(csv_path)
print(f"  Dataset    : {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"  CSV path   : {csv_path}")
print(f"  Target     : CarbonEmission  mean={df['CarbonEmission'].mean():.0f}  std={df['CarbonEmission'].std():.0f}")

# ── Feature engineering ──
feat = pd.DataFrame()

df['Vehicle Type'] = df['Vehicle Type'].fillna('none')
vmap = {'none':0,'':0,'petrol':1,'diesel':2,'hybrid':3,'electric':4,'lpg':5}
feat['vehicle_type_enc'] = df['Vehicle Type'].str.lower().map(lambda x: vmap.get(x.strip(), 0)).fillna(0)
dist = pd.to_numeric(df['Vehicle Monthly Distance Km'], errors='coerce').fillna(0)
feat['vehicle_km']     = dist
feat['vehicle_km_log'] = np.log1p(dist)

transport_dummies = pd.get_dummies(df['Transport'].fillna('unknown'), prefix='transport')
feat = pd.concat([feat, transport_dummies], axis=1)

fmap = {'never':0,'rarely':1,'frequently':3,'very frequently':5}
feat['flight_score'] = df['Frequency of Traveling by Air'].str.lower().map(lambda x: fmap.get(x.strip(), 0)).fillna(0)

heat_map = {'electricity':0.5,'coal':0.8,'natural gas':0.4,'wood':0.3,'none':0,'nan':0}
feat['heating_factor'] = df['Heating Energy Source'].str.lower().map(lambda x: heat_map.get(x.strip(), 0.5)).fillna(0.5)
tv   = pd.to_numeric(df['How Long TV PC Daily Hour'],    errors='coerce').fillna(3)
inet = pd.to_numeric(df['How Long Internet Daily Hour'], errors='coerce').fillna(4)
feat['elec_hours'] = tv + inet
eff_map = {'no':0,'sometimes':0.5,'yes':1}
feat['energy_eff'] = df['Energy efficiency'].str.lower().map(lambda x: eff_map.get(x.strip(), 0)).fillna(0)

diet_map = {'vegan':1.0,'vegetarian':1.5,'pescatarian':2.0,'omnivore':2.5}
feat['diet_factor'] = df['Diet'].str.lower().map(lambda x: diet_map.get(x.strip(), 2.5)).fillna(2.5)
grocery = pd.to_numeric(df['Monthly Grocery Bill'], errors='coerce').fillna(150)
feat['grocery']     = grocery
feat['grocery_log'] = np.log1p(grocery)
clothes = pd.to_numeric(df['How Many New Clothes Monthly'], errors='coerce').fillna(5)
feat['new_clothes'] = clothes
shower_map = {'less frequently':1,'daily':2,'more frequently':3,'twice a day':4}
feat['shower_score'] = df['How Often Shower'].str.lower().map(lambda x: shower_map.get(x.strip(), 2)).fillna(2)

rec_lists = parse_list_col(df['Recycling'])
feat['recycling_count'] = [len(x) for x in rec_lists]
feat['recycles_any']    = (feat['recycling_count'] > 0).astype(int)
size_map = {'small':5,'medium':10,'large':20,'extra large':30}
bag_size = df['Waste Bag Size'].str.lower().map(lambda x: size_map.get(x.strip(), 10)).fillna(10)
bag_cnt  = pd.to_numeric(df['Waste Bag Weekly Count'], errors='coerce').fillna(2)
feat['weekly_waste'] = bag_size * bag_cnt

social_map = {'never':1,'sometimes':2,'often':3}
feat['social_score'] = df['Social Activity'].str.lower().map(lambda x: social_map.get(x.strip(), 2)).fillna(2)
body_dummies = pd.get_dummies(df['Body Type'].fillna('unknown'), prefix='body')
feat = pd.concat([feat, body_dummies], axis=1)
feat['is_male'] = (df['Sex'].str.lower() == 'male').astype(int)

cook_lists = parse_list_col(df['Cooking_With'])
feat['cook_appliance_count'] = [len(x) for x in cook_lists]
intense = ['Oven','Grill','Airfryer']
feat['intense_appliances']   = [sum(1 for i in x if i in intense) for x in cook_lists]

feat['vehicle_km_type_ix'] = feat['vehicle_km'] * feat['vehicle_type_enc']
feat['diet_grocery_ix']    = feat['diet_factor'] * feat['grocery'] / 100

feat = feat.fillna(0)
feat = feat.loc[:, ~feat.columns.duplicated()]

y    = pd.to_numeric(df['CarbonEmission'], errors='coerce')
mask = feat.notna().all(axis=1) & y.notna()
X, y = feat[mask], y[mask]

print(f"  Feature matrix: {X.shape[0]:,} samples x {X.shape[1]} features")

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler   = RobustScaler()
Xtr_s    = scaler.fit_transform(X_train)
Xte_s    = scaler.transform(X_test)

models_reg = {
    'Random Forest'    : RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1),
    'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42),
    'Ridge Regression' : Ridge(alpha=1.0),
}

print("\n  +-------------------------+------------+------------+--------------+--------------+")
print("  | Model                   |  R2 Score  |  MAE (kg)  |  RMSE (kg)   |  MAPE (%)    |")
print("  +-------------------------+------------+------------+--------------+--------------+")

trained = {}
for name, model in models_reg.items():
    model.fit(Xtr_s, y_train)
    yp   = model.predict(Xte_s)
    r2   = r2_score(y_test, yp)
    mae  = mean_absolute_error(y_test, yp)
    rmse = np.sqrt(mean_squared_error(y_test, yp))
    mape = np.mean(np.abs((y_test - yp) / (y_test + 1e-9))) * 100
    print(f"  | {name:<23} |  {r2:>8.4f}  | {mae:>10.1f} | {rmse:>12.1f} | {mape:>12.2f} |")
    trained[name] = model

rf_m, gb_m, rg_m = trained['Random Forest'], trained['Gradient Boosting'], trained['Ridge Regression']
ens_pred = rf_m.predict(Xte_s)*0.4 + gb_m.predict(Xte_s)*0.4 + rg_m.predict(Xte_s)*0.2
print(f"  | {'Ensemble (40/40/20)':<23} |  {r2_score(y_test,ens_pred):>8.4f}  | {mean_absolute_error(y_test,ens_pred):>10.1f} | {np.sqrt(mean_squared_error(y_test,ens_pred)):>12.1f} | {np.mean(np.abs((y_test-ens_pred)/(y_test+1e-9)))*100:>12.2f} |")
print("  +-------------------------+------------+------------+--------------+--------------+")

print("\n  Cross-Validation (5-Fold) - Random Forest:")
cv_scores = cross_val_score(rf_m, scaler.transform(X), y, cv=KFold(5, shuffle=True, random_state=42), scoring='r2')
print(f"  Folds : {[f'{s:.4f}' for s in cv_scores]}")
print(f"  Mean  : {cv_scores.mean():.4f}   Std : {cv_scores.std():.4f}")

print("\n  Top 10 Feature Importances (Random Forest):")
fi = pd.Series(rf_m.feature_importances_, index=X.columns).sort_values(ascending=False)
for fn, imp in fi.head(10).items():
    bar = '#' * int(imp * 100)
    print(f"  {fn:<35} {imp:.4f}  {bar}")

# ─────────────────────────────────────────────
# PART 2 – ENTERPRISE ESG (CLASSIFICATION)
# ─────────────────────────────────────────────
print("\n\n[2/2] ENTERPRISE ESG RISK CLASSIFICATION MODEL")
print("-" * 60)
print("  Generating synthetic ESG dataset...")

np.random.seed(42)
n = 2000
industry_map = {'technology':1,'manufacturing':2,'retail':3,'healthcare':4,
                'finance':5,'energy':6,'transport':7,'agriculture':8}
industry_penalty = {'technology':3,'finance':2,'healthcare':1,'retail':0,
                    'transport':-1,'manufacturing':-2,'agriculture':-3,'energy':-5}
industries = np.random.choice(list(industry_map.keys()), n)
employees  = np.random.randint(10, 50000, n)
energy_kwh = np.random.uniform(1000, 500000, n)
travel_km  = np.random.uniform(0, 200000, n)
cloud_pct  = np.random.uniform(0, 100, n)
waste_rec  = np.random.uniform(0, 100, n)
renew_pct  = np.random.uniform(0, 100, n)
has_policy = np.random.randint(0, 2, n)
remote     = np.random.uniform(0, 100, n)
offsets    = np.random.uniform(0, 100, n)
supply_sc  = np.random.uniform(0, 10, n)
board_div  = np.random.uniform(0, 100, n)
training_h = np.random.uniform(0, 100, n)

esg = (renew_pct*0.3 + waste_rec*0.2 + cloud_pct*0.1 + remote*0.1 + offsets*0.1
       + supply_sc*2 + board_div*0.1 + training_h*0.05 + has_policy*10
       - (energy_kwh/(employees+1))*0.001
       - (travel_km/(employees+1))*0.005
       + np.array([industry_penalty[i] for i in industries]))

labels = np.where(esg < 20, 'High Risk', np.where(esg < 45, 'Medium Risk', 'Low Risk'))

Xe = np.column_stack([
    [industry_map[i] for i in industries], employees,
    energy_kwh/(employees+1), travel_km/(employees+1),
    cloud_pct, waste_rec, renew_pct, has_policy,
    remote, offsets, supply_sc, board_div, training_h
])

Xe_tr, Xe_te, ye_tr, ye_te = train_test_split(Xe, labels, test_size=0.2, stratify=labels, random_state=42)
dt = DecisionTreeClassifier(max_depth=8, min_samples_split=10, min_samples_leaf=5, random_state=42)
dt.fit(Xe_tr, ye_tr)
ye_pred = dt.predict(Xe_te)

acc = accuracy_score(ye_te, ye_pred)
print(f"\n  Decision Tree Accuracy : {acc:.4f}  ({acc*100:.1f}%)")
print("\n  Classification Report:")
print(classification_report(ye_te, ye_pred))

cm_labels = sorted(set(list(ye_te) + list(ye_pred)))
cm = confusion_matrix(ye_te, ye_pred, labels=cm_labels)
print("  Confusion Matrix  (rows=Actual, cols=Predicted):")
header = "  " + " "*12 + "  ".join(f"{l[:8]:>8}" for l in cm_labels)
print(header)
for i, lbl in enumerate(cm_labels):
    row = "  " + f"{lbl[:12]:<12}" + "  ".join(f"{cm[i][j]:>8}" for j in range(len(cm_labels)))
    print(row)

cv_e = cross_val_score(dt, Xe, labels, cv=5, scoring='accuracy')
print(f"\n  5-Fold CV Accuracy : {cv_e.mean():.4f} +/- {cv_e.std():.4f}")

# ─────────────────────────────────────────────
# PART 3 – EDGE CASE TESTING
# ─────────────────────────────────────────────
print("\n\n[3/3] EDGE CASE TESTING")
print("=" * 60)

feature_names = list(X.columns)

def predict_individual(overrides):
    base = {col: 0.0 for col in feature_names}
    base.update({'vehicle_type_enc':1,'vehicle_km':800,'vehicle_km_log':np.log1p(800),
                 'flight_score':1,'heating_factor':0.5,'elec_hours':7,'energy_eff':0.5,
                 'diet_factor':2.0,'grocery':150,'grocery_log':np.log1p(150),
                 'new_clothes':5,'shower_score':2,'recycling_count':2,'recycles_any':1,
                 'weekly_waste':30,'social_score':2,'is_male':0,'cook_appliance_count':2,
                 'intense_appliances':1})
    base.update(overrides)
    row = pd.DataFrame([base], columns=feature_names).fillna(0)
    return rf_m.predict(scaler.transform(row))[0]

individual_cases = [
    ("Ultra-Green (vegan, no car, no flights)",
     {'vehicle_type_enc':0,'vehicle_km':0,'vehicle_km_log':0,'flight_score':0,
      'diet_factor':1.0,'recycling_count':4,'recycles_any':1,'energy_eff':1,
      'weekly_waste':10,'new_clothes':1,'grocery':80,'grocery_log':np.log1p(80)}),
    ("Average City Dweller",
     {'vehicle_type_enc':1,'vehicle_km':1000,'vehicle_km_log':np.log1p(1000),
      'flight_score':1,'diet_factor':2.0,'recycling_count':2,'recycles_any':1,
      'energy_eff':0.5,'weekly_waste':40,'new_clothes':5}),
    ("Frequent Flyer + Meat Diet",
     {'vehicle_type_enc':1,'vehicle_km':2000,'vehicle_km_log':np.log1p(2000),
      'flight_score':3,'diet_factor':2.5,'recycling_count':0,'recycles_any':0,
      'energy_eff':0,'weekly_waste':80,'new_clothes':20,'grocery':400,'grocery_log':np.log1p(400)}),
    ("Max Carbon (all high-emission choices)",
     {'vehicle_type_enc':2,'vehicle_km':5000,'vehicle_km_log':np.log1p(5000),
      'flight_score':5,'diet_factor':2.5,'recycling_count':0,'recycles_any':0,
      'energy_eff':0,'heating_factor':0.8,'weekly_waste':120,'new_clothes':40,
      'social_score':3,'intense_appliances':3}),
    ("No Vehicle + Vegetarian",
     {'vehicle_type_enc':0,'vehicle_km':0,'vehicle_km_log':0,'flight_score':0,
      'diet_factor':1.5,'energy_eff':1,'recycling_count':3,'recycles_any':1}),
    ("Electric Vehicle + Vegan",
     {'vehicle_type_enc':4,'vehicle_km':1500,'vehicle_km_log':np.log1p(1500),
      'flight_score':1,'diet_factor':1.0,'energy_eff':1,'recycling_count':4,'recycles_any':1}),
    ("Heavy Shopper, Short Haul Flights",
     {'vehicle_type_enc':1,'vehicle_km':800,'vehicle_km_log':np.log1p(800),
      'flight_score':1,'diet_factor':2.5,'new_clothes':30,'grocery':600,'grocery_log':np.log1p(600),
      'recycling_count':0,'recycles_any':0,'weekly_waste':100}),
    ("Hybrid Car, Pescatarian, Partial Recycler",
     {'vehicle_type_enc':3,'vehicle_km':1200,'vehicle_km_log':np.log1p(1200),
      'flight_score':1,'diet_factor':2.0,'recycling_count':2,'recycles_any':1,'energy_eff':0.5}),
]

print("\n  INDIVIDUAL PROFILES")
print(f"  {'Profile':<45} {'CO2e/yr':>10}  Category")
print("  " + "-"*72)
for name, overrides in individual_cases:
    pred = predict_individual(overrides)
    cat  = "LOW  (<2000)" if pred < 2000 else ("MEDIUM" if pred < 4000 else "HIGH (>4000)")
    print(f"  {name:<45} {pred:>8,.0f} kg  {cat}")

def predict_esg(profile):
    row = np.array([[
        industry_map.get(profile.get('industry','technology'), 1),
        profile.get('employees', 500),
        profile.get('energy_per_emp', 1000),
        profile.get('travel_per_emp', 500),
        profile.get('cloud_pct', 50),
        profile.get('waste_recycled', 50),
        profile.get('renewable_pct', 30),
        profile.get('has_policy', 0),
        profile.get('remote_work', 30),
        profile.get('carbon_offsets', 20),
        profile.get('supply_chain', 5),
        profile.get('board_diversity', 40),
        profile.get('training_hours', 20),
    ]])
    return dt.predict(row)[0]

esg_cases = [
    ("Green Tech Startup",          {'industry':'technology','employees':50,'energy_per_emp':200,'renewable_pct':90,'cloud_pct':95,'waste_recycled':80,'has_policy':1,'remote_work':80,'carbon_offsets':80,'supply_chain':9,'board_diversity':60,'training_hours':80}),
    ("Heavy Manufacturer",          {'industry':'manufacturing','employees':5000,'energy_per_emp':50000,'renewable_pct':5,'cloud_pct':10,'waste_recycled':20,'has_policy':0,'remote_work':5,'carbon_offsets':5,'supply_chain':2,'board_diversity':20,'training_hours':10}),
    ("Responsible Bank",            {'industry':'finance','employees':2000,'energy_per_emp':500,'renewable_pct':60,'cloud_pct':80,'waste_recycled':70,'has_policy':1,'remote_work':60,'carbon_offsets':60,'supply_chain':7,'board_diversity':55,'training_hours':50}),
    ("High-Travel Logistics Co",    {'industry':'transport','employees':1000,'energy_per_emp':20000,'travel_per_emp':50000,'renewable_pct':10,'cloud_pct':30,'waste_recycled':30,'has_policy':0,'remote_work':10,'carbon_offsets':10,'supply_chain':3,'board_diversity':25,'training_hours':15}),
    ("Sustainable Farm",            {'industry':'agriculture','employees':200,'energy_per_emp':2000,'renewable_pct':50,'waste_recycled':60,'has_policy':1,'carbon_offsets':40,'supply_chain':6,'board_diversity':50,'training_hours':30}),
    ("Mid-Size Hospital",           {'industry':'healthcare','employees':800,'energy_per_emp':3000,'renewable_pct':40,'cloud_pct':60,'waste_recycled':55,'has_policy':1,'remote_work':30,'carbon_offsets':35,'supply_chain':6,'board_diversity':55,'training_hours':45}),
    ("Fast Fashion Retailer",       {'industry':'retail','employees':3000,'energy_per_emp':2000,'renewable_pct':15,'waste_recycled':25,'has_policy':0,'remote_work':10,'carbon_offsets':10,'supply_chain':2,'board_diversity':30,'training_hours':10}),
    ("Coal Energy Giant",           {'industry':'energy','employees':10000,'energy_per_emp':100000,'renewable_pct':2,'cloud_pct':20,'waste_recycled':15,'has_policy':0,'remote_work':5,'carbon_offsets':5,'supply_chain':1,'board_diversity':15,'training_hours':5}),
    ("Small Eco Retailer",          {'industry':'retail','employees':30,'energy_per_emp':300,'renewable_pct':80,'waste_recycled':90,'has_policy':1,'remote_work':50,'carbon_offsets':60,'supply_chain':8,'board_diversity':60,'training_hours':60}),
    ("Mid-Transition Manufacturer", {'industry':'manufacturing','employees':2000,'energy_per_emp':10000,'renewable_pct':40,'waste_recycled':55,'has_policy':1,'remote_work':20,'carbon_offsets':30,'supply_chain':5,'board_diversity':40,'training_hours':35}),
]

print("\n\n  ENTERPRISE ESG PROFILES")
print(f"  {'Profile':<35} {'ESG Verdict'}")
print("  " + "-"*55)
verdict_badge = {'Low Risk':'LOW RISK','Medium Risk':'MEDIUM RISK','High Risk':'HIGH RISK'}
for name, profile in esg_cases:
    result = predict_esg(profile)
    print(f"  {name:<35} {verdict_badge.get(result, result)}")

print("\n" + "=" * 60)
print("  EVALUATION COMPLETE")
print("=" * 60)
