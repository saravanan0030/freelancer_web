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
    status TEXT DEFAULT 'pending',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

# Add status column if it doesn't exist
try:
    cursor.execute("ALTER TABLE projects ADD COLUMN status TEXT DEFAULT 'pending'")
except sqlite3.OperationalError:
    pass  # Column already exists

# Add created_date column if it doesn't exist
try:
    cursor.execute("ALTER TABLE projects ADD COLUMN created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
except sqlite3.OperationalError:
    pass  # Column already exists

conn.commit()
conn.close()

print("Database initialized successfully!")
