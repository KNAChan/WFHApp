import mysql.connector

DB_CONFIG = {
    "host": "127.0.0.1",    # XAMPP MySQL host
    "port": 3307,           # XAMPP MySQL port (change if needed)
    "user": "root",
    "password": "",
    "use_pure": True        # required for XAMPP
}

DB_NAME = "wfh_app"

def setup():
    # Connect without database
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    conn.close()

    # Connect with database
    conn = mysql.connector.connect(**DB_CONFIG, database=DB_NAME)
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE,
        password VARCHAR(50),
        name VARCHAR(100),
        status VARCHAR(20) DEFAULT 'offline',
        checked_in BOOLEAN DEFAULT FALSE,
        in_call BOOLEAN DEFAULT FALSE,
        last_activity DATETIME
    )
    """)

    # Sample users
    users = [
        ("alice", "123", "Alice"),
        ("bob", "123", "Bob"),
        ("charlie", "123", "Charlie")
    ]

    for u in users:
        try:
            cursor.execute(
                "INSERT INTO users (username, password, name) VALUES (%s,%s,%s)", u
            )
        except mysql.connector.IntegrityError:
            pass  # user exists, skip

    conn.commit()
    cursor.close()
    conn.close()
    print("Database ready")

if __name__ == "__main__":
    setup()