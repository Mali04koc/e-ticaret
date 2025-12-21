from website import create_app, db
from website.models import Order

app = create_app()

with app.app_context():
    # Update orders that have old statuses or "Paid" variants
    orders = Order.query.all()
    count = 0
    for order in orders:
        # Check if status is one of the old ones or contains "Paid"
        if order.status in ['Pending', 'Accepted', 'Out for delivery', 'Paid'] or 'Paid (' in order.status:
            order.status = 'Onaylanmayı Bekliyor'
            count += 1
            
    db.session.commit()
    print(f"Updated {count} orders to 'Onaylanmayı Bekliyor'.")
