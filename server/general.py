
from flask import Blueprint, jsonify, request, make_response
from flask_restful import Api, Resource
from models import Product, Category, Role, Order, OrderItem
from werkzeug.exceptions import NotFound
from config import cloudinary


# Create a Blueprint
general_bp = Blueprint('general', __name__, url_prefix='/shopit')
general_api = Api(general_bp)


class RolesResource(Resource):
    def get(self):
        roles = [role.to_dict() for role in Role.query.all()]
        return roles

class ListProducts(Resource):
    def get(self):
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        paginated_products = Product.query.paginate(page=page, per_page=per_page, error_out=False)
        products = paginated_products.items
        total_items = paginated_products.total
        total_pages = paginated_products.pages

        products_list = [
            {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "category_id": product.category_id,
                "image_url": product.image_url,
                "seller_id": product.seller_id
            } 
            for product in products
        ]

        return jsonify({
            'products': products_list,
            'meta': {
                'page': page,
                'per_page': per_page,
                'total_items': total_items,
                'total_pages': total_pages
            }
        })

class GetProduct(Resource):
    def get(self, product_id):
        product = Product.query.get(product_id)
        if product is None:
            raise NotFound("Product not found")
        product_data = {
            "id": product.id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "category_id": product.category_id,
            "image_url": product.image_url,
            "seller_id": product.seller_id
        }
        return product_data, 200

class ListCategories(Resource):
    def get(self):
        categories = Category.query.all()
        categories_list = [category.to_dict() for category in categories]
        return categories_list

class ProductsByCategory(Resource):
    def get(self, category_id):
        category = Category.query.get(category_id)
        if category is None:
            raise NotFound("Category not found")

        products = Product.query.filter_by(category_id=category_id).all()
        products_list = [
            {
                "id": product.id,
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "category_id": product.category_id,
                "image_url": product.image_url,
                "seller_id": product.seller_id
            }
            for product in products
        ]
        return products_list, 200

class OrderResource(Resource):
    def get(self, order_id):
        try:
            # Fetch the order with its related order items and shipping address
            order = Order.query.filter_by(id=order_id).first_or_404()
            
            # Construct response with order items and shipping address
            order_items = [
                {
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'price': item.price,
                    'product': {
                        'title': item.product.title,
                        'image_url': item.product.image_url
                    }
                }
                for item in order.order_items
            ]
            
            shipping_address = None
            if order.shipping_address:
                shipping_address = {
                    'address': order.shipping_address.address,
                    'city': order.shipping_address.city,
                    'country': order.shipping_address.country
                }
            
            response = {
                'order_id': order.id,
                'buyer_id': order.buyer_id,
                'total_price': order.total_price,
                'status': order.status,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'shipping_address': shipping_address,
                'order_items': order_items
            }
            
            return make_response(jsonify(response), 200)
        
        except Exception as e:
            return {'error': str(e)}, 500


class TestResource(Resource):
    def get(self):
        return jsonify({"message": "Test endpoint is working!"})

general_api.add_resource(TestResource, '/test')

# Add resources to the API
general_api.add_resource(RolesResource, '/roles')
general_api.add_resource(ListProducts, '/products')
general_api.add_resource(GetProduct, '/products/<int:product_id>')
general_api.add_resource(ListCategories, '/categories')
general_api.add_resource(ProductsByCategory, '/categories/<int:category_id>/products')
general_api.add_resource(OrderResource, '/order/<int:order_id>')



