import joblib
import numpy as np
import pandas as pd
import os
import json


class CarbonCalculator:
    def __init__(self):
        self.carbon_model = None
        self.model_features = None

        model_path = "models/carbon_model_v3.pkl"

        if os.path.exists(model_path):
            try:
                model_package = joblib.load(model_path)

                self.carbon_model = model_package["model"]
                self.model_features = model_package["features"]

                print("ML Model Loaded: UI-Aligned v2")
                print(f"Features Expected: {len(self.model_features)}")

            except Exception as e:
                print(f"Error loading model: {e}")
                self.carbon_model = None
                self.model_features = []
        else:
            print("No model found at", model_path)
            self.carbon_model = None
            self.model_features = []

        # Load emission factors
        try:
            self.emission_factors = joblib.load("models/emission_factors.pkl")
        except:
            # Emission factors sourced from IEA 2023 + DEFRA 2023 guidelines
            self.emission_factors = {
                'electricity': {
                    'USA': 0.38, 'UK': 0.23, 'Canada': 0.15, 'Australia': 0.70,
                    'Germany': 0.35, 'France': 0.05, 'India': 0.67, 'China': 0.58,
                    'Japan': 0.43, 'Brazil': 0.08, 'South Africa': 0.80, 'Other': 0.50
                },
                'vehicle': {
                    'none': 0, 'petrol': 0.19, 'diesel': 0.21,
                    'hybrid': 0.10, 'electric': 0.05
                },
                'flights': {
                    'none': 0, 'domestic': 300, 'international': 1500, 'frequent': 3000
                },
                'diet': {
                    'vegan': 1000, 'vegetarian': 1500, 'mixed': 2200, 'non-veg': 2800
                },
                'shopping': {'low': 500, 'medium': 1000, 'high': 2000},
                'recycling': {'yes': -200, 'no': 0}
            }

    # ============================================================
    # MAIN FUNCTION
    # ============================================================

    def calculate_individual_footprint(self, inputs):

        # ==============================
        # 1️⃣ RULE-BASED CALCULATION
        # ==============================

        country = inputs.get("country", "Other")
        household_size = max(int(inputs.get("household_size", 1)), 1)
        energy_source = inputs.get("energy_source", "grid")
        home_type = inputs.get("home_type", "apartment")
        heating_source = inputs.get("heating_source", "electric")
        meat_frequency = int(inputs.get("meat_frequency", 3))
        food_waste = inputs.get("food_waste", "rarely")
        vehicle_efficiency = float(inputs.get("vehicle_efficiency", 15))
        renewable_percent = float(inputs.get("renewable_percent", 0))

        # Multipliers
        _home_type_mult  = {"apartment": 0.8, "house": 1.0, "shared": 0.6}
        _heating_ef      = {"electric": 0.4, "gas": 0.2, "oil": 0.3, "heatpump": 0.1, "none": 0}
        _food_waste_mult = {"rarely": 1.0, "sometimes": 1.1, "often": 1.2}
        _energy_mult     = {"grid": 1.0, "solar": 0.1, "mixed": 0.6}

        # Electricity — adjusted for home type + renewable %
        country_factor = self.emission_factors["electricity"].get(country, 0.5)
        base_elec_per_capita = inputs["electricity_kwh"] * 12 / household_size
        home_adj_elec = base_elec_per_capita * _home_type_mult.get(home_type, 1.0)
        if energy_source == "grid":
            effective_ef = country_factor * (1 - renewable_percent / 100) + (0.1 * renewable_percent / 100)
        else:
            effective_ef = country_factor * _energy_mult.get(energy_source, 1.0)
        electricity_emissions = home_adj_elec * effective_ef

        # Heating — based on home type base kWh × fuel factor
        _heating_base_kwh = {"house": 4000, "apartment": 2500, "shared": 1500}
        heating_kwh_per_capita = _heating_base_kwh.get(home_type, 2500) / household_size
        heating_emissions = heating_kwh_per_capita * _heating_ef.get(heating_source, 0.2)

        # Transport — use fuel efficiency if provided
        if inputs["vehicle_type"] != "none" and vehicle_efficiency > 0:
            fuel_per_km = 1 / vehicle_efficiency
            vehicle_emissions = inputs["vehicle_km"] * 12 * fuel_per_km * 2.3
        else:
            veh_factor = self.emission_factors["vehicle"].get(inputs["vehicle_type"], 0)
            vehicle_emissions = inputs["vehicle_km"] * veh_factor * 12

        flight_emissions = self.emission_factors["flights"].get(inputs["flight_type"], 0)

        # Diet — base + meat frequency + food waste adjustment
        base_diet = self.emission_factors["diet"].get(inputs["diet_type"], 2200)
        meat_extra = meat_frequency * 52 * 7.0
        diet_emissions = (base_diet + meat_extra) * _food_waste_mult.get(food_waste, 1.0)

        shopping_emissions = self.emission_factors["shopping"].get(inputs["shopping_freq"], 1000)
        recycling_effect = self.emission_factors["recycling"].get(inputs["recycling"], 0)

        rule_based_total = (
            electricity_emissions + heating_emissions +
            vehicle_emissions + flight_emissions +
            diet_emissions + shopping_emissions + recycling_effect
        )


        # ==============================
        # 2️⃣ ML PREDICTION
        # ==============================

        ml_prediction = 0
        final_footprint = rule_based_total

        if self.carbon_model and self.model_features:
            try:
                # Maps matching the training script exactly
                _vehicle_ef = {"none": 0, "petrol": 0.19, "diesel": 0.21, "hybrid": 0.10, "electric": 0.05}
                _diet_ef    = {"veg": 1000, "mixed": 2200, "non-veg": 2800}
                _shop_ef    = {"low": 500, "medium": 1000, "high": 2000}
                _flight_map = {0: 0, 1: 300, 2: 1500, 3: 3000}
                _energy_mult = {"grid": 1.0, "solar": 0.1, "mixed": 0.6}

                # Convert flight_type string → integer used in training
                flight_str_to_int = {"none": 0, "domestic": 1, "international": 2, "frequent": 3}
                flights_int = flight_str_to_int.get(inputs.get("flight_type", "none"), 0)

                elec_per_capita   = inputs["electricity_kwh"] * 12 / household_size
                country_ef_val    = self.emission_factors["electricity"].get(country, 0.5)
                elec_country_fac  = elec_per_capita * country_ef_val
                elec_source_mult  = _energy_mult.get(energy_source, 1.0)
                veh_emission_raw  = inputs["vehicle_km"] * 12 * _vehicle_ef.get(inputs["vehicle_type"], 0)
                flt_emission_raw  = _flight_map.get(flights_int, 0)
                diet_emission_raw = _diet_ef.get(inputs["diet_type"], 2200)
                shop_emission_raw = _shop_ef.get(inputs["shopping_freq"], 1000)
                rec_credit        = -200 if inputs["recycling"] == "yes" else 0

                ml_input = pd.DataFrame([{
                    "country":              inputs["country"],
                    "electricity_kwh":      inputs["electricity_kwh"],
                    "household_size":       household_size,
                    "energy_source":        energy_source,
                    "vehicle_type":         inputs["vehicle_type"],
                    "vehicle_km":           inputs["vehicle_km"],
                    "flights_per_year":     flights_int,
                    "public_transport":     inputs.get("public_transport", "sometimes"),
                    "diet_type":            inputs["diet_type"],
                    "shopping_freq":        inputs["shopping_freq"],
                    "recycling":            inputs["recycling"],
                    "elec_per_capita":      elec_per_capita,
                    "elec_country_factor":  elec_country_fac,
                    "elec_source_mult":     elec_source_mult,
                    "vehicle_emission_raw": veh_emission_raw,
                    "flight_emission_raw":  flt_emission_raw,
                    "diet_emission_raw":    diet_emission_raw,
                    "shopping_emission_raw":shop_emission_raw,
                    "recycle_credit":       rec_credit,
                    "home_type":              home_type,
                    "heating_source":         heating_source,
                    "meat_frequency":         meat_frequency,
                    "food_waste":             food_waste,
                    "vehicle_efficiency":     vehicle_efficiency,
                    "renewable_percent":      renewable_percent,
                    "elec_per_capita_base":   base_elec_per_capita,
                    "elec_per_capita_home_adj": home_adj_elec,
                    "country_ef":             country_factor,
                    "effective_elec_ef":      effective_ef,
                    "heating_kwh_per_capita": heating_kwh_per_capita,
                    "heating_emission_raw":   heating_emissions,

                }])

                categorical_cols = ["country", "energy_source", "vehicle_type", "home_type", "heating_source", "food_waste",
                                    "public_transport", "diet_type", "shopping_freq", "recycling"]
                ml_encoded = pd.get_dummies(ml_input, columns=categorical_cols, drop_first=False)
                ml_encoded = ml_encoded.reindex(columns=self.model_features, fill_value=0)

                ml_prediction  = float(self.carbon_model.predict(ml_encoded)[0])
                final_footprint = ml_prediction

            except Exception as e:
                print("ML Prediction Failed, falling back to rule-based:", e)
                final_footprint = rule_based_total
        else:
            final_footprint = rule_based_total
        # if self.carbon_model and self.model_features:
        #     try:
        #         import pandas as pd

        #         ml_input = pd.DataFrame([{
        #             "country": inputs["country"],
        #             "electricity_kwh": inputs["electricity_kwh"],
        #             "household_size": household_size,
        #             "energy_source": energy_source,
        #             "vehicle_type": inputs["vehicle_type"],
        #             "vehicle_km": inputs["vehicle_km"],
        #             "flight_type": inputs["flight_type"],
        #             "diet_type": inputs["diet_type"],
        #             "shopping_freq": inputs["shopping_freq"],
        #             "recycling": 1 if inputs["recycling"] == "yes" else 0
        #         }])

        #         ml_encoded = pd.get_dummies(ml_input)
        #         ml_encoded = ml_encoded.reindex(columns=self.model_features, fill_value=0)
        #         ml_prediction = float(self.carbon_model.predict(ml_encoded)[0])

                

        #         # ==============================
        #         # Dynamic Hybrid Blending
        #         # ==============================

        #         if ml_prediction > 0:

        #             # Low emission users → trust rule more
        #             if rule_based_total < 2000:
        #                 alpha = 0.7

        #             # Very high users → trust ML more
        #             elif rule_based_total > 5000:
        #                 alpha = 0.3

        #             # Mid-range → balanced
        #             else:
        #                 alpha = 0.5

        #             final_footprint = (
        #                 alpha * rule_based_total +
        #                 (1 - alpha) * ml_prediction
        #             )

        #     except Exception as e:
        #         print("ML Prediction Failed:", e)
        #         final_footprint = rule_based_total

        # ==============================
        # 3️⃣ BREAKDOWN
        # ==============================

        raw_breakdown = {
            "electricity": electricity_emissions + heating_emissions,
            "transport": vehicle_emissions + flight_emissions,
            "diet": diet_emissions,
            "shopping": shopping_emissions,
            "recycling_credit": recycling_effect,
        }


        raw_total = sum(raw_breakdown.values())

        if raw_total <= 0:
            scaling_factor = 1
        else:
            scaling_factor = final_footprint / raw_total

        breakdown = {
            key: round(value * scaling_factor, 2)
            for key, value in raw_breakdown.items()
        }

        final_footprint = round(sum(breakdown.values()), 2)

        # ==============================
        # 4️⃣ LEVEL CLASSIFICATION
        # ==============================

        if final_footprint < 1538:
            carbon_level = "Well Below Average"
        elif final_footprint < 2080:
            carbon_level = "Below Average"
        elif final_footprint < 2768:
            carbon_level = "Near Average"
        elif final_footprint < 4285:
            carbon_level = "Above Average"
        else:
            carbon_level = "Well Above Average"

        return {
            "total_footprint": final_footprint,
            "carbon_level": carbon_level,
            "breakdown": breakdown,
            "ml_prediction": round(ml_prediction, 2),
            "rule_based": round(rule_based_total, 2),
            "suggestions": self.generate_suggestions(inputs, final_footprint, carbon_level)
        }
    # ============================================================
    # SUGGESTIONS
    # ============================================================

    def generate_suggestions(self, inputs, footprint, level):
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                
                prompt = f"""
                Analyze this user's carbon footprint profile:
                - Country: {inputs.get('country')}
                - Electricity: {inputs.get('electricity_kwh')} kWh/mo
                - Vehicle: {inputs.get('vehicle_type')} ({inputs.get('vehicle_km')} km/mo)
                - Diet: {inputs.get('diet_type')}
                - Total Footprint: {footprint} kg CO2e ({level})

                Provide 5 highly personalized, practical, and short actionable tips to reduce their emissions.
                """
                completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are an expert environmental consultant. Always output valid JSON with a single key 'suggestions' containing a list of 5 short string sentences. Do not use markdown outside of the JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama3-8b-8192",
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
                
                response_json = json.loads(completion.choices[0].message.content)
                if "suggestions" in response_json and isinstance(response_json["suggestions"], list):
                    return response_json["suggestions"][:6]
            except Exception as e:
                print(f"Groq API Error (Individual): {e}")

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

        return suggestions[:6]  # Limit to 6 suggestions


# ============================================================
# ESG CALCULATOR CLASS
# ============================================================
# ============================================================
# STRUCTURED ESG CALCULATOR (Explainable + Professional)
# ============================================================

class ESGCalculator:
    def __init__(self):
        print("Structured ESG Engine Loaded")

    # ============================================================
    # MAIN ESG CALCULATION
    # ============================================================

    def calculate_esg_score(self, inputs):

        employees = max(inputs.get('employees', 1), 1)
        energy_usage = inputs.get('energy_usage', 0)
        travel_km = inputs.get('travel_km', 0)
        waste_level = inputs.get('waste_management', 3)
        cloud_usage = inputs.get('cloud_usage', 'no')

        # ------------------------------------------------------------
        # 1️⃣ ENVIRONMENTAL SCORE (70%)
        # ------------------------------------------------------------

        energy_per_employee = energy_usage / employees
        travel_per_employee = travel_km / employees
        emissions_per_employee = energy_per_employee + (travel_per_employee * 0.2)
        industry_benchmarks = {
            "technology": 2.5,
            "manufacturing": 8.0,
            "finance": 1.5,
            "retail": 4.0,
            "healthcare": 3.5,
            "energy": 12.0,
            "agriculture": 6.0,
            "transport": 9.0,
            "other": 4.0
        }

        industry = inputs.get("industry", "other").lower()
        benchmark = industry_benchmarks.get(industry, 4.0)
        energy_intensity = energy_per_employee

        environmental_score = 100

        if emissions_per_employee < benchmark:
            benchmark_status = "Better than industry average"
        elif emissions_per_employee < benchmark * 1.5:
            benchmark_status = "Near industry average"
        else:
            benchmark_status = "Worse than industry average"

        if travel_km > 40000:
            environmental_score -= 5

        # Energy intensity penalty (kWh per employee per month)
        if energy_per_employee > 1500:
            environmental_score -= 30
        elif energy_per_employee > 800:
            environmental_score -= 20
        elif energy_per_employee > 400:
            environmental_score -= 10

        # Travel intensity penalty (km per employee per year)
        if travel_per_employee > 4000:
            environmental_score -= 25
        elif travel_per_employee > 2000:
            environmental_score -= 15
        elif travel_per_employee > 1000:
            environmental_score -= 10
        elif travel_per_employee > 500:
            environmental_score -= 5

        # Waste management bonus
        # Strong waste penalty scaling
        if waste_level <= 2:
            environmental_score -= 20
        elif waste_level == 3:
            environmental_score += 0
        elif waste_level == 4:
            environmental_score += 5
        elif waste_level == 5:
            environmental_score += 10

        # Cloud efficiency bonus
        if cloud_usage == "yes":
            environmental_score += 10

        environmental_score = max(0, min(100, environmental_score))

        # ------------------------------------------------------------
        # 2️⃣ SOCIAL SCORE (15%)
        # ------------------------------------------------------------

        social_score = 70  # Base assumption

        # Larger companies usually have more structured systems
        if employees > 500:
            social_score += 15
        elif employees > 100:
            social_score += 10
        elif employees > 20:
            social_score += 5

        social_score = max(0, min(100, social_score))

        # ------------------------------------------------------------
        # 3️⃣ GOVERNANCE SCORE (15%)
        # ------------------------------------------------------------

        governance_score = 60  # Base governance maturity

        # Waste maturity contributes
        governance_score += waste_level * 5

        # Cloud usage implies digital maturity
        if cloud_usage == "yes":
            governance_score += 10

        governance_score = max(0, min(100, governance_score))

        # ------------------------------------------------------------
        # 4️⃣ FINAL ESG SCORE
        # ------------------------------------------------------------

        final_score = (
            environmental_score * 0.70 +
            social_score * 0.15 +
            governance_score * 0.15
        )

        final_score = round(final_score, 1)

        # ------------------------------------------------------------
        # 5️⃣ RISK CLASSIFICATION
        # ------------------------------------------------------------

        # Determine ESG risk category
        if final_score >= 85:
            risk_prediction = "Low"
        elif final_score >= 65:
            risk_prediction = "Medium"
        else:
            risk_prediction = "High"

        return {
            'total_score': round(final_score, 1),
            'environmental_score': round(environmental_score, 1),
            'social_score': round(social_score, 1),
            'governance_score': round(governance_score, 1),
            'esg_risk': risk_prediction,
            'emissions_per_employee': round(emissions_per_employee, 2),
            'energy_intensity': round(energy_intensity, 2),
            'industry_benchmark': benchmark,
            'benchmark_status': benchmark_status,
            'recommendations': self.generate_esg_recommendations(inputs, risk_prediction, final_score)
        }

    # ============================================================
    # ESG RECOMMENDATIONS
    # ============================================================

    def generate_esg_recommendations(self, inputs, risk, score):
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                
                prompt = f"""
                Analyze this company's ESG profile:
                - Company: {inputs.get('company_name')}
                - Industry: {inputs.get('industry')}
                - Employees: {inputs.get('employees')}
                - Energy Usage: {inputs.get('energy_usage')} kWh/mo
                - Cloud Infrastructure: {inputs.get('cloud_usage')}
                - Waste Management Level: {inputs.get('waste_management')}/5
                - Overall ESG Risk: {risk}
                - Overall ESG Score: {score}/100

                Provide 5 highly personalized, strategic corporate recommendations to improve their ESG standing.
                """
                completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are an expert corporate ESG consultant. Always output valid JSON with a single key 'recommendations' containing a list of 5 short string sentences. Do not use markdown outside of the JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama3-8b-8192",
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
                
                response_json = json.loads(completion.choices[0].message.content)
                if "recommendations" in response_json and isinstance(response_json["recommendations"], list):
                    return response_json["recommendations"][:6]
            except Exception as e:
                print(f"Groq API Error (Enterprise): {e}")

        recommendations = []

        if risk == "High":
            recommendations.append(
                "⚠️ High ESG risk. Immediate sustainability audit recommended."
            )

        if inputs.get("cloud_usage") == "no":
            recommendations.append(
                "☁️ Consider migrating to cloud infrastructure for energy efficiency."
            )

        if inputs.get("waste_management", 0) < 3:
            recommendations.append(
                "🗑️ Improve waste management through recycling and structured disposal."
            )

        if inputs.get("energy_usage", 0) / max(inputs.get("employees", 1), 1) > 1000:
            recommendations.append(
                "🔋 Conduct an energy audit to reduce operational intensity."
            )

        recommendations.append(
            "📊 Begin quarterly ESG reporting and transparency tracking."
        ) 

        return recommendations[:6]