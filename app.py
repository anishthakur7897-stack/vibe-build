from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = "handloom_secret_key"

# Upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # USERS TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # PRODUCTS TABLE
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


# ---------------- HOME PAGE ---------------- #

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
            conn = sqlite3.connect("database.db")
            c = conn.cursor()

            c.execute("""
                INSERT INTO users
                (name, email, password, role)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                email,
                hashed_password,
                role
            ))

            conn.commit()
            conn.close()

            flash(
                "Registration Successful!",
                "success"
            )

            return redirect("/login")

        except sqlite3.IntegrityError:

            flash(
                "Email already exists!",
                "danger"
            )

            return redirect("/register")

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        )

        user = c.fetchone()
        conn.close()

        if user and check_password_hash(
            user[3],
            password
        ):

            session["user_id"] = user[0]
            session["username"] = user[1]
            session["role"] = user[4]

            # Role Redirect
            if user[4] == "admin":
                return redirect("/admin")

            elif user[4] == "seller":
                return redirect("/seller")

            elif user[4] == "buyer":
                return redirect("/buyer")

        else:
            flash(
                "Invalid Email or Password",
                "danger"
            )

    return render_template("login.html")


# ---------------- ADMIN ---------------- #

@app.route("/admin")
def admin_dashboard():

    if (
        "role" not in session
        or session["role"] != "admin"
    ):
        return redirect("/login")

    return render_template(
        "admin_dashboard.html",
        username=session["username"]
    )


# ---------------- SELLER ---------------- #

@app.route("/seller")
def seller_dashboard():

    if (
        "role" not in session
        or session["role"] != "seller"
    ):
        return redirect("/login")

    return render_template(
        "seller_dashboard.html",
        username=session["username"]
    )


# ---------------- BUYER ---------------- #

@app.route("/buyer")
def buyer_dashboard():

    if (
        "role" not in session
        or session["role"] != "buyer"
    ):
        return redirect("/login")

    return render_template(
        "buyer_dashboard.html",
        username=session["username"]
    )


# ---------------- PRODUCT UPLOAD ---------------- #

@app.route(
    "/upload-product",
    methods=["GET", "POST"]
)
def upload_product():

    if (
        "role" not in session
        or session["role"] != "seller"
    ):
        return redirect("/login")

    if request.method == "POST":

        product_name = request.form[
            "product_name"
        ]

        description = request.form[
            "description"
        ]

        price = request.form["price"]

        category = request.form[
            "category"
        ]

        image = request.files["image"]

        filename = secure_filename(
            image.filename
        )

        image_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )

        image.save(image_path)

        conn = sqlite3.connect(
            "database.db"
        )

        c = conn.cursor()

        c.execute("""
            INSERT INTO products
            (
                seller_name,
                product_name,
                description,
                price,
                category,
                image
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session["username"],
            product_name,
            description,
            price,
            category,
            filename
        ))

        conn.commit()
        conn.close()

        flash(
            "Product Uploaded Successfully!",
            "success"
        )

        return redirect("/seller")

    return render_template(
        "upload_product.html"
    )
@app.route("/products")
def products():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM products"
    )

    products = cursor.fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=products
    )

@app.route("/my-products")
def my_products():

    if "role" not in session or session["role"] != "seller":
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT * FROM products WHERE seller_name=?",
        (session["username"],)
    )

    items = c.fetchall()

    conn.close()

    return render_template("my_products.html", products=items)

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged out successfully!",
        "info"
    )

    return redirect("/")

@app.route("/test")
def test():
    return "Flask is working!"


# ---------------- RUN APP ---------------- #

if __name__ == "__main__":

    init_db()

    app.run(debug=True)