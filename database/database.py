import os
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor

DB_URL = os.environ.get('DATABASE_URL')

class DBWrapper:
    """A smart wrapper that switches between local SQLite and Render's PostgreSQL seamlessly."""
    def __init__(self):
        self.is_postgres = bool(DB_URL)
        if self.is_postgres:
            self.conn = psycopg2.connect(DB_URL, cursor_factory=DictCursor)
        else:
            self.conn = sqlite3.connect('database/carbon_esg.db')
            self.conn.row_factory = sqlite3.Row

    def execute(self, query, params=()):
        if self.is_postgres:
            # Convert SQLite '?' placeholders to Postgres '%s'
            query = query.replace('?', '%s')
            
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_db_connection():
    """Get a database connection"""
    return DBWrapper()

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    is_pg = conn.is_postgres
    
    # PostgreSQL uses SERIAL, SQLite uses AUTOINCREMENT
    autoincrement = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    
    # Create users table
    conn.execute(f'''
    CREATE TABLE IF NOT EXISTS users (
        id {autoincrement},
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        user_type TEXT NOT NULL CHECK(user_type IN ('individual', 'enterprise')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        subscription_plan TEXT DEFAULT 'free',
        plan_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create individual assessments table
    conn.execute(f'''
    CREATE TABLE IF NOT EXISTS individual_assessments (
        id {autoincrement},
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
        home_type TEXT,
        heating_source TEXT,
        meat_frequency INTEGER,
        food_waste TEXT,
        vehicle_efficiency REAL,
        renewable_percent REAL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create enterprise assessments table
    conn.execute(f'''
    CREATE TABLE IF NOT EXISTS enterprise_assessments (
        id {autoincrement},
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
    conn.execute(f'''
    CREATE TABLE IF NOT EXISTS reports (
        id {autoincrement},
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

if __name__ == '__main__':
    init_db()