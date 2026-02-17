import sqlite3

# Create database and tables
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")

# Create projects table
cursor.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    price REAL NOT NULL,
    image TEXT,
    client TEXT,
    contact TEXT,
    rating REAL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

# Create reviews table
cursor.execute("""
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    client_name TEXT,
    review TEXT,
    rating REAL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
)
""")

conn.commit()
conn.close()

print("Database initialized successfully!")
