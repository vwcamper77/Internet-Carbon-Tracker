import os
import sqlite3
import datetime

# Log function to display and track any errors
def log_error(message):
    print(f"Error: {message}")
    log_folder = os.path.join(os.path.expanduser('~'), 'Documents', 'CO2_Tracker', 'logs')
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    log_path = os.path.join(log_folder, 'error_log.txt')
    with open(log_path, 'a') as error_file:
        error_file.write(f"{datetime.datetime.now()}: {message}\n")

# Function to initialize the database
def init_database():
    try:
        # Create the folder in the user's documents if it doesn't exist
        documents_folder = os.path.join(os.path.expanduser('~'), 'Documents', 'CO2_Tracker')
        if not os.path.exists(documents_folder):
            os.makedirs(documents_folder)
            print(f"Created folder at {documents_folder}")
        
        # Path to the database
        db_path = os.path.join(documents_folder, 'co2_usage.db')
        
        # Check if the path is correct
        print(f"Database path: {db_path}")
        
        # Attempt to connect to the database and create tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create necessary tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS network_usage (
                timestamp TEXT,
                data_sent REAL,
                data_received REAL,
                total_usage REAL,
                daily_usage REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS start_date (
                start_date TEXT
            )
        ''')

        # Commit changes and close the connection
        conn.commit()
        conn.close()
        print("Database initialized successfully!")

    except Exception as e:
        log_error(f"Error initializing database: {str(e)}")

# Run the database initialization function
init_database()
