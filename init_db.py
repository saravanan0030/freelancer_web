import sqlite3

DATABASE = "database.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    print("Initializing database...")

    # -------------------------
    # USERS TABLE
    # -------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)

    # -------------------------
    # PROJECTS TABLE
    # -------------------------
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

    # -------------------------
    # REVIEWS TABLE
    # -------------------------
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

    # -------------------------
    # ADD MISSING COLUMNS SAFELY
    # -------------------------

    # CONTACT column fix
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN contact TEXT")
        print("Added contact column")
    except sqlite3.OperationalError:
        pass

    # STATUS column fix
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN status TEXT DEFAULT 'pending'")
        print("Added status column")
    except sqlite3.OperationalError:
        pass

    # CREATED DATE column fix
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("Added created_date column")
    except sqlite3.OperationalError:
        pass


    conn.commit()
    conn.close()

    print("Database initialized successfully!")


# Run function
if __name__ == "__main__":
    init_db()