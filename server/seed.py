import bcrypt
from models import db, User, Product, Category, Role, Order, OrderItem, Cart, CartItem, Review, Admin
from app import app

def hash_password(password):
    """ Hash a password using bcrypt. """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def seed_data():
    print("Deleting all records...")
    User.query.delete()
    Category.query.delete()
    Product.query.delete()
    Role.query.delete()
    Order.query.delete()
    OrderItem.query.delete()
    Cart.query.delete()
    CartItem.query.delete()
    Review.query.delete()

    print("Creating Roles...")
    # Roles
    role1 = Role(name='Buyer')
    role2 = Role(name='Seller')
    role3 = Role(name='Admin')
    db.session.add_all([role1, role2, role3])
    db.session.commit()

    print("Creating Users...")
    # Create users
    user1 = User(
        first_name="Elon",
        last_name="Musk",
        username="seller1",
        email="seller1@example.com",
        password=hash_password("password"),
        role_id=role2.id
    )
    user2 = User(
        first_name="Stan",
        last_name="Smith",
        username="seller2",
        email="seller2@example.com",
        password=hash_password("password"),
        role_id=role2.id
    )
    user3 = User(
        first_name="Mark",
        last_name="Beast",
        username="beast",
        email="beast@example.com",
        password=hash_password("password"),
        role_id=role1.id
    )
    db.session.add_all([user1, user2, user3])
    db.session.commit()

    print("Creating Admins...")
    # Create admin user
    admin_role = Role.query.filter_by(name='Admin').first()
    if admin_role:
        admin_user = Admin(
            first_name="Tony",
            last_name="Stark",
            username='Iron',
            email='tony@example.com',
            password=hash_password('88888888'),
            role_id=admin_role.id
        )
        db.session.add(admin_user)
        db.session.commit()
    else:
        print("Admin role not found. Please ensure roles are seeded properly.")

    # Create categories
    # category1 = Category(name="Electronics", image_url="https://i.pinimg.com/564x/1e/72/e3/1e72e3a95993056e144f6bbdbd032861.jpg")
    # category2 = Category(name="Books", image_url = "https://i.pinimg.com/564x/1a/11/27/1a11272d801b8d3f51332b12e87b635d.jpg")
    # category3 = Category(name="Clothing", image_url="https://i.pinimg.com/564x/41/ee/54/41ee54c88e48977145af1846889a56fa.jpg")
    # category4 = Category(name="Toys", image_url="https://i.pinimg.com/564x/2a/d2/e0/2ad2e0775fe81e8fe6a4ccefc6636ee2.jpg")
    # db.session.add_all([category1, category2, category3, category4])
    # db.session.commit()

    # print("Creating Products...")
    # # Create products
    # products = [
    #     Product(
    #         title="Iphone 13",
    #         description="Brand new with a powerful camera",
    #         price=650,
    #         category_id=category1.id,
    #         image_url="https://i.pinimg.com/564x/be/a3/12/bea31296162a1c6d82f7cfa90a14d60b.jpg",
    #         seller_id=user1.id,
    #         stock=15
    #     ),
    #     Product(
    #         title="The Alchemist",
    #         description="A starter must read for every reader",
    #         price=29.99,
    #         category_id=category2.id,
    #         image_url="https://i.pinimg.com/564x/49/7f/22/497f22527c6c0b20fb0bbe814ab918b2.jpg",
    #         seller_id=user1.id,
    #         stock=20
    #     ),
    #     Product(
    #         title="Dennis Rodman Vintage T-Shirt",
    #         description="Stampa frontale in stile Hip Hop. Composition: 100% Cotton",
    #         price=9.99,
    #         category_id=category3.id,
    #         image_url="https://i.pinimg.com/564x/3e/0c/17/3e0c176bd253f7df77b51436ae296e9a.jpg",
    #         seller_id=user2.id,
    #         stock=20
    #     ),
    #     Product(
    #         title="Lightning McQueen Gift Set",
    #         description="This fun and functional gift toy cars is a must buy. Features: Material: Alloy + Plastic + Rubber Colour options available Age Range: > 3 years old",
    #         price=49.99,
    #         category_id=category4.id,
    #         image_url="https://i.pinimg.com/564x/f0/a2/9f/f0a29f9f19810aa08aae24fea5baa202.jpg",
    #         seller_id=user2.id,
    #         stock=15
    #     )
    # ]
    # db.session.add_all(products)
    # db.session.commit()

    # print("Creating Carts...")
    # # Create carts
    # cart1 = Cart(user_id=user3.id, total_price=0)
    # db.session.add(cart1)
    # db.session.commit()

    # print("Creating CartItems...")
    # # Create cart items
    # cart_items = [
    #     CartItem(cart_id=cart1.id, product_id=products[0].id, quantity=2, price=products[0].price),
    #     CartItem(cart_id=cart1.id, product_id=products[1].id, quantity=1, price=products[1].price)
    # ]
    # db.session.add_all(cart_items)
    # db.session.commit()

    # # Update cart total price
    # cart1.total_price = sum([item.quantity * item.price for item in cart_items])
    # db.session.commit()

    # print("Creating Orders...")
    # # Create orders
    # order1 = Order(buyer_id=user3.id, total_price=0)
    # db.session.add(order1)
    # db.session.commit()

    # print("Creating OrderItems...")
    # # Create order items
    # order_items = [
    #     OrderItem(order_id=order1.id, product_id=products[0].id, quantity=2, price=products[0].price),
    #     OrderItem(order_id=order1.id, product_id=products[1].id, quantity=1, price=products[1].price)
    # ]
    # db.session.add_all(order_items)
    # db.session.commit()

    # # Update order total price
    # order1.total_price = sum([item.quantity * item.price for item in order_items])
    # db.session.commit()

    # print("Creating Reviews...")
    # # Create reviews
    # reviews = [
    #     Review(
    #         product_id=products[0].id,
    #         user_id=user3.id,
    #         rating=5,
    #         comment="Great product, highly recommend!"
    #     ),
    #     Review(
    #         product_id=products[1].id,
    #         user_id=user3.id,
    #         rating=4,
    #         comment="Good product, but a bit expensive."
    #     )
    # ]
    # db.session.add_all(reviews)
    # db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure all tables are created
        seed_data()  # Seed the database with mock data
        print("Database seeded!")
