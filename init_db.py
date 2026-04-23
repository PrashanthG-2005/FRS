import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

def init_db():
    try:
        # Connect without DB to create it
        db = MySQLdb.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            passwd=os.getenv("MYSQL_PASSWORD")
        )
        cursor = db.cursor()
        
        # Create Database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {os.getenv('MYSQL_DB')}")
        print(f"Database '{os.getenv('MYSQL_DB')}' created or already exists.")
        
        # Switch to the database
        db.select_db(os.getenv("MYSQL_DB"))
        
        # Read and execute schema.sql
        with open('schema.sql', 'r') as f:
            sql_commands = f.read().split(';')
            for command in sql_commands:
                if command.strip():
                    try:
                        cursor.execute(command)
                    except Exception as e:
                        print(f"Warning: {e}")
        
        db.commit()
        print("Schema applied successfully.")
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    init_db()
