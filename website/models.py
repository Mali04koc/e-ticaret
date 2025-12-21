# database sayfamız
from . import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Customer(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(20), unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    password_hash = db.Column(db.String(255))
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    is_banned = db.Column(db.Boolean, default=False)

    cart_items = db.relationship('Cart', backref=db.backref('customer', lazy=True))
    orders = db.relationship('Order', backref=db.backref('customer', lazy=True))

    @property
    def password(self):
        raise AttributeError('Password is not a readable Attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password=password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password=password)

    def __str__(self):
        return '<Customer %r>' % Customer.id


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    previous_price = db.Column(db.Float, nullable=False)
    in_stock = db.Column(db.Integer, nullable=False)
    product_picture = db.Column(db.String(1000), nullable=False)
    flash_sale = db.Column(db.String(100)) # Stores discount percentage text e.g. "%20 İndirim"
    category = db.Column(db.String(100)) # Stores product category
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    carts = db.relationship('Cart', backref=db.backref('product', lazy=True))
    orders = db.relationship('Order', backref=db.backref('product', lazy=True))

    def __str__(self):
        return '<Product %r>' % self.product_name


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    # customer product

    def __str__(self):
        return '<Cart %r>' % self.id


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    payment_id = db.Column(db.String(1000), nullable=False)

    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_link = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    # customer

    def __str__(self):
        return '<Order %r>' % self.id


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    
    address_title = db.Column(db.String(100), nullable=False)
    general_address = db.Column(db.String(300), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    recipient_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    def __str__(self):
        return '<Address %r>' % self.address_title


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_link = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    card_name = db.Column(db.String(100), nullable=False) # e.g. "My Personal Card"
    masked_number = db.Column(db.String(20), nullable=False) # "**** **** **** 1234"
    expiry_date = db.Column(db.String(5), nullable=False) # "12/26"

    def __str__(self):
        return '<Card %r>' % self.masked_number


class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_value = db.Column(db.Float, nullable=False)
    is_percentage = db.Column(db.Boolean, default=False)
    target_customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True) # Null = Global
    is_active = db.Column(db.Boolean, default=True)

    def __str__(self):
        return '<Coupon %r>' % self.code











