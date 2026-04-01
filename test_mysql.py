import mysql.connector

try:
    print("🔹 Attempting to connect to MySQL...")
    conn = mysql.connector.connect(
        host="127.0.0.1",
        port=3307,
        user="root",
        password="",  # leave empty if no root password
        use_pure =  True #rare case
    )
    print("✅ Connected to MySQL!")
    conn.close()

except mysql.connector.Error as e:
    print("❌ MySQL ERROR:", e)

except Exception as e:
    print("❌ OTHER ERROR:", e)