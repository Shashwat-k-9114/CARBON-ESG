import sqlite3
import os

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect('database/carbon_esg.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        user_type TEXT NOT NULL CHECK(user_type IN ('individual', 'enterprise')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create individual assessments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS individual_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        country TEXT,
        electricity_kwh REAL,
        vehicle_type TEXT,
        vehicle_km REAL,
        flight_type TEXT,
        diet_type TEXT,
        shopping_freq TEXT,
        recycling TEXT,
        carbon_footprint REAL,
        carbon_level TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create enterprise assessments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS enterprise_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        company_name TEXT,
        industry TEXT,
        employees INTEGER,
        energy_usage REAL,
        travel_km REAL,
        cloud_usage INTEGER,
        waste_management INTEGER,
        emissions_per_employee REAL,
        energy_intensity REAL,
        esg_score REAL,
        esg_risk TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create reports table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        report_type TEXT,
        file_path TEXT,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def get_db_connection():
    """Get a database connection"""
    conn = sqlite3.connect('database/carbon_esg.db')
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn

if __name__ == '__main__':
    init_db()