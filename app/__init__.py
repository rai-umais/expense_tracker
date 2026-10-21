import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access your expenses.'
login_manager.login_message_category = 'warning'

def create_app(config_class=Config):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    static_dir = os.path.join(root_dir, 'static')
    app = Flask(__name__, static_folder=static_dir)
    app.config.from_object(config_class)

    # Ensure instance directory exists for SQLite
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.expenses.routes import expenses_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)

    # Initialize tables
    with app.app_context():
        db.create_all()

    return app
