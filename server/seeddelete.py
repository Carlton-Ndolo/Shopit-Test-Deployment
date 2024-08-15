from app import app # Adjust the import according to your project structure
from models import UserAddress, db  # Adjust the import according to your project structure

# Ensure your app context is pushed for database operations
with app.app_context():
    try:
        # Query all records from the UserAddress table
        user_addresses = UserAddress.query.all()

        # Delete all records
        for address in user_addresses:
            db.session.delete(address)
        
        # Commit the changes to the database
        db.session.commit()
        print("All records from UserAddress table have been deleted successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")
