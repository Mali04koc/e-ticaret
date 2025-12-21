from website import create_app, db
import sqlalchemy as sa
from website.models import Coupon

app = create_app()

with app.app_context():
    # Helper to check if table exists
    engine = db.engine
    inspector = sa.inspect(engine)
    
    if 'coupon' not in inspector.get_table_names():
        db.create_all()
        print("Created 'coupon' table.")
    else:
        print("'coupon' table already exists.")
