import joblib
import numpy as np
import pandas as pd
import os


class CarbonCalculator:
    def __init__(self):
        self.carbon_model = None
        self.scaler = None
        self.model_features = None
        self.model_type = None
        self.ensemble_weights = None

        model_path = "models/carbon_model_laptop.pkl"

        if os.path.exists(model_path):
            model_package = joblib.load(model_path)

            self.carbon_model = model_package.get("model")
            self.scaler = model_package.get("scaler")
            self.model_features = model_package.get("features")
            self.model_type = model_package.get("model_type")
            self.ensemble_weights = model_package.get("ensemble_weights")

            print(f"ML Model Loaded: {self.model_type}")
            print(f"Features Expected: {len(self.model_features)}")

        self.emission_factors = joblib.load("models/emission_factors.pkl")

    # ============================================================
    # MAIN FUNCTION
    # ============================================================

    def calculate_individual_footprint(self, inputs):

        # ------------------------------------------------------------
        # 1️⃣ RULE-BASED CALCULATION
        # ------------------------------------------------------------

        country = inputs.get("country", "Other")

        electricity_factor = self.emission_factors["electricity"].get(country, 0.5)
        electricity_emissions = inputs["electricity_kwh"] * electricity_factor * 12

        vehicle_type = inputs["vehicle_type"]
        vehicle_factor = self.emission_factors["vehicle"].get(vehicle_type, 0.18)
        vehicle_emissions = inputs["vehicle_km"] * vehicle_factor * 12

        flight_emissions = self.emission_factors["flights"].get(inputs["flight_type"], 0)

        diet_emissions = (
            self.emission_factors["diet"].get(inputs["diet_type"], 600) * 12
        )

        shopping_emissions = (
            self.emission_factors["shopping"].get(inputs["shopping_freq"], 150)
            * 12
        )

        recycling_effect = (
            self.emission_factors["recycling"].get(inputs["recycling"], 0) * 12
        )

        rule_based_total = (
            electricity_emissions
            + vehicle_emissions
            + flight_emissions
            + diet_emissions
            + shopping_emissions
            + recycling_effect
        )

        # ------------------------------------------------------------
        # 2️⃣ ML PREDICTION (FULL FEATURE REBUILD)
        # ------------------------------------------------------------

        ml_prediction = None
        final_footprint = rule_based_total

        if self.carbon_model and self.model_features:

            try:
                # Create full feature dict initialized to zero
                feature_dict = {feature: 0 for feature in self.model_features}

                # -------------------------
                # Core Feature Mapping
                # -------------------------

                vehicle_map = {"none": 0, "petrol": 1, "diesel": 2}
                flight_map = {"none": 0, "short": 1, "medium": 2, "long": 3}
                diet_map = {"veg": 1.5, "mixed": 2.0, "non-veg": 2.5}
                shopping_map = {"low": 1, "medium": 2, "high": 3}

                # Vehicle
                if "vehicle_type_encoded" in feature_dict:
                    feature_dict["vehicle_type_encoded"] = vehicle_map.get(
                        inputs["vehicle_type"], 0
                    )

                if "vehicle_km" in feature_dict:
                    feature_dict["vehicle_km"] = inputs["vehicle_km"]

                if "vehicle_km_log" in feature_dict:
                    feature_dict["vehicle_km_log"] = np.log1p(inputs["vehicle_km"])

                # Flight
                if "flight_freq_score" in feature_dict:
                    feature_dict["flight_freq_score"] = flight_map.get(
                        inputs["flight_type"], 0
                    )

                # Diet
                if "diet_carbon_factor" in feature_dict:
                    feature_dict["diet_carbon_factor"] = diet_map.get(
                        inputs["diet_type"], 2.0
                    )

                # Shopping proxy
                if "clothes_consumption_score" in feature_dict:
                    feature_dict["clothes_consumption_score"] = shopping_map.get(
                        inputs["shopping_freq"], 2
                    )

                # Recycling
                if "recycles_any" in feature_dict:
                    feature_dict["recycles_any"] = 1 if inputs["recycling"] == "yes" else 0

                # Interaction Terms
                if "vehicle_km_type_interaction" in feature_dict:
                    feature_dict["vehicle_km_type_interaction"] = (
                        feature_dict.get("vehicle_km", 0)
                        * feature_dict.get("vehicle_type_encoded", 0)
                    )

                if "lifestyle_composite" in feature_dict:
                    feature_dict["lifestyle_composite"] = (
                        feature_dict.get("diet_carbon_factor", 2.0)
                        + feature_dict.get("clothes_consumption_score", 2)
                        + feature_dict.get("flight_freq_score", 0)
                    )

                # -------------------------
                # Create DataFrame in correct order
                # -------------------------

                ml_input_df = pd.DataFrame([feature_dict])[self.model_features]

                # Apply scaler if exists
                if self.scaler:
                    ml_input_scaled = self.scaler.transform(ml_input_df)
                else:
                    ml_input_scaled = ml_input_df.values

                # Handle ensemble model
                if isinstance(self.carbon_model, dict):
                    rf = self.carbon_model["rf"]
                    gb = self.carbon_model["gb"]
                    ridge = self.carbon_model["ridge"]
                    weights = self.ensemble_weights or [0.4, 0.4, 0.2]

                    ml_prediction = (
                        rf.predict(ml_input_scaled)[0] * weights[0]
                        + gb.predict(ml_input_scaled)[0] * weights[1]
                        + ridge.predict(ml_input_scaled)[0] * weights[2]
                    )
                else:
                    ml_prediction = self.carbon_model.predict(
                        ml_input_scaled
                    )[0]

                # Blend 70% ML + 30% Rule
                final_footprint = 0.7 * ml_prediction + 0.3 * rule_based_total

            except Exception as e:
                print("ML Prediction Failed:", e)
                ml_prediction = None
                final_footprint = rule_based_total

        # ------------------------------------------------------------
        # 3️⃣ BREAKDOWN SCALING
        # ------------------------------------------------------------

        raw_breakdown = {
            "electricity": electricity_emissions,
            "transport": vehicle_emissions + flight_emissions,
            "diet": diet_emissions,
            "shopping": shopping_emissions,
            "recycling_credit": recycling_effect,
        }

        raw_total = sum(raw_breakdown.values())
        scaling_factor = final_footprint / raw_total if raw_total > 0 else 1

        breakdown = {
            key: round(value * scaling_factor, 2)
            for key, value in raw_breakdown.items()
        }

        final_footprint = sum(breakdown.values())

        # ------------------------------------------------------------
        # 4️⃣ Carbon Level Classification
        # ------------------------------------------------------------

        if final_footprint < 3000:
            carbon_level = "Very Low"
        elif final_footprint < 5000:
            carbon_level = "Low"
        elif final_footprint < 7000:
            carbon_level = "Medium-Low"
        elif final_footprint < 9000:
            carbon_level = "Medium"
        elif final_footprint < 12000:
            carbon_level = "Medium-High"
        else:
            carbon_level = "High"

        suggestions = self.generate_suggestions(
            inputs, final_footprint, carbon_level
        )

        return {
            "total_footprint": round(final_footprint, 2),
            "carbon_level": carbon_level,
            "breakdown": breakdown,
            "suggestions": suggestions,
            "ml_prediction": round(ml_prediction, 2) if ml_prediction else None,
            "rule_based": round(rule_based_total, 2),
        }

    # ============================================================
    # SUGGESTIONS
    # ============================================================

    def generate_suggestions(self, inputs, footprint, level):
        suggestions = []

        if footprint > 12000:
            suggestions.append(
                "🚨 Your carbon footprint is very high. Consider consulting a sustainability expert."
            )

        if inputs["electricity_kwh"] > 500:
            suggestions.append(
                "💡 Reduce electricity usage by switching to LED bulbs and efficient appliances."
            )

        if inputs["vehicle_type"] != "none" and inputs["vehicle_km"] > 800:
            suggestions.append(
                "🚗 Consider public transport, EVs, or carpooling."
            )

        if inputs["diet_type"] == "non-veg":
            suggestions.append(
                "🌱 Reduce meat consumption to lower diet emissions."
            )

        if inputs["shopping_freq"] == "high":
            suggestions.append(
                "🛍️ Reduce shopping frequency and choose sustainable products."
            )

        if inputs["flight_type"] in ["medium", "long"]:
            suggestions.append(
                "✈️ Consider reducing flight frequency where possible."
            )

        if len(suggestions) < 3:
            suggestions.append("🌳 Offset emissions via verified carbon credits.")
            suggestions.append("🏠 Improve insulation and home efficiency.")

        return suggestions


# ============================================================
# ESG CALCULATOR CLASS - ADDED TO FIX THE IMPORT ERROR
# ============================================================

class ESGCalculator:
    def __init__(self):
        # Try to load ESG model if it exists
        esg_model_path = 'models/esg_model.pkl'
        if os.path.exists(esg_model_path):
            self.esg_model = joblib.load(esg_model_path)
            print("ESG Model Loaded")
        else:
            # Create a simple default model if none exists
            from sklearn.tree import DecisionTreeClassifier
            print("ESG Model not found, using default classifier")
            
            # Create synthetic training data
            np.random.seed(42)
            X_synth = np.random.rand(100, 8)
            y_synth = np.random.choice(['Low', 'Medium', 'High'], 100, p=[0.3, 0.4, 0.3])
            
            self.esg_model = DecisionTreeClassifier(max_depth=5, random_state=42)
            self.esg_model.fit(X_synth, y_synth)
        
    def calculate_esg_score(self, inputs):
        """
        Calculate ESG score and risk for enterprises
        """
        # Calculate derived metrics
        emissions_per_employee = (inputs['energy_usage'] * 0.5) / max(inputs['employees'], 1)
        energy_intensity = inputs['energy_usage'] / max(inputs['employees'], 1)
        
        # Prepare for ML model
        industry_map = {
            'Manufacturing': 0, 'IT': 1, 'Retail': 2,
            'Healthcare': 3, 'Transport': 4, 'Other': 1
        }
        
        ml_input = np.array([[
            industry_map.get(inputs['industry'], 1),
            inputs['employees'],
            inputs['energy_usage'],
            inputs['travel_km'],
            1 if inputs['cloud_usage'] == 'yes' else 0,
            inputs['waste_management'],
            emissions_per_employee,
            energy_intensity
        ]])
        
        # Get risk prediction
        risk_prediction = self.esg_model.predict(ml_input)[0]
        
        # Calculate ESG score (0-100)
        base_score = 50
        
        # Adjust based on inputs
        if inputs['cloud_usage'] == 'yes':
            base_score += 10  # Cloud is generally more efficient
        
        if inputs['waste_management'] >= 4:
            base_score += 15
        elif inputs['waste_management'] >= 3:
            base_score += 5
        
        if emissions_per_employee < 2:
            base_score += 15
        elif emissions_per_employee < 5:
            base_score += 5
        
        if inputs['employees'] > 100:
            base_score += 5  # Larger companies typically have better systems
        
        # Cap score
        final_score = min(100, max(0, base_score))
        
        # Component scores
        environmental_score = final_score * 0.7
        social_score = final_score * 0.15
        governance_score = final_score * 0.15
        
        return {
            'total_score': round(final_score, 1),
            'environmental_score': round(environmental_score, 1),
            'social_score': round(social_score, 1),
            'governance_score': round(governance_score, 1),
            'esg_risk': risk_prediction,
            'emissions_per_employee': round(emissions_per_employee, 2),
            'energy_intensity': round(energy_intensity, 2),
            'recommendations': self.generate_esg_recommendations(inputs, risk_prediction, final_score)
        }
    
    def generate_esg_recommendations(self, inputs, risk, score):
        """Generate ESG improvement recommendations"""
        recommendations = []
        
        if risk == 'High':
            recommendations.append("⚠️ HIGH RISK: Immediate action required. Conduct a comprehensive ESG audit.")
        
        if score < 50:
            recommendations.append("📋 Develop a formal ESG policy and sustainability strategy.")
        
        if inputs['cloud_usage'] == 'no':
            recommendations.append("☁️ Migrate to cloud services to reduce energy consumption by up to 30%.")
        
        if inputs['waste_management'] < 3:
            recommendations.append("🗑️ Implement a waste management system with recycling and composting.")
        
        if inputs['energy_usage'] / max(inputs['employees'], 1) > 1000:
            recommendations.append("🔋 Conduct an energy audit and invest in energy-efficient equipment.")
        
        recommendations.append("📊 Start tracking and reporting ESG metrics quarterly.")
        recommendations.append("👥 Establish an ESG committee with board oversight.")
        
        return recommendations