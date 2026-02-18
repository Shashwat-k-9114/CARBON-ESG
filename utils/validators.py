def validate_individual_input(data):
    """
    Validate individual carbon calculator inputs
    data: dictionary of form inputs
    returns: list of error messages
    """
    errors = []
    
    required_fields = ['country', 'electricity_kwh', 'vehicle_type', 
                      'flight_type', 'diet_type', 'shopping_freq', 'recycling']
    
    # Check for missing required fields
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Validate electricity
    electricity = data.get('electricity_kwh', '0')
    try:
        electricity_val = float(electricity)
        if electricity_val < 0 or electricity_val > 10000:
            errors.append("Electricity usage must be between 0 and 10,000 kWh")
    except ValueError:
        errors.append("Electricity usage must be a number")
    
    # Handle vehicle type and km
    vehicle_type = data.get('vehicle_type', 'none')
    vehicle_km = data.get('vehicle_km', '0')
    
    # Validate vehicle km based on vehicle type
    if vehicle_type != 'none':
        try:
            vehicle_km_val = float(vehicle_km)
            if vehicle_km_val < 0 or vehicle_km_val > 10000:
                errors.append("Vehicle km must be between 0 and 10,000")
        except ValueError:
            if not vehicle_km.strip():
                errors.append("Vehicle km is required when you have a vehicle")
            else:
                errors.append("Vehicle km must be a number")
    else:
        # If no vehicle, set vehicle_km to 0
        data['vehicle_km'] = '0'
    
    # Validate categorical values
    valid_vehicle = ['none', 'petrol', 'diesel']
    if vehicle_type not in valid_vehicle:
        errors.append(f"Vehicle type must be one of: {', '.join(valid_vehicle)}")
    
    valid_flight = ['none', 'short', 'medium', 'long']
    if data.get('flight_type', '') not in valid_flight:
        errors.append(f"Flight type must be one of: {', '.join(valid_flight)}")
    
    valid_diet = ['veg', 'mixed', 'non-veg']
    if data.get('diet_type', '') not in valid_diet:
        errors.append(f"Diet type must be one of: {', '.join(valid_diet)}")
    
    valid_shopping = ['low', 'medium', 'high']
    if data.get('shopping_freq', '') not in valid_shopping:
        errors.append(f"Shopping frequency must be one of: {', '.join(valid_shopping)}")
    
    valid_recycling = ['yes', 'no']
    if data.get('recycling', '') not in valid_recycling:
        errors.append("Recycling must be 'yes' or 'no'")
    
    return errors


def validate_enterprise_input(data):
    """
    Validate enterprise ESG assessment inputs
    data: dictionary of form inputs
    returns: list of error messages
    """
    errors = []
    
    required_fields = ['company_name', 'industry', 'employees', 'energy_usage',
                      'travel_km', 'cloud_usage', 'waste_management']
    
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            errors.append(f"{field.replace('_', ' ').title()} is required")
    
    # Validate numerical values
    try:
        employees = int(data['employees'])
        if employees < 1 or employees > 1000000:
            errors.append("Number of employees must be between 1 and 1,000,000")
    except (ValueError, TypeError):
        errors.append("Employees must be a whole number")
    
    try:
        energy = float(data['energy_usage'])
        if energy < 0 or energy > 10000000:
            errors.append("Energy usage must be between 0 and 10,000,000")
    except (ValueError, TypeError):
        errors.append("Energy usage must be a number")
    
    try:
        travel = float(data['travel_km'])
        if travel < 0 or travel > 10000000:
            errors.append("Travel km must be between 0 and 10,000,000")
    except (ValueError, TypeError):
        errors.append("Travel km must be a number")
    
    try:
        waste = int(data['waste_management'])
        if waste < 1 or waste > 5:
            errors.append("Waste management level must be between 1 and 5")
    except (ValueError, TypeError):
        errors.append("Waste management must be a number between 1 and 5")
    
    # Validate categorical
    valid_cloud = ['yes', 'no']
    if data.get('cloud_usage', '') not in valid_cloud:
        errors.append("Cloud usage must be 'yes' or 'no'")
    
    return errors


def validate_login(data):
    """
    Validate login form
    data: dictionary of form inputs
    returns: list of error messages
    """
    errors = []
    
    if 'username' not in data or not data['username'].strip():
        errors.append("Username is required")
    
    if 'password' not in data or not data['password'].strip():
        errors.append("Password is required")
    
    return errors


def validate_register(data):
    """
    Validate registration form
    data: dictionary of form inputs
    returns: list of error messages
    """
    errors = validate_login(data)
    
    if 'email' not in data or not data['email'].strip():
        errors.append("Email is required")
    elif '@' not in data['email']:
        errors.append("Valid email is required")
    
    if 'user_type' not in data or data['user_type'] not in ['individual', 'enterprise']:
        errors.append("User type must be 'individual' or 'enterprise'")
    
    if 'confirm_password' in data and data['password'] != data['confirm_password']:
        errors.append("Passwords do not match")
    
    return errors