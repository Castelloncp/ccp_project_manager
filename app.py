import os
from flask import Flask
from config import Config
from models import db, User
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None

# register blueprints
from auth import auth_bp
from projects import projects_bp
from users import users_bp
from files import files_bp
from audit import audit_bp

app.register_blueprint(auth_bp)
app.register_blueprint(projects_bp, url_prefix='/projects')
app.register_blueprint(users_bp)
app.register_blueprint(files_bp)
app.register_blueprint(audit_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
