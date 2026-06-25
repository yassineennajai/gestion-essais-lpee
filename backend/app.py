import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_cors import CORS
from datetime import timedelta 
from flask_jwt_extended import JWTManager 

# استيراد الكائنات المشتركة بشكل نقي لتجنب الـ Circular Import
from extensions import db, socketio

from routes.routes_auth import auth_bp
from routes.routes_utilisateurs import utilisateurs_bp
from routes.routes_essais import essais_bp
from routes.routes_unites import unites_bp
from routes.routes_familles import familles_bp
from routes.routes_normes import normes_bp   
from routes.routes_dashboard import dashboard_bp 

from routes.routes_villes import routes_villes
from routes.routes_domaines import routes_domaines
from routes.routes_grandeurs import routes_grandeurs

app = Flask(__name__)

CORS(app, resources={r"/*": {
    "origins": ["http://localhost:4200"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization", "X-User-Role", "X-User-Unite"]
}}, supports_credentials=True)

app.config['SECRET_KEY'] = 'LPEE_CEMGI_LABORATOIRE_SECRET_KEY_2026_PRODUCTION'
app.config['JWT_SECRET_KEY'] = 'LPEE_CEMGI_LABORATOIRE_JWT_SECRET_KEY_2026_SECURE'

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:lpee@localhost/laboratoire'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تهيئة الـ socketio المستورد من extensions
socketio.init_app(
    app, 
    cors_allowed_origins="http://localhost:4200", 
    async_mode='eventlet',
    logger=True,
    engineio_logger=True
)

jwt = JWTManager(app)
db.init_app(app)

with app.app_context():
    import models
    db.create_all()

# تسجيل الـ Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(utilisateurs_bp)
app.register_blueprint(essais_bp)
app.register_blueprint(unites_bp)
app.register_blueprint(familles_bp)
app.register_blueprint(normes_bp)
app.register_blueprint(dashboard_bp)

app.register_blueprint(routes_villes)
app.register_blueprint(routes_domaines)
app.register_blueprint(routes_grandeurs)

@socketio.on('connect')
def handle_connect():
    print("Un client Angular s'est connecté au serveur WebSocket.")

@socketio.on('disconnect')
def handle_disconnect():
    print("Un client Angular s'est déconnecté du serveur WebSocket.")

if __name__ == '__main__':
    socketio.run(
        app,
        debug=True,
        host='0.0.0.0',
        port=5000
    )