from website import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE product ADD COLUMN is_active BOOLEAN DEFAULT TRUE;"))
            conn.commit()
            print("Migration successful: Added is_active column.")
    except Exception as e:
        print(f"Migration failed (might already exist): {e}")
