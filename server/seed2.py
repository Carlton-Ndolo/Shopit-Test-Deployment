from models import db, User, Product, Category, Role, Order, OrderItem, Cart, CartItem, Review
from app import app

def seed_data_for_fifth_user():
    fifth_user_id = 10  # The ID of the fourth user

    print("Creating Cart for Fifth User...")
    # Create cart for fifth user
    cart = Cart(user_id=fifth_user_id, total_price=0)
    db.session.add(cart)
    db.session.commit()

    print("Creating CartItems for Fifth User...")
    # Create cart items for fifth user
    cart_items = [
        CartItem(cart_id=cart.id, product_id=5, quantity=1, price=300),  # Assuming product_id 1 exists
        CartItem(cart_id=cart.id, product_id=6, quantity=1, price=35)   # Assuming product_id 2 exists
    ]
    db.session.add_all(cart_items)
    db.session.commit()

    # Update cart total price
    cart.total_price = sum([item.quantity * item.price for item in cart_items])
    db.session.commit()

    print("Creating Order for Fifth User...")
    # Create order for fifth user
    order = Order(buyer_id=fifth_user_id, total_price=0)
    db.session.add(order)
    db.session.commit()

    print("Creating OrderItems for Fifth User...")
    # Create order items for fifth user
    order_items = [
        OrderItem(order_id=order.id, product_id=5, quantity=1, price=300),  # Assuming product_id 1 exists
        OrderItem(order_id=order.id, product_id=6, quantity=1, price=35)   # Assuming product_id 2 exists
    ]
    db.session.add_all(order_items)
    db.session.commit()

    # Update order total price
    order.total_price = sum([item.quantity * item.price for item in order_items])
    db.session.commit()

    print("Creating Reviews for Fifth User...")
    # Create reviews for fifth user
    reviews = [
        Review(
            product_id=5,  # Assuming product_id 1 exists
            user_id=fifth_user_id,
            rating=4,
            comment="Pretty good product."
        ),
        Review(
            product_id=6,  # Assuming product_id 2 exists
            user_id=fifth_user_id,
            rating=5,
            comment="Excellent product!"
        )
    ]
    db.session.add_all(reviews)
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure all tables are created

        seed_data_for_fifth_user()
        print("Database seeded for fifth user!")
