from website import create_app, db
import sqlalchemy as sa

app = create_app()

with app.app_context():
    engine = db.engine
    inspector = sa.inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('customer')]
    
    if 'is_banned' not in columns:
        with engine.connect() as conn:
            conn.execute(sa.text('ALTER TABLE customer ADD COLUMN is_banned BOOLEAN DEFAULT 0'))
            print("Successfully added 'is_banned' column to customer table.")
    else:
        print("'is_banned' column already exists.")
