from flask import Blueprint, jsonify, make_response
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token, JWTManager, get_jwt, current_user
from models import db, User, Role, Admin
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from functools import wraps
from datetime import timedelta

JWT_BLACKLIST_ENABLED = True
JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']

auth_bp = Blueprint('auth', __name__, url_prefix='/shopit')
bcrypt = Bcrypt()
jwt = JWTManager()
auth_api = Api(auth_bp)

# JWT blacklist
blacklist = set()

# Argument parsers
role_parser = reqparse.RequestParser()
register_parser = reqparse.RequestParser()
login_parser = reqparse.RequestParser()

register_parser.add_argument('first_name', type=str, required=True, help='First name is required')
register_parser.add_argument('last_name', type=str, required=True, help='Last name is required')
register_parser.add_argument('username', type=str, required=True, help='Username is required')
register_parser.add_argument('email', type=str, required=True, help='Email is required')
register_parser.add_argument('password', type=str, required=True, help='Password is required')
register_parser.add_argument('role_id', type=int, required=True, help='Role ID is required')

login_parser.add_argument('email', type=str, required=True, help='Email is required')
login_parser.add_argument('password', type=str, required=True, help='Password is required')

admin_login_parser = reqparse.RequestParser()
admin_login_parser.add_argument('email', type=str, required=True, help='Email is required')
admin_login_parser.add_argument('password', type=str, required=True, help='Password is required')



@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    return jwt_payload['jti'] in blacklist

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).first()

def allow(*allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            user = get_jwt_identity()
            user = User.query.get(user)
            roles = [user.role.name]
            for role in allowed_roles:
                if role in roles:
                    return fn(*args, **kwargs)
            return jsonify({"msg": "Access Denied"}), 403
        return decorator
    return wrapper


class UserRolesResource(Resource):
    def get(self):
        roles = Role.query.filter(Role.name.in_(["Buyer", "Seller"])).all()
        roles_data = [{"id": role.id, "name": role.name} for role in roles]
        return jsonify(roles_data)



class RegisterResource(Resource):
    def post(self):
        args = register_parser.parse_args()
        role = Role.query.get(args['role_id'])
        if not role:
            return jsonify({"error": "Invalid role_id"}), 400

        if User.query.filter_by(username=args['username']).first() or User.query.filter_by(email=args['email']).first():
            return jsonify({"error": "Username or email already exists"}), 400

        hashed_password = generate_password_hash(args['password'], method='pbkdf2:sha256')
        user = User(first_name=args['first_name'], last_name=args['last_name'], username=args['username'], email=args['email'], password=hashed_password, role_id=args['role_id'])

        db.session.add(user)
        db.session.commit()

        return {"message": "User registered successfully"}, 201

class LoginResource(Resource):
    def post(self):
        args = login_parser.parse_args()
        user = User.query.filter_by(email=args['email']).first()

        if not user:
            return {"msg": "User does not exist in our database"}, 404

        print(f"Stored password hash: {user.password}")
        print(f"Provided password: {args['password']}")

        if not check_password_hash(user.password, args['password']):
            return {"msg": "Password is incorrect!"}, 401

        token = create_access_token(identity=user.id,expires_delta=timedelta(days=7))
        refresh_token = create_refresh_token(identity=user.id)

        role = {
            "id": user.role.id,
            "name": user.role.name
        }

        return {
            "token": token,
            "refresh_token": refresh_token,
            "role": role
        }, 200
class AdminRegisterResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('first_name', type=str, required=True, help='First name is required')
        self.parser.add_argument('last_name', type=str, required=True, help='Last name is required')
        self.parser.add_argument('username', type=str, required=True, help='Username is required')
        self.parser.add_argument('email', type=str, required=True, help='Email is required')
        self.parser.add_argument('password', type=str, required=True, help='Password is required')

    def post(self):
        args = self.parser.parse_args()

        # Check if admin already exists
        existing_admin = Admin.query.filter_by(email=args['email']).first()
        if existing_admin:
            return {"msg": "Admin already exists"}, 400

        # Hash the password
        hashed_password = generate_password_hash(args['password'], method='pbkdf2:sha256')

        # Fetch role_id for admin (assuming role name is 'Admin')
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            return {"msg": "Admin role not found"}, 404

        # Create new admin
        new_admin = Admin(
            first_name=args['first_name'],
            last_name=args['last_name'],
            username=args['username'],
            email=args['email'],
            password=hashed_password,
            role_id=admin_role.id
        )

        db.session.add(new_admin)
        db.session.commit()

        return {"msg": "Admin registered successfully"}, 201

class AdminLoginResource(Resource):
    def post(self):
        args = admin_login_parser.parse_args()
        admin = Admin.query.filter_by(email=args['email']).first()

        if not admin:
            return {"msg": "Admin does not exist in our database"}, 404

        if not check_password_hash(admin.password, args['password']):
            return {"msg": "Password is incorrect!"}, 401

        token = create_access_token(identity=admin.id)
        refresh_token = create_refresh_token(identity=admin.id)

        return {
            "token": token,
            "refresh_token": refresh_token
        }, 200

class LogoutResource(Resource):
    @jwt_required()
    def post(self):
        try:
            jti = get_jwt()['jti']
            blacklist.add(jti)
            return make_response(jsonify({"msg": "Successfully logged out"}), 200)
        except Exception as e:
            return make_response(jsonify({"msg": str(e)}), 422)

    
class RefreshResource(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        # Generate a new access token
        new_token = create_access_token(identity=current_user)
        return jsonify(access_token=new_token)


class ChangePassword(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('current_password', type=str, required=True, help='Current password is required')
        self.parser.add_argument('new_password', type=str, required=True, help='New password is required')
        self.parser.add_argument('confirm_new_password', type=str, required=True, help='Password confirmation is required')

    @jwt_required()
    def post(self):
        args = self.parser.parse_args()
        current_password = args['current_password']
        new_password = args['new_password']
        confirm_new_password = args['confirm_new_password']
        
        # Validate new passwords match
        if new_password != confirm_new_password:
            return jsonify({"error": "New passwords do not match."}), 400
        
        # Get the current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404
        
        # Check current password
        if not check_password_hash(user.password, current_password):
            return jsonify({"error": "Current password is incorrect."}), 400
        
        # Update password
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({"message": "Password updated successfully."})
    
class CheckAuthStatus(Resource):
    @jwt_required()
    def get(self):
        # Get the identity of the current user
        current_user_id = get_jwt_identity()

        # Fetch the user from the database
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'message': 'User not found',
            }), 404

        # Assuming the user has a role attribute that is a relationship to a Role model
        user_role = user.role.name if user.role else 'No role assigned'

        return jsonify({
            'message': 'User is authenticated',
            'user': {
                'id': user.id,
                'email': user.email,
                'role': user_role
            }
        })

auth_api.add_resource(UserRolesResource, '/roles')
auth_api.add_resource(RegisterResource, '/register')
auth_api.add_resource(LoginResource, '/login')
auth_api.add_resource(AdminRegisterResource, '/admin_register')
auth_api.add_resource(AdminLoginResource, '/admin_login')
auth_api.add_resource(LogoutResource, '/logout')
auth_api.add_resource(RefreshResource, '/refresh')
auth_api.add_resource(ChangePassword, '/change-password')
auth_api.add_resource(CheckAuthStatus, '/check_token')