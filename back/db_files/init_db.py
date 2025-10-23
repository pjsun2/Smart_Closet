import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_closet.db')

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            User_id INTEGER PRIMARY KEY AUTOINCREMENT,
            User_email TEXT NOT NULL UNIQUE,
            User_password TEXT NOT NULL,
            User_nickname TEXT NOT NULL,
            User_createDate DATE NOT NULL,
            User_updateDate DATE NOT NULL,
            User_gender TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clothing_information (
            CI_id INTEGER PRIMARY KEY AUTOINCREMENT,
            User_id INTEGER NOT NULL,
            CI_imageURL TEXT NOT NULL,
            CI_mainCategory TEXT NOT NULL,
            CI_subCategory TEXT NOT NULL,
            CI_createDate DATE NOT NULL,
            CI_check INTEGER NOT NULL,
            FOREIGN KEY (User_id) REFERENCES User(User_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attributes (
            A_id INTEGER PRIMARY KEY AUTOINCREMENT,
            A_name TEXT NOT NULL UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clothing_attributes (
            CA_id INTEGER PRIMARY KEY AUTOINCREMENT,
            CI_id INTEGER NOT NULL,
            A_id INTEGER NOT NULL,
            CA_value TEXT NOT NULL,
            CA_updateDate DATE NOT NULL,
            FOREIGN KEY (CI_id) REFERENCES clothing_information(CI_id),
            FOREIGN KEY (A_id) REFERENCES attributes(A_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == '__main__':
    init_database()