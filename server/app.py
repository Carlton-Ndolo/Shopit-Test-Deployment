from flask import Flask, jsonify
from flask_migrate import Migrate
from auth import auth_bp, jwt, bcrypt
from general import general_bp
from buyer import buyer_bp
from seller import seller_bp
from flask_cors import CORS
from models import db
from admin import admin_bp
import logging

logging.basicConfig(level=logging.DEBUG)


app = Flask(__name__)

app.config['SECRET_KEY'] = '8321ce6cc7de4184bf491894345e73b0'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

# Configure CORS to allow requests from your frontend URL
CORS(app, supports_credentials=True,resources={r"/*": {"origins": "*"}}) # Adjust the origin as needed

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(general_bp)
app.register_blueprint(buyer_bp)
app.register_blueprint(seller_bp)
app.register_blueprint(admin_bp)

bcrypt.init_app(app)
db.init_app(app)
jwt.init_app(app)
migrate = Migrate(app=app, db=db)

@app.route('/')
def hello():
    return 'Hello there!'

@app.route('/debug-cors', methods=['GET'])
def debug_cors():
    response = jsonify({"message": "CORS headers should be visible in the network tab."})
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')  # Adjust if needed
    return response

if __name__ == '__main__':
    app.run(port=5000, debug=True)
