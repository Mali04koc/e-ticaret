from website import create_app, db
from website.models import Card

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables updated successfully!")
