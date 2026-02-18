import os
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash
)
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, set_access_cookies, unset_jwt_cookies
)

from config import Config
from models import db, User, LoginHistory
from ml_model import predict_anomaly, train_model


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Ensure instance folder exists for SQLite DB
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def encode_ip(ip_address: str) -> int:
    """
    Convert last 2 digits of the last IPv4 octet into an integer.
    Example: '192.168.1.45' -> 45
    """
    try:
        last_octet = ip_address.split(".")[-1]
        last_two_chars = last_octet[-2:]  # handles 1-digit as well
        return int(last_two_chars)
    except Exception:
        return 0


def encode_device(user_agent: str) -> int:
    """
    Map device types to integers based on the user-agent.
    Example mapping (simple heuristic):
        0 -> desktop
        1 -> mobile
        2 -> tablet
        3 -> other
    """
    ua = (user_agent or "").lower()
    if "mobile" in ua and "tablet" not in ua:
        return 1
    if "tablet" in ua or "ipad" in ua:
        return 2
    if "windows" in ua or "macintosh" in ua or "linux" in ua:
        return 0
    return 3


def register_routes(app: Flask) -> None:
    @app.route("/")
    def index():
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Email and password are required.", "danger")
                return redirect(url_for("register"))

            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash("User with this email already exists.", "warning")
                return redirect(url_for("register"))

            user = User(email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("login.html", is_register=True)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            user = User.query.filter_by(email=email).first()
            if user is None or not user.check_password(password):
                flash("Invalid email or password.", "danger")
                return redirect(url_for("login"))

            # Extract behavioral features
            now = datetime.utcnow()
            login_hour = now.hour
            ip_address = request.headers.get("X-Forwarded-For", request.remote_addr) or ""
            ip_encoded = encode_ip(ip_address)
            user_agent = request.headers.get("User-Agent", "")
            device_encoded = encode_device(user_agent)

            login_features = [login_hour, ip_encoded, device_encoded]

            # Train model (if enough history) and predict anomaly
            # Note: predict_anomaly internally checks for min 10 logins
            is_suspicious = predict_anomaly(user.id, login_features)

            # Save login history
            history = LoginHistory(
                user_id=user.id,
                login_hour=login_hour,
                ip_encoded=ip_encoded,
                device_encoded=device_encoded,
                is_suspicious=is_suspicious,
                timestamp=now,
            )
            db.session.add(history)
            db.session.commit()

            # Optionally, retrain model after new data point
            train_model(user.id)

            # Generate JWT and store in cookie
            access_token = create_access_token(identity=str(user.id))
            resp = redirect(url_for("dashboard"))
            set_access_cookies(resp, access_token)

            flash(
                "Login successful, but behavior flagged as suspicious."
                if is_suspicious
                else "Login successful.",
                "warning" if is_suspicious else "success",
            )
            return resp

        return render_template("login.html", is_register=False)

    @app.route("/logout")
    def logout():
        resp = redirect(url_for("login"))
        unset_jwt_cookies(resp)
        flash("Logged out.", "info")
        return resp

    @app.route("/dashboard")
    @jwt_required()
    def dashboard():
        user_id = int(get_jwt_identity())
        total_logins = LoginHistory.query.filter_by(user_id=user_id).count()
        suspicious_logins = (
            LoginHistory.query.filter_by(user_id=user_id, is_suspicious=True).count()
        )

        return render_template(
            "dashboard.html",
            total_logins=total_logins,
            suspicious_logins=suspicious_logins,
        )


app = create_app()

if __name__ == "__main__":
    # For Azure App Service, you typically use gunicorn instead of this block,
    # but this allows local development with: python app.py
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)