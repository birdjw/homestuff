from flask import Flask, jsonify, render_template
from flask_login import login_required

from .config import load_config
from .extensions import init_extensions, db
from .routes.items import bp as items_bp
from .routes.restock import bp as restock_bp
from .routes.storage_areas import bp as storage_areas_bp
from .routes.vendors import bp as vendors_bp
from .routes.auth import bp as auth_bp


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or load_config())

    init_extensions(app)
    register_blueprints(app)
    register_cli(app)

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "app": app.config.get("APP_NAME", "HomeStuff")})

    @app.route("/")
    @login_required
    def index():
        return render_template("index.html", app_name=app.config.get("APP_NAME", "HomeStuff"))

    @app.route("/storage-areas-ui")
    @login_required
    def storage_areas_ui():
        return render_template("storage_areas.html", app_name=app.config.get("APP_NAME", "HomeStuff"))

    @app.route("/items-ui")
    @login_required
    def items_ui():
        return render_template("items.html", app_name=app.config.get("APP_NAME", "HomeStuff"))

    @app.route("/vendors-ui")
    @login_required
    def vendors_ui():
        return render_template("vendors.html", app_name=app.config.get("APP_NAME", "HomeStuff"))

    @app.route("/restock-ui")
    @login_required
    def restock_ui():
        return render_template("restock.html", app_name=app.config.get("APP_NAME", "HomeStuff"))
    return app


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(storage_areas_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(restock_bp)
    app.register_blueprint(vendors_bp)


def register_cli(app):
    @app.shell_context_processor
    def make_shell_context():
        # Expose db and models in `flask shell`
        from . import models

        return {"db": db, "models": models}
