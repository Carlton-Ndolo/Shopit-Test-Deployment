#buyer.py
from flask import Blueprint, request, session, make_response, jsonify
from flask_jwt_extended import jwt_required, current_user, get_jwt_identity
from models import db, User, Product, Cart, CartItem, Review, Category, OrderItem, Order, Wishlist, UserAddress, UserPayment
from flask_restful import Api, Resource, reqparse
from datetime import datetime
from auth import allow
from config import cloudinary
from marshmallow import Schema, fields, ValidationError
import stripe

buyer_bp = Blueprint('buyer_bp', __name__, url_prefix = '/shopit/buyer')
buyer_api = Api(buyer_bp)

stripe.api_key = 'sk_test_51Pj5cTAEksgxXJsgAlOZSZzkkgwxFX2YJ1vju3R9F2FYKey9Unhj6r7egYdWEDWGSm94oQ9bt3Ko1a0pqKucqQLu00w9li6Psn'

class AddToCart(Resource):
    @jwt_required()
    @allow('Buyer')
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404

        if product.stock < quantity:
            return jsonify({"error": "Insufficient stock"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()

        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if cart_item:
            if product.stock < (cart_item.quantity + quantity):
                return jsonify({"error": "Insufficient stock"}), 400
            cart_item.quantity += quantity
        else:
            if product.stock < quantity:
                return jsonify({"error": "Insufficient stock"}), 400
            cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity, price=product.price)
            db.session.add(cart_item)

        cart.total_price += product.price * quantity
        product.stock -= quantity

        db.session.commit()

        return make_response(jsonify({"message": "Product added to cart successfully"}), 201)


class DeleteCartItem(Resource):
    @jwt_required()
    @allow('Buyer')
    def delete(self, product_id):
        user_id = get_jwt_identity()  # Get the user ID from the JWT token
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            return jsonify({"error": "Cart not found"}), 404

        # Find the cart item to delete
        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
        if not cart_item:
            return jsonify({"error": "Cart item not found"}), 404
        
        

        # Remove the cart item from the database
        db.session.delete(cart_item)
        db.session.commit()

        return make_response(jsonify({"message": "Item removed from cart successfully"}), 200)


class GetCartResource(Resource):
    @jwt_required()
    @allow('Buyer')
    def get(self):
        user_id = get_jwt_identity()  # Get the user ID from the JWT token
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            return jsonify({"error": "Cart not found"}), 404

        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        cart_items_list = []
        total_price = 0

        for item in cart_items:
            product = Product.query.get(item.product_id)
            if product:
                item_total = item.quantity * product.price
                total_price += item_total
                cart_items_list.append({
                    "product_id": product.id,
                    "title": product.title,
                    "description": product.description,
                    "image": product.image_url,
                    "price": product.price,
                    "quantity": item.quantity,
                    "total_price": item_total
                })

        return jsonify({
            "cart_items": cart_items_list,
            "total_price": total_price
        })

class UpdateCart(Resource):
    @jwt_required()
    @allow('Buyer')
    def put(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.json
        updated_items = data.get('items', [])

        if not updated_items:
            return jsonify({"error": "No items provided"}), 400

        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            return jsonify({"error": "Cart not found"}), 404

        total_price = 0

        for item in updated_items:
            product_id = item.get('product_id')
            new_quantity = item.get('quantity')

            if new_quantity <= 0:
                return jsonify({"error": "Quantity must be greater than zero"}), 400

            cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
            if not cart_item:
                return jsonify({"error": f"Product {product_id} not found in cart"}), 404

            product = Product.query.get(product_id)
            if not product:
                return jsonify({"error": f"Product {product_id} does not exist"}), 404

            # Calculate the difference between new quantity and current quantity
            quantity_diff = new_quantity - cart_item.quantity

            if product.stock < quantity_diff:
                return jsonify({"error": "Insufficient stock"}), 400

            # Update the stock and cart item quantity
            product.stock -= quantity_diff
            cart_item.quantity = new_quantity

            # Calculate the total price
            total_price += new_quantity * product.price

        # Commit all changes at once
        db.session.commit()

        # Update total price of the cart
        cart.total_price = total_price
        db.session.commit()

        return jsonify({
            "message": "Cart updated successfully",
            "total_price": total_price
        })


class Checkout(Resource):
    @jwt_required()
    @allow('Buyer')
    def post(self):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return make_response(jsonify({"error": "User not found"}), 404)

        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart or cart.total_price == 0:
            return make_response(jsonify({"error": "Cart is empty"}), 400)

        data = request.get_json()
        token = data.get('stripe_token')
        shipping_address_id = data.get('shipping_address_id')

        if not token:
            return make_response(jsonify({"error": "Stripe token is required"}), 400)

        if not shipping_address_id:
            return make_response(jsonify({"error": "Shipping address is required"}), 400)

        address = UserAddress.query.get(shipping_address_id)
        if not address:
            return make_response(jsonify({"error": "Shipping address not found"}), 404)

        try:
            charge = stripe.Charge.create(
                amount=int(cart.total_price * 100),  # Stripe expects the amount in cents
                currency='kes',
                description=f'Order by {user.username}',
                source=token
            )
        except stripe.error.StripeError as e:
            return make_response(jsonify({"error": str(e)}), 400)

        # Create a new order with the shipping address
        order = Order(
            buyer_id=user_id,
            total_price=cart.total_price,
            status="Successful",
            shipping_address_id=shipping_address_id
        )
        db.session.add(order)
        db.session.commit()

        # Create order items and update product stock
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price
            )
            db.session.add(order_item)
            
            product = Product.query.get(item.product_id)
            product.stock -= item.quantity

        # Create UserPayment entry
        user_payment = UserPayment(
            user_id=user_id,
            payment_method=charge.payment_method_details['type'],
            account_no=charge.payment_method,
            amount=charge.amount,  # converting back to original currency
            name=user.username,
            description=charge.description,
            status=charge.status,
            receipt_url=charge.receipt_url
        )
        db.session.add(user_payment)

        # Empty the cart
        CartItem.query.filter_by(cart_id=cart.id).delete()
        cart.total_price = 0

        db.session.commit()

        response = {
            "message": "Checkout successful",
            "charge_id": charge.id,
            "charge_status": charge.status,
            "total_amount": charge.amount,
            "currency": charge.currency,
            "order_id": order.id,
            "receipt_url": charge.receipt_url
        }
        return make_response(jsonify(response), 201)



class ReviewPostResource(Resource):
    @jwt_required()
    @allow('Buyer')
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json()
        product_id = data.get('product_id')
        rating = data.get('rating')
        comment = data.get('comment', '')

        if not product_id or not rating:
            return jsonify({"error": "Product ID and rating are required"}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Check if the user has purchased the product
        order_item = OrderItem.query.join(Order).filter(
            Order.buyer_id == user_id,
            OrderItem.product_id == product_id
        ).first()

        if not order_item:
            return jsonify({"error": "User has not purchased this product"}), 403

        review = Review(
            product_id=product_id,
            user_id=user_id,
            rating=rating,
            comment=comment
        )

        db.session.add(review)
        db.session.commit()

        return make_response(jsonify({"message": "Review created successfully"}), 201)
    

class ReviewUpdateResource(Resource):
    @jwt_required()
    @allow('Buyer')
    def put(self, review_id):
        user_id = get_jwt_identity()
        data = request.get_json()
        rating = data.get('rating')
        comment = data.get('comment', '')

        review = Review.query.get(review_id)
        if not review:
            return {"error": "Review not found"}, 404

        if review.user_id != user_id:
            return {"error": "You can only edit your own reviews"}, 403

        if rating:
            review.rating = rating
        if comment:
            review.comment = comment
        review.updated_at = datetime.now()

        db.session.commit()

        return make_response(jsonify({
            "message": "Review updated successfully",
            "review": {
                "id": review.id,
                "product_id": review.product_id,
                "user_id": review.user_id,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at,
                "updated_at": review.updated_at
            }
        }), 200)

class DeleteReview(Resource):
    @jwt_required()
    @allow('Buyer')
    def delete(self, review_id):
        user_id = get_jwt_identity()
        review = Review.query.get(review_id)
        
        if not review:
            return jsonify({"error": "Review not found"}), 404

        if review.user_id != user_id:
            return jsonify({"error": "You can only delete your own reviews"}), 403

        deleted_review = {
            "id": review.id,
            "product_id": review.product_id,
            "user_id": review.user_id,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at,
            "updated_at": review.updated_at
        }

        db.session.delete(review)
        db.session.commit()

        return make_response(jsonify({
            "message": "Review deleted successfully",
            "deleted_review": deleted_review
        }), 200)




class ProductReviewsResource(Resource):
    def get(self, product_id):
        product = Product.query.get(product_id)
        if not product:
            return {"error": "Product not found"}, 404

        reviews = Review.query.filter_by(product_id=product_id).all()
        reviews_list = [{
            "id": review.id,
            "user_id": review.user_id,
            "user_name": f"{review.user.first_name} {review.user.last_name}",  # Get the full name of the user
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at,
            "updated_at": review.updated_at,
            "verified_purchase": OrderItem.query.join(Order).filter(
                Order.buyer_id == review.user_id,
                OrderItem.product_id == product_id
            ).count() > 0
        } for review in reviews]

        return make_response(jsonify(reviews_list), 200)



class AddToWishlistResource(Resource):
    @jwt_required()
    @allow('Buyer')
    def post(self):
        user_id = get_jwt_identity()
        data = request.get_json()
        product_id = data.get('product_id')

        if not product_id:
            return jsonify({"error": "Product ID is required"}), 400

        product = Product.query.get(product_id)
        if not product:
            return jsonify({"error": "Product not found"}), 404

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        wishlist_item = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
        if wishlist_item:
            return jsonify({"error": "Product already in wishlist"}), 400

        wishlist = Wishlist(
            user_id=user_id,
            product_id=product_id
        )

        db.session.add(wishlist)
        db.session.commit()

        return make_response(jsonify({
            "message": "Product added to wishlist successfully",
            "product": {
                "id": wishlist.id,
                "title": product.title,
                "description": product.description,
                "price": product.price,
                "image_url": product.image_url,
                "created_at": wishlist.created_at,
                "updated_at": wishlist.updated_at
            }
        }), 201)



class ViewWishlistResource(Resource):
    @jwt_required()
    @allow('Buyer')
    def get(self):
        user_id = get_jwt_identity()
        wishlists = Wishlist.query.filter_by(user_id=user_id).all()
        result = []
        for item in wishlists:
            product = Product.query.get(item.product_id)
            result.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_title": product.title,
                "product_description": product.description,
                "product_price": product.price,
                "product_image_url": product.image_url,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            })

        return make_response(jsonify(result), 200)

class DeleteFromWishlistResource(Resource):
    @jwt_required()
    @allow('Buyer')
    def delete(self, wishlist_id):
        user_id = get_jwt_identity()
        wishlist_item = Wishlist.query.get(wishlist_id)
        if not wishlist_item:
            return jsonify({"error": "Wishlist item not found"}), 404

        if wishlist_item.user_id != user_id:
            return jsonify({"error": "You can only delete your own wishlist items"}), 403

        db.session.delete(wishlist_item)
        db.session.commit()

        return make_response(jsonify({
            "message": "Wishlist item deleted successfully",
            "deleted_item": {
                "id": wishlist_item.id,
                "product_id": wishlist_item.product_id
            }
        }), 200)
    
class UserAddressSchema(Schema):
    id = fields.Int()
    user_id = fields.Int()
    address = fields.Str()
    telephone = fields.Str()
    postal_code = fields.Str()
    city = fields.Str()
    country = fields.Str()
    is_selected = fields.Bool()

class UserSchema(Schema):
    id = fields.Int()
    first_name = fields.Str()
    last_name = fields.Str()
    username = fields.Str()
    email = fields.Str()
    addresses = fields.List(fields.Nested(UserAddressSchema))


class GetUserProfile(Resource):
    @jwt_required()
    def get(self):
        # Get the current user's identity
        current_user_id = get_jwt_identity()

        # Fetch the user and their addresses
        user = User.query.get(current_user_id)
        if not user:
            return {'message': 'User not found'}, 404

        # Serialize the user and their addresses
        user_schema = UserSchema()
        user_data = user_schema.dump(user)

        return jsonify(user_data)


# Resource for getting and updating user profile
class UpdateUserProfile(Resource):
    @jwt_required()
    def put(self):
        # Get the current user's identity
        current_user_id = get_jwt_identity()

        # Fetch the user
        user = User.query.get(current_user_id)
        if not user:
            return {'message': 'User not found'}, 404

        # Validate and update the request data
        data = request.get_json()
        try:
            user_schema = UserSchema(partial=True)
            user_data = user_schema.load(data, partial=True)
        except ValidationError as err:
            return {'errors': err.messages}, 400

        # Update user fields
        for key, value in user_data.items():
            setattr(user, key, value)
        
        db.session.commit()
        
        return jsonify({'message': 'User profile updated successfully'})

class AddUserAddress(Resource):
    @jwt_required()
    def post(self):
        current_user_id = get_jwt_identity()
        data = request.get_json()
        try:
            address_schema = UserAddressSchema()
            address_data = address_schema.load(data)
        except ValidationError as err:
            return {'errors': err.messages}, 400

        address = UserAddress(user_id=current_user_id, **address_data)
        db.session.add(address)
        db.session.commit()

        return jsonify({'message': 'Address added successfully'})

# Resource for updating an existing address
class UpdateUserAddress(Resource):
    @jwt_required()
    def put(self, address_id):
        current_user_id = get_jwt_identity()
        address = UserAddress.query.filter_by(id=address_id, user_id=current_user_id).first()
        if not address:
            return {'message': 'Address not found'}, 404

        data = request.get_json()
        try:
            address_schema = UserAddressSchema(partial=True)
            address_data = address_schema.load(data, partial=True)
        except ValidationError as err:
            return {'errors': err.messages}, 400

        for key, value in address_data.items():
            setattr(address, key, value)
        
        db.session.commit()

        return jsonify({'message': 'Address updated successfully'})

# Resource for deleting an address
class DeleteUserAddress(Resource):
    @jwt_required()
    def delete(self, address_id):
        current_user_id = get_jwt_identity()
        address = UserAddress.query.filter_by(id=address_id, user_id=current_user_id).first()
        if not address:
            return {'message': 'Address not found'}, 404

        db.session.delete(address)
        db.session.commit()

        return jsonify({'message': 'Address deleted successfully'})

class ListUserAddresses(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        addresses = UserAddress.query.filter_by(user_id=current_user_id).all()

        addresses_list = [
            {
                "id": address.id,
                "address": address.address,
                "telephone": address.telephone,
                "postal_code": address.postal_code,
                "city": address.city,
                "country": address.country,
                "is_selected": address.is_selected
            }
            for address in addresses
        ]

        return jsonify(addresses_list)

class SelectedAddressResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        selected_address = UserAddress.query.filter_by(user_id=user_id, is_selected=True).first()

        if selected_address:
            address_schema = UserAddressSchema()
            return make_response(jsonify({'address': address_schema.dump(selected_address)}), 200)
        else:
            return make_response(jsonify({'message': 'No selected address found'}), 404)
    

class SelectAddressResource(Resource):
    @jwt_required()
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('address_id', type=int, required=True, help='Address ID is required')
        args = parser.parse_args()

        user_id = get_jwt_identity()
        address_id = args['address_id']

        address = UserAddress.query.filter_by(id=address_id, user_id=user_id).first()
        if not address:
            return {'message': 'Address not found'}, 404

        # Deselect all addresses for the user
        UserAddress.query.filter_by(user_id=user_id).update({'is_selected': False})

        # Select the given address
        address.is_selected = True
        db.session.commit()

        return make_response(jsonify({'message': 'Address selected successfully'}), 200)
    
class CheckoutHistory(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        print(f"Authenticated user ID: {user_id}")  # Debug statement
        
        buyer = User.query.get(user_id)
        if not buyer:
            return {"error": "User not found"}, 404
        
        print(f"User Role ID: {buyer.role_id}")  # Debug statement
        
       
        if buyer.role_id != 1: 
            return {"error": "Unauthorized"}, 403

       
        orders = Order.query.filter_by(buyer_id=user_id).all()

       
        orders_list = []
        for order in orders:
            order_items = [
                {
                    "product_id": item.product_id,
                    "product_title": item.product.title,
                    "quantity": item.quantity,
                    "price": item.price
                } for item in order.order_items
            ]

            orders_list.append({
                "order_id": order.id,
                "total_price": order.total_price,
                "status": order.status,
                "created_at": order.created_at,
                "updated_at": order.updated_at,
                "order_items": order_items
            })

        return jsonify({"orders": orders_list})


buyer_api.add_resource(AddToCart, '/add_to_cart')
buyer_api.add_resource(DeleteCartItem, '/cart/items/<int:product_id>')
buyer_api.add_resource(GetCartResource, '/cart')
buyer_api.add_resource(UpdateCart, '/cart/update')
buyer_api.add_resource(Checkout, '/checkout')
buyer_api.add_resource(ReviewPostResource, '/reviews')
buyer_api.add_resource(ReviewUpdateResource, '/reviews/<int:review_id>')
buyer_api.add_resource(DeleteReview, '/reviews/<int:review_id>')
buyer_api.add_resource(ProductReviewsResource, '/products/<int:product_id>/reviews')
buyer_api.add_resource(AddToWishlistResource, '/wishlist')
buyer_api.add_resource(ViewWishlistResource, '/wishlist')
buyer_api.add_resource(DeleteFromWishlistResource, '/wishlist/<int:wishlist_id>')
buyer_api.add_resource(GetUserProfile, '/profile')
buyer_api.add_resource(UpdateUserProfile, '/profile')
buyer_api.add_resource(AddUserAddress, '/addresses')
buyer_api.add_resource(UpdateUserAddress, '/addresses/<int:address_id>')
buyer_api.add_resource(DeleteUserAddress, '/addresses/<int:address_id>')
buyer_api.add_resource(ListUserAddresses, '/addresses')
buyer_api.add_resource(SelectedAddressResource, '/selected-address')
buyer_api.add_resource(SelectAddressResource, '/select-address')
buyer_api.add_resource(CheckoutHistory, '/checkout/history')

