import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect("database.db")
c = conn.cursor()

email = "admin@gmail.com"
password = "admin123"
name = "Admin"

hashed = generate_password_hash(password)

# remove old admin if exists
c.execute("DELETE FROM users WHERE email=?", (email,))

# insert new admin
c.execute("""
INSERT INTO users (name, email, password, role)
VALUES (?, ?, ?, ?)
""", (name, email, hashed, "admin"))

conn.commit()
conn.close()

print("ADMIN CREATED SUCCESSFULLY")
print("Email: admin@gmail.com")
print("Password: admin123")