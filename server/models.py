#models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class SerializerMixin:
    def to_dict(self, include_relationships=False):
        """Serialize model to dictionary, including optional relationships."""
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        
        if include_relationships:
            for rel in self.__mapper__.relationships.keys():
                rel_obj = getattr(self, rel)
                if rel_obj is not None:
                    if isinstance(rel_obj, list):
                        data[rel] = [item.to_dict(include_relationships=True) for item in rel_obj]
                    else:
                        data[rel] = rel_obj.to_dict(include_relationships=True)
        return data

class Role(db.Model, SerializerMixin):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    users = db.relationship('User', back_populates='role')

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    role = db.relationship('Role', back_populates='users')
    products = db.relationship('Product', order_by='Product.id', back_populates='seller')
    orders = db.relationship('Order', order_by='Order.id', back_populates='buyer')
    user_payments = db.relationship('UserPayment', order_by='UserPayment.id', back_populates='user')
    address = db.relationship('UserAddress',  back_populates='user')
    cart = db.relationship('Cart', uselist=False, back_populates='user')
    reviews = db.relationship('Review', order_by='Review.id', back_populates='user')
    wishlists = db.relationship('Wishlist', order_by='Wishlist.id', back_populates='user')
    checkouts = db.relationship('Checkout', order_by='Checkout.id', back_populates='user')

class Category(db.Model, SerializerMixin):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    image_url = db.Column(db.String(200))

    products = db.relationship('Product', back_populates='category')

class Product(db.Model, SerializerMixin):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    stock = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(200))
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    seller = db.relationship('User', back_populates='products')
    category = db.relationship('Category', back_populates='products')
    order_items = db.relationship('OrderItem', order_by='OrderItem.id', back_populates='product', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', order_by='CartItem.id', back_populates='product', cascade='all, delete-orphan')
    reviews = db.relationship('Review', order_by='Review.id', back_populates='product', cascade='all, delete-orphan')
    wishlists = db.relationship('Wishlist', order_by='Wishlist.id', back_populates='product', cascade='all, delete-orphan')

class Order(db.Model, SerializerMixin):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    shipping_address_id = db.Column(db.Integer, db.ForeignKey('user_addresses.id'), nullable=True)  # New field

    buyer = db.relationship('User', back_populates='orders')
    order_items = db.relationship('OrderItem', order_by='OrderItem.id', back_populates='order')
    payment_details = db.relationship('PaymentDetail', order_by='PaymentDetail.id', back_populates='order')
    shipping_address = db.relationship('UserAddress', back_populates='orders')  # New relationship

class PaymentDetail(db.Model, SerializerMixin):
    __tablename__ = 'payment_details'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    payment_method = db.Column(db.String, nullable=False)
    payment_status = db.Column(db.String, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.now)
    amount = db.Column(db.Float, nullable=False)

    order = db.relationship('Order', back_populates='payment_details')

class UserPayment(db.Model, SerializerMixin):
    __tablename__ = 'user_payments'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payment_method = db.Column(db.String, nullable=False)
    account_no = db.Column(db.String, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.now)
    amount = db.Column(db.Float, nullable=False)
    name = db.Column(db.String, nullable=True)  # Name associated with the payment
    description = db.Column(db.String, nullable=True)  # Payment description
    status = db.Column(db.String, nullable=True)  # Payment status (e.g., succeeded, pending)
    receipt_url = db.Column(db.String, nullable=True)  # URL to the payment receipt

    user = db.relationship('User', back_populates='user_payments')


class OrderItem(db.Model, SerializerMixin):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    order = db.relationship('Order', back_populates='order_items')
    product = db.relationship('Product', back_populates='order_items')

class UserAddress(db.Model, SerializerMixin):
    __tablename__ = 'user_addresses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address = db.Column(db.Text, nullable=False)
    telephone = db.Column(db.String(20))
    postal_code = db.Column(db.String(20))
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    address_type = db.Column(db.String(50))
    is_selected = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', back_populates='address')
    orders = db.relationship('Order', back_populates='shipping_address')


class Cart(db.Model, SerializerMixin):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship('User', back_populates='cart')
    cart_items = db.relationship('CartItem', order_by='CartItem.id', back_populates='cart')
    checkout = db.relationship('Checkout', uselist=False, back_populates='cart')


class CartItem(db.Model, SerializerMixin):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    cart = db.relationship('Cart', back_populates='cart_items')
    product = db.relationship('Product', back_populates='cart_items')

class Review(db.Model, SerializerMixin):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    product = db.relationship('Product', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')

class Wishlist(db.Model, SerializerMixin):
    __tablename__ = 'wishlists'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship('User', back_populates='wishlists')
    product = db.relationship('Product', back_populates='wishlists')

class Admin(db.Model, SerializerMixin):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)    
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    role = db.relationship('Role')

class Checkout(db.Model, SerializerMixin):
    __tablename__ = 'checkouts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    user = db.relationship('User', back_populates='checkouts')
    cart = db.relationship('Cart', back_populates='checkout')


