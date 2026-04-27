from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash

from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from datetime import datetime

# Import local modules
from config import Config
from database.database import init_db, get_db_connection
from utils.calculations import CarbonCalculator, ESGCalculator
from utils.validators import validate_individual_input, validate_enterprise_input, validate_login, validate_register
from utils.pdf_generator import PDFGenerator

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
calculator = CarbonCalculator()
esg_calculator = ESGCalculator()
pdf_gen = PDFGenerator()

# Ensure database is initialized
if not os.path.exists('database/carbon_esg.db'):
    init_db()

# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------
def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session

def get_current_user():
    """Get current user info from database"""
    if not is_logged_in():
        return None
    
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?', 
        (session['user_id'],)
    ).fetchone()
    conn.close()
    
    return dict(user) if user else None

# ------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------

@app.route('/')
def index():
    """Home/Landing page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if is_logged_in():
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        errors = validate_login(request.form)
        
        if errors:
            return render_template('login.html', errors=errors)
        
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', 
            (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['subscription_plan'] = user['subscription_plan'] if user['subscription_plan'] else 'free'
            session['user_type'] = user['user_type']
            return redirect(url_for('dashboard'))
        else:
            errors = ['Invalid username or password']
            return render_template('login.html', errors=errors)
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if is_logged_in():
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        errors = validate_register(request.form)
        
        if errors:
            return render_template('register.html', errors=errors)
        
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        user_type = request.form['user_type']
        
        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO users (username, email, password, user_type) VALUES (?, ?, ?, ?)',
                (username, email, password, user_type)
            )
            conn.commit()
            conn.close()
            
            # Auto-login after registration
            conn = get_db_connection()
            user = conn.execute(
                'SELECT id FROM users WHERE username = ?', 
                (username,)
            ).fetchone()
            conn.close()
            
            session['user_id'] = user['id']
            session['username'] = username
            session['user_type'] = user_type
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            errors = [f'Registration failed: {str(e)}']
            return render_template('register.html', errors=errors)
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """User dashboard based on user type"""
    if not is_logged_in():
        return redirect(url_for('login'))
    
    user = get_current_user()
    
    # Get user's previous assessments
    conn = get_db_connection()
    
    if user['user_type'] == 'individual':
        assessments = conn.execute(
            '''SELECT * FROM individual_assessments 
               WHERE user_id = ? ORDER BY created_at DESC LIMIT 5''',
            (user['id'],)
        ).fetchall()
        template = 'individual_dashboard.html'
    else:
        assessments = conn.execute(
            '''SELECT * FROM enterprise_assessments 
               WHERE user_id = ? ORDER BY created_at DESC LIMIT 5''',
            (user['id'],)
        ).fetchall()
        template = 'enterprise_dashboard.html'
    
    conn.close()
    
    return render_template(template, 
                          user=user, 
                          assessments=assessments)

@app.route('/calculate/individual', methods=['GET', 'POST'])
def calculate_individual():
    """Individual carbon footprint calculation"""
    if not is_logged_in():
        return redirect(url_for('login'))
    
    user = get_current_user()
    if user['user_type'] != 'individual':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Enforce free plan assessment limit
        plan = session.get('subscription_plan', 'free')
        if plan == 'free':
            conn = get_db_connection()
            from datetime import datetime
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0).strftime('%Y-%m-%d')
            count = conn.execute(
                'SELECT COUNT(*) FROM individual_assessments WHERE user_id = ? AND created_at >= ?',
                (session['user_id'], month_start)
            ).fetchone()[0]
            conn.close()
            if count >= 1:
                return render_template('individual_dashboard.html', user=get_current_user(),
                    errors=['Free plan allows 1 assessment/month. <a href="/pricing">Upgrade your plan</a> for unlimited.'])


        flights_raw = request.form.get("flights_per_year", "0")

        flight_mapping = {
            "0": "none",
            "1": "domestic",
            "2": "international",
            "3": "frequent"
        }

        mapped_flight_type = flight_mapping.get(flights_raw, "none")
        # Get form data
        form_data = {
            'country': request.form.get('country', '').strip(),
            'household_size': request.form.get('household_size', '1').strip(),
            'electricity_kwh': request.form.get('electricity_kwh', '0').strip(),
            'energy_source': request.form.get('energy_source', 'grid').strip(),
            'vehicle_type': request.form.get('vehicle_type', 'none').strip(),
            'vehicle_km': request.form.get('vehicle_km', '0').strip(),
            'flight_type': mapped_flight_type,
            'public_transport': request.form.get('public_transport', 'sometimes').strip(),
            'diet_type': request.form.get('diet_type', 'mixed').strip(),
            'shopping_freq': request.form.get('shopping_freq', 'medium').strip(),
            'recycling': request.form.get('recycling', 'no').strip(),
            'home_type': request.form.get('home_type', 'apartment').strip(),
            'heating_source': request.form.get('heating_source', 'electric').strip(),
            'meat_frequency': request.form.get('meat_frequency', '3').strip(),
            'food_waste': request.form.get('food_waste', 'rarely').strip(),
            'vehicle_efficiency': request.form.get('vehicle_efficiency', '15').strip(),
            'renewable_percent': request.form.get('renewable_percent', '0').strip()
        }
        
        # Validate inputs
        errors = validate_individual_input(form_data)
        
        if errors:
            return render_template('individual_dashboard.html', 
                                  user=user, 
                                  errors=errors,
                                  form_data=form_data)
        
        # Convert to proper types
        try:
            inputs = {
                'country': form_data['country'],
                'household_size': int(form_data['household_size']),
                'electricity_kwh': float(form_data['electricity_kwh']),
                'energy_source': form_data['energy_source'],
                'vehicle_type': form_data['vehicle_type'],
                'vehicle_km': float(form_data['vehicle_km']),
                'flight_type': form_data['flight_type'],
                'public_transport': form_data['public_transport'],
                'diet_type': form_data['diet_type'],
                'shopping_freq': form_data['shopping_freq'],
                'recycling': form_data['recycling'],
                'home_type': form_data['home_type'],
                'heating_source': form_data['heating_source'],
                'meat_frequency': int(form_data['meat_frequency']),
                'food_waste': form_data['food_waste'],
                'vehicle_efficiency': float(form_data['vehicle_efficiency']) if form_data['vehicle_efficiency'] else 15.0,
                'renewable_percent': float(form_data['renewable_percent']),

            }
        except ValueError as e:
            errors = [f"Invalid number format: {str(e)}"]
            return render_template('individual_dashboard.html', 
                                  user=user, 
                                  errors=errors,
                                  form_data=form_data)
        
        # Calculate carbon footprint
        result = calculator.calculate_individual_footprint(inputs)
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO individual_assessments 
            (user_id, country, electricity_kwh, vehicle_type, vehicle_km, 
             flight_type, diet_type, shopping_freq, recycling, 
             carbon_footprint, carbon_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user['id'],
            inputs['country'],
            inputs['electricity_kwh'],
            inputs['vehicle_type'],
            inputs['vehicle_km'],
            inputs['flight_type'],
            inputs['diet_type'],
            inputs['shopping_freq'],
            inputs['recycling'],
            result['total_footprint'],
            result['carbon_level']
        ))
        
        assessment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Store result in session for display
        session['last_calculation'] = {
            'inputs': inputs,
            'result': result,
            'assessment_id': assessment_id
        }
        
        return redirect(url_for('show_result'))
    
    return render_template('individual_dashboard.html', user=user)

@app.route('/calculate/enterprise', methods=['GET', 'POST'])
def calculate_enterprise():
    """Enterprise ESG assessment"""
    if not is_logged_in():
        return redirect(url_for('login'))
    
    user = get_current_user()
    if user['user_type'] != 'enterprise':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Validate inputs
        errors = validate_enterprise_input(request.form)
        
        if errors:
            return render_template('enterprise_dashboard.html', 
                                  user=user, 
                                  errors=errors,
                                  form_data=request.form)
        
        # Calculate ESG score
        inputs = {
            'company_name': request.form['company_name'],
            'industry': request.form['industry'],
            'employees': int(request.form['employees']),
            'energy_usage': float(request.form['energy_usage']),
            'travel_km': float(request.form['travel_km']),
            'cloud_usage': request.form['cloud_usage'],
            'waste_management': int(request.form['waste_management'])
        }
        
        result = esg_calculator.calculate_esg_score(inputs)
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO enterprise_assessments 
            (user_id, company_name, industry, employees, energy_usage, 
             travel_km, cloud_usage, waste_management,
             emissions_per_employee, energy_intensity, esg_score, esg_risk)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user['id'],
            inputs['company_name'],
            inputs['industry'],
            inputs['employees'],
            inputs['energy_usage'],
            inputs['travel_km'],
            1 if inputs['cloud_usage'] == 'yes' else 0,
            inputs['waste_management'],
            result['emissions_per_employee'],
            result['energy_intensity'],
            result['total_score'],
            result['esg_risk']
        ))
        
        assessment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Store result in session
        session['last_esg_calculation'] = {
            'inputs': inputs,
            'result': result,
            'assessment_id': assessment_id
        }
        
        return redirect(url_for('show_esg_result'))
    
    return render_template('enterprise_dashboard.html', user=user)

@app.route('/result')
def show_result():
    """Show individual calculation result"""
    if not is_logged_in() or 'last_calculation' not in session:
        return redirect(url_for('dashboard'))
    
    user = get_current_user()
    calculation = session['last_calculation']
    
    # Make sure ml_prediction exists in the result
    if 'ml_prediction' not in calculation['result']:
        calculation['result']['ml_prediction'] = 0
    
    return render_template('result.html', 
                          user=user,
                          inputs=calculation['inputs'],
                          result=calculation['result'])

@app.route('/esg-result')
def show_esg_result():
    """Show ESG calculation result"""
    if not is_logged_in() or 'last_esg_calculation' not in session:
        return redirect(url_for('dashboard'))
    
    user = get_current_user()
    calculation = session['last_esg_calculation']
    
    # Ensure all required fields exist
    if 'recommendations' not in calculation['result']:
        calculation['result']['recommendations'] = []
    
    return render_template('result.html', 
                          user=user,
                          inputs=calculation['inputs'],
                          result=calculation['result'],
                          is_esg=True)

@app.route('/generate-report/<report_type>')
def generate_report(report_type):
    """Generate and download PDF report"""
    if not is_logged_in():
        return redirect(url_for('login'))
    
    user = get_current_user()
    
    if report_type == 'individual' and 'last_calculation' in session:
        calculation = session['last_calculation']
        buffer = pdf_gen.generate_individual_report(user, calculation['result'])
        
        # Save report record to database
        filename = f"Carbon_Report_{user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO reports (user_id, report_type, file_path) VALUES (?, ?, ?)',
            (user['id'], 'individual', filename)
        )
        conn.commit()
        conn.close()
        
        return send_file(buffer, 
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
    
    elif report_type == 'enterprise' and 'last_esg_calculation' in session:
        calculation = session['last_esg_calculation']
        buffer = pdf_gen.generate_enterprise_report(user, 
                                                     calculation['result'],
                                                     calculation['inputs'])
        
        # Save report record
        filename = f"ESG_Report_{user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO reports (user_id, report_type, file_path) VALUES (?, ?, ?)',
            (user['id'], 'enterprise', filename)
        )
        conn.commit()
        conn.close()
        
        return send_file(buffer,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
    
    elif report_type == 'certificate':
        filename = f"Certificate_{user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        # Determine what type of certificate to generate
        if user['user_type'] == 'individual' and 'last_calculation' in session:
            score = session['last_calculation']['result']['total_footprint']
            # Convert footprint to score (inverse)
            cert_score = max(0, 100 - (score / 200))
            buffer = pdf_gen.generate_certificate(user, 
                                                   'Carbon Footprint Assessment',
                                                   round(cert_score, 1))
        elif user['user_type'] == 'enterprise' and 'last_esg_calculation' in session:
            score = session['last_esg_calculation']['result']['total_score']
            buffer = pdf_gen.generate_certificate(user,
                                                   'ESG Readiness Assessment',
                                                   score)
        else:
            return redirect(url_for('dashboard'))
        
        return send_file(buffer,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='application/pdf')
    
    return redirect(url_for('dashboard'))

@app.route('/reports')
def view_reports():
    """View generated reports"""
    if not is_logged_in():
        return redirect(url_for('login'))
    
    user = get_current_user()
    
    conn = get_db_connection()
    reports = conn.execute(
        '''SELECT * FROM reports 
           WHERE user_id = ? ORDER BY generated_at DESC''',
        (user['id'],)
    ).fetchall()
    conn.close()
    
    return render_template('reports.html', user=user, reports=reports)

@app.route('/api/countries')
def get_countries():
    """API endpoint to get available countries"""
    # Simplified list - you can expand this
    countries = [
        'USA', 'UK', 'Canada', 'Australia', 'Germany', 'France',
        'India', 'China', 'Japan', 'Brazil', 'South Africa'
    ]
    return jsonify(countries)

# ------------------------------------------------------------
# ERROR HANDLERS
# ------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


# ------------------------------------------------------------
# PRICING & SUBSCRIPTION ROUTES
# ------------------------------------------------------------

PLAN_FEATURES = {
    'free':        {'assessments_per_month': 1, 'pdf_export': False, 'history_months': 0, 'personalized_tips': False, 'advanced_analytics': False, 'family_accounts': False, 'esg_reports': False},
    'eco-starter': {'assessments_per_month': None, 'pdf_export': True,  'history_months': 6, 'personalized_tips': True,  'advanced_analytics': False, 'family_accounts': False, 'esg_reports': False},
    'eco-pro':     {'assessments_per_month': None, 'pdf_export': True,  'history_months': 12, 'personalized_tips': True,  'advanced_analytics': True,  'family_accounts': True,  'esg_reports': False},
    'business':    {'assessments_per_month': None, 'pdf_export': True,  'history_months': 24, 'personalized_tips': True,  'advanced_analytics': True,  'family_accounts': True,  'esg_reports': True},
}

@app.route('/pricing')
def pricing():
    current_plan = 'free'
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute('SELECT subscription_plan FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        if user:
            current_plan = user['subscription_plan'] or 'free'
    return render_template('pricing.html', current_plan=current_plan)

@app.route('/subscribe/<plan>')
def subscribe(plan):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    valid_plans = ['free', 'eco-starter', 'eco-pro', 'business']
    if plan not in valid_plans:
        return redirect(url_for('pricing'))
    conn = get_db_connection()
    conn.execute('UPDATE users SET subscription_plan = ?, plan_updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                 (plan, session['user_id']))
    conn.commit()
    conn.close()
    session['subscription_plan'] = plan
    flash(f'Plan updated to {plan.title()}! (Developer Mode)', 'success')
    return redirect(url_for('pricing'))


# ------------------------------------------------------------
# RUN APPLICATION
# ------------------------------------------------------------

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('static/reports', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    print("Starting Carbon ESG Platform...")
    print("Open your browser and go to: http://localhost:5000")
    debug_mode = app.config.get('DEBUG', False)
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)