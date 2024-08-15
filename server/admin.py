from flask import Blueprint, jsonify, request
from flask_restful import Api, Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Category, User, Admin
from functools import wraps
from config import cloudinary
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/shopit/admin')
admin_api = Api(admin_bp)

# Argument parsers for category creation and update
category_parser = reqparse.RequestParser()
category_parser.add_argument('name', type=str, required=True, help='Category name is required')

update_category_parser = reqparse.RequestParser()
update_category_parser.add_argument('name', type=str, required=False, help='Category name is optional')

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity() 
        admin = Admin.query.get(user_id)  

        if not admin:
            return {"error": "Admin not found"}, 404  
        if admin.role.name != 'Admin': 
            return {"error": "Admin access required"}, 403 

        return fn(*args, **kwargs)  

    return wrapper

class CreateCategoryResource(Resource):
    @jwt_required()
    @admin_required
    def post(self):
        # Handle JSON data or form data
        if request.content_type == 'application/json':
            args = request.get_json() or {}
            category_name = args.get('name', '').strip()
        else:
            category_name = request.form.get('name', '').strip()

        # Log the received values
        logging.debug(f"Received category_name: '{category_name}'")
        logging.debug(f"Form data: {request.form}")

        # Validate category_name
        if not category_name:
            return {"error": "Category name is required and cannot be empty"}, 400

        # Check for existing category with the same name
        if Category.query.filter_by(name=category_name).first():
            return {"error": "Category with this name already exists"}, 400

        # Handle file upload
        image_url = ''
        if 'file' in request.files:
            file = request.files['file']
            if file:
                upload_result = cloudinary.uploader.upload(file)
                image_url = upload_result.get('secure_url')

        # Create the category
        category = Category(name=category_name, image_url=image_url)
        db.session.add(category)
        db.session.commit()

        return {"message": "Category created", "category_id": category.id}, 201


class UpdateCategoryResource(Resource):
    @jwt_required()
    @admin_required
    def put(self, category_id):
        args = update_category_parser.parse_args()
        category = Category.query.get_or_404(category_id)

        # Update fields if provided
        if 'name' in args:
            category.name = args['name']

        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file:
                upload_result = cloudinary.uploader.upload(file)
                category.image_url = upload_result.get('secure_url')

        db.session.commit()
        return {"message": "Category updated", "category_id": category.id}, 200

    
class UpdateCategoryResource(Resource):
    @jwt_required()
    @admin_required
    def put(self, category_id):
        args = update_category_parser.parse_args()
        category = Category.query.get_or_404(category_id)

        # Update fields if provided
        if 'name' in args:
            category.name = args['name']
        # if 'description' in args:
            # category.description = args['description']

        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file:
                upload_result = cloudinary.uploader.upload(file)
                category.image_url = upload_result.get('secure_url')

        db.session.commit()
        return {"message": "Category updated", "category_id": category.id}, 200

admin_api.add_resource(CreateCategoryResource, '/create_category')
admin_api.add_resource(UpdateCategoryResource, '/update_category/<int:category_id>')