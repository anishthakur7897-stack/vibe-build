from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ================= PRODUCTION FIX =================
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret_key")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_name TEXT,
            product_name TEXT,
            description TEXT,
            price REAL,
            category TEXT,
            image TEXT
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute("""
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, ?)
            """, (name, email, hashed_password, role))

            conn.commit()
            conn.close()

            flash("Registration Successful!", "success")
            return redirect("/login")

        except:
            flash("Email already exists!", "danger")
            return redirect("/register")

    return render_template("register.html")


# ---------------- LOGIN FIXED ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):

            session.clear()

            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[4]
            session["cart"] = []

            if user[4] == "admin":
                return redirect("/admin")
            elif user[4] == "seller":
                return redirect("/seller")
            else:
                return redirect("/buyer")

        flash("Invalid credentials", "danger")

    return render_template("login.html")


# ---------------- ADMIN ---------------- #

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/login")

    return render_template("admin_dashboard.html",
                           username=session.get("username"))


# ---------------- SELLER ---------------- #

@app.route("/seller")
def seller():
    if session.get("role") != "seller":
        return redirect("/login")

    return render_template("seller_dashboard.html",
                           username=session.get("username"))


# ---------------- BUYER ---------------- #

@app.route("/buyer")
def buyer():
    if session.get("role") != "buyer":
        return redirect("/login")

    return render_template("buyer_dashboard.html",
                           username=session.get("username"))


# ---------------- UPLOAD ---------------- #

@app.route("/upload-product", methods=["GET", "POST"])
def upload_product():
    if session.get("role") != "seller":
        return redirect("/login")

    if request.method == "POST":

        product_name = request.form["product_name"]
        description = request.form["description"]
        price = request.form["price"]
        category = request.form["category"]

        image = request.files["image"]
        filename = secure_filename(image.filename)

        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""
            INSERT INTO products
            (seller_name, product_name, description, price, category, image)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session["username"], product_name, description, price, category, filename))

        conn.commit()
        conn.close()

        flash("Product uploaded!", "success")
        return redirect("/seller")

    return render_template("upload_product.html")


# ---------------- PRODUCTS ---------------- #

@app.route("/products")
def products():
    search = request.args.get("search")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    if search:
        c.execute("""
            SELECT * FROM products
            WHERE product_name LIKE ? OR category LIKE ?
        """, (f"%{search}%", f"%{search}%"))
    else:
        c.execute("SELECT * FROM products")

    products = c.fetchall()
    conn.close()

    return render_template("products.html",
                           products=products,
                           search=search)


# ---------------- CART ---------------- #

@app.route("/add-to-cart/<int:product_id>")
def add_to_cart(product_id):

    if "cart" not in session:
        session["cart"] = []

    if product_id not in session["cart"]:
        session["cart"].append(product_id)

    session.modified = True

    flash("Added to cart!", "success")
    return redirect("/products")


@app.route("/cart")
def cart():

    items = []

    if session.get("cart"):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        placeholders = ",".join("?" * len(session["cart"]))

        c.execute(f"""
            SELECT * FROM products WHERE id IN ({placeholders})
        """, session["cart"])

        items = c.fetchall()
        conn.close()

    return render_template("cart.html", products=items)


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- RUN (RENDER FIX) ---------------- #

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=10000)