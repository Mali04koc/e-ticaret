from flask import Blueprint, render_template, flash, redirect, request, jsonify
from .models import Product, Cart, Order, Address, Card, Coupon, Favorite
from flask_login import login_required, current_user
from . import db
from intasend import APIService
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

views = Blueprint('views', __name__)

API_PUBLISHABLE_KEY = os.getenv('INTASEND_PUBLISHABLE_KEY')
API_TOKEN = os.getenv('INTASEND_API_TOKEN')


@views.context_processor
def inject_favorites():
    if current_user.is_authenticated:
        favorites = Favorite.query.filter_by(customer_link=current_user.id).all()
        fav_ids = [fav.product_link for fav in favorites]
        return dict(user_favorites=fav_ids)
    return dict(user_favorites=[])


@views.route('/favorites')
@login_required
def favorites():
    user_favorites = Favorite.query.filter_by(customer_link=current_user.id).all()
    # We need to get the actual product objects.
    # Assuming Favorite has product_link which is the ID.
    # Better to join or just query Products where id in list.
    fav_product_ids = [f.product_link for f in user_favorites]
    if fav_product_ids:
        products = Product.query.filter(Product.id.in_(fav_product_ids)).all()
    else:
        products = []
        
    return render_template('favs.html', items=products)


@views.route('/toggle-favorite/<int:item_id>')
@login_required
def toggle_favorite(item_id):
    product = Product.query.get(item_id)
    if not product:
        flash('Ürün bulunamadı.', category='error')
        return redirect(request.referrer)

    existing_fav = Favorite.query.filter_by(customer_link=current_user.id, product_link=item_id).first()
    
    if existing_fav:
        db.session.delete(existing_fav)
        db.session.commit()
        flash(f'{product.product_name} favorilerden çıkarıldı.', category='info')
    else:
        new_fav = Favorite(customer_link=current_user.id, product_link=item_id)
        db.session.add(new_fav)
        db.session.commit()
        flash(f'{product.product_name} favorilere eklendi.', category='success')
    
    return redirect(request.referrer)


@views.route('/')
def landing():
    """Public Landing Page"""
    if current_user.is_authenticated:
        return redirect('/shop')
    return render_template('index.html')


@views.route('/shop')
@login_required
def home():
    """Main Shop Page (previously home)"""
    items = Product.query.filter(Product.flash_sale != None).all()

    return render_template('home.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])


@views.route('/add-to-cart/<int:item_id>')
@login_required
def add_to_cart(item_id):
    item_to_add = Product.query.get(item_id)
    if not item_to_add or not item_to_add.is_active:
        flash('Bu ürün şu anda temin edilemiyor.', category='error')
        return redirect(request.referrer)
        
    item_exists = Cart.query.filter_by(product_link=item_id, customer_link=current_user.id).first()
    if item_exists:
        try:
            item_exists.quantity = item_exists.quantity + 1
            db.session.commit()
            flash(f'  { item_exists.product.product_name } miktarı güncellendi.')
            return redirect(request.referrer)
        except Exception as e:
            print('Miktar Güncellenmedi', e)
            flash(f'{ item_exists.product.product_name } miktarı güncellenmedi.')
            return redirect(request.referrer)

    new_cart_item = Cart()
    new_cart_item.quantity = 1
    new_cart_item.product_link = item_to_add.id
    new_cart_item.customer_link = current_user.id

    try:
        db.session.add(new_cart_item)
        db.session.commit()
        flash(f'{new_cart_item.product.product_name} sepete eklendi')
    except Exception as e:
        print('Eşya sepete eklenemedi', e)
        flash(f'{new_cart_item.product.product_name} sepete eklenemedi')

    return redirect(request.referrer)


@views.route('/cart')
@login_required
def show_cart():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    amount = 0
    for item in cart:
        amount += item.product.current_price * item.quantity

    return render_template('cart.html', cart=cart, amount=amount, total=amount+200)


@views.route('/pluscart')
@login_required
def plus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        cart_item.quantity = cart_item.quantity + 1
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 200
        }

        return jsonify(data)


@views.route('/minuscart')
@login_required
def minus_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        if cart_item.quantity > 1:
            cart_item.quantity = cart_item.quantity - 1
            db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 200
        }

        return jsonify(data)


@views.route('removecart')
@login_required
def remove_cart():
    if request.method == 'GET':
        cart_id = request.args.get('cart_id')
        cart_item = Cart.query.get(cart_id)
        db.session.delete(cart_item)
        db.session.commit()

        cart = Cart.query.filter_by(customer_link=current_user.id).all()

        amount = 0

        for item in cart:
            amount += item.product.current_price * item.quantity

        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'total': amount + 200
        }

        return jsonify(data)


@views.route('/place-order')
@login_required
def place_order():
    customer_cart = Cart.query.filter_by(customer_link=current_user.id)
    if customer_cart:
        try:
            total = 0
            for item in customer_cart:
                if not item.product.is_active:
                    flash(f"'{item.product.product_name}' şu anda temin edilemiyor. Lütfen sepetinizden çıkarın.", category='error')
                    return redirect('/cart')
                total += item.product.current_price * item.quantity

            service = APIService(token=API_TOKEN, publishable_key=API_PUBLISHABLE_KEY, test=True)
            create_order_response = service.collect.mpesa_stk_push(phone_number='YOUR_NUMBER ', email=current_user.email,
                                                                   amount=total + 200, narrative='Purchase of goods')

            for item in customer_cart:
                new_order = Order()
                new_order.quantity = item.quantity
                new_order.price = item.product.current_price
                new_order.status = create_order_response['invoice']['state'].capitalize()
                new_order.payment_id = create_order_response['id']

                new_order.product_link = item.product_link
                new_order.customer_link = item.customer_link

                db.session.add(new_order)

                product = Product.query.get(item.product_link)

                product.in_stock -= item.quantity

                db.session.delete(item)

                db.session.commit()

            flash('Order Placed Successfully')

            return redirect('/orders')
        except Exception as e:
            print(e)
            flash('Order not placed')
            return redirect('/')
    else:
        flash('Your cart is Empty')
        return redirect('/')


@views.route('/apply-coupon', methods=['POST'])
@login_required
def apply_coupon():
    code = request.form.get('code')
    if not code:
        flash('Kupon kodu girilmedi.', category='error')
        return redirect('/checkout')
        
    coupon = Coupon.query.filter_by(code=code).first()
    
    if not coupon:
        flash('Geçersiz kupon kodu.', category='error')
        return redirect('/checkout')
        
    if not coupon.is_active:
        flash('Bu kupon artık geçerli değil.', category='error')
        return redirect('/checkout')
        
    # Check Target
    if coupon.target_customer_id and coupon.target_customer_id != current_user.id:
        flash('Bu kupon size özel değil.', category='error')
        return redirect('/checkout')
        
    # Calculate Discount
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    subtotal = sum(item.product.current_price * item.quantity for item in cart)
    
    discount = 0
    if coupon.is_percentage:
        discount = (subtotal * coupon.discount_value) / 100
    else:
        discount = coupon.discount_value
        
    # Store in session
    session['coupon_code'] = coupon.code
    session['discount_amount'] = discount
    flash(f'Kupon uygulandı! {discount} TL indirim.', category='success')
    
    return redirect('/checkout')


@views.route('/remove-coupon')
@login_required
def remove_coupon():
    session.pop('coupon_code', None)
    session.pop('discount_amount', None)
    flash('Kupon kaldırıldı.', category='info')
    return redirect('/checkout')


@views.route('/checkout')
@login_required
def checkout():
    cart = Cart.query.filter_by(customer_link=current_user.id).all()
    if not cart:
        flash('Sepetiniz boş. Lütfen ürün ekleyin.', category='error')
        return redirect('/shop')

    addresses = Address.query.filter_by(customer_link=current_user.id).all()
    saved_cards = Card.query.filter_by(customer_link=current_user.id).all()
    
    amount = 0
    for item in cart:
        amount += item.product.current_price * item.quantity
    
    total_price = amount + 200 # Shipping cost
    
    # Apply Discount if Coupon exists in session
    discount_amount = 0
    if 'coupon_code' in session:
        discount_amount = session.get('discount_amount', 0)
        total_price -= discount_amount
        
    if total_price < 0:
        total_price = 0
    
    return render_template('checkout.html', cart=cart, addresses=addresses, saved_cards=saved_cards, total_price=total_price)


import random
from flask import session

@views.route('/send-email-code', methods=['POST'])
@login_required
def send_email_code():
    import requests
    
    code = str(random.randint(100000, 999999))
    session['email_code'] = code
    
    # Brevo API Config
    url = "https://api.brevo.com/v3/smtp/email"
    api_key = os.getenv('BREVO_API_KEY')
    sender_email = os.getenv('BREVO_SENDER_EMAIL')
    sender_name = os.getenv('BREVO_SENDER_NAME')
    
    # Payload
    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email
        },
        "to": [
            {
                "email": current_user.email,
                "name": f"{current_user.first_name} {current_user.last_name}"
            }
        ],
        "subject": "Ödeme Doğrulama Kodu",
        "htmlContent": f"<html><body><h1>Doğrulama Kodunuz: {code}</h1><p>Bu kodu ödeme sayfasında giriniz.</p></body></html>"
    }
    
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            print(f"Email sent successfully to {current_user.email}")
            return jsonify({'success': True, 'message': 'Email sent'})
        else:
            print(f"Brevo Error: {response.text}")
            return jsonify({'success': False, 'message': 'Email sending failed'}), 500
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': 'System error'}), 500


@views.route('/process-payment', methods=['POST'])
@login_required
def process_payment():
    selected_address_id = request.form.get('selected_address')
    saved_card_id = request.form.get('saved_card_id')
    
    if not selected_address_id:
        flash('Lütfen bir teslimat adresi seçin.', category='error')
        return redirect('/checkout')
        
    payment_method = "New Card"
    
    if saved_card_id:
        # Saved Card Flow
        payment_method = "Saved Card"
        email_code = request.form.get('email_code')
        correct_code = session.get('email_code')
        
        if not email_code or email_code != correct_code:
            flash('Email Doğrulama kodu hatalı!', category='error')
            return redirect('/checkout')
            
        # Clear code
        session.pop('email_code', None)
        
    else:
        # New Card Flow (Simulation)
        card_number = request.form.get('cardNumber')
        if not card_number: 
            flash('Ödeme bilgileri eksik.', category='error')
            return redirect('/checkout')

    # If payment successful:
    customer_cart = Cart.query.filter_by(customer_link=current_user.id).all()

    # Check for inactive products before processing
    for item in customer_cart:
        if not item.product.is_active:
            flash(f"'{item.product.product_name}' şu anda temin edilemiyor. Lütfen sepetinizden çıkarın.", category='error')
            return redirect('/cart')
    
    try:
        payment_id = f"PAY-{current_user.id}-{int(datetime.now().timestamp())}"
        
        for item in customer_cart:
            new_order = Order()
            new_order.quantity = item.quantity
            new_order.price = item.product.current_price
            new_order.status = "Onaylanmayı Bekliyor"
            new_order.payment_id = payment_id
            new_order.product_link = item.product_link
            new_order.customer_link = item.customer_link
            
            db.session.add(new_order)
            
            product = Product.query.get(item.product_link)
            product.in_stock -= item.quantity
            
            db.session.delete(item)
            
        db.session.commit()
        flash('Siparişiniz başarıyla alındı!', category='success')
        return redirect('/orders')
        
    except Exception as e:
        print(f"Order error: {e}")
        flash('Sipariş oluşturulurken bir hata oluştu.', category='error')
        return redirect('/checkout')


@views.route('/orders')
@login_required
def order():
    orders = Order.query.filter_by(customer_link=current_user.id).all()
    return render_template('profile_templates/orders.html', orders=orders)


@views.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search')
        items = Product.query.filter(Product.product_name.ilike(f'%{search_query}%')).all()
        return render_template('search.html', items=items, cart=Cart.query.filter_by(customer_link=current_user.id).all()
                           if current_user.is_authenticated else [])

    return render_template('search.html')














@views.route('/category/<string:name>')
@login_required
def get_category(name):
    items = Product.query.filter_by(category=name).all()
    user_cart = Cart.query.filter_by(customer_link=current_user.id).all()
    
    if name == 'electronics':
        return render_template('category_template/electronics.html', items=items, cart=user_cart)
    elif name == 'home_living':
        return render_template('category_template/home_living.html', items=items, cart=user_cart)
    elif name == 'fashion':
        return render_template('category_template/fashion.html', items=items, cart=user_cart)
    elif name == 'gaming':
         return render_template('category_template/gaming.html', items=items, cart=user_cart)
    elif name == 'accessories':
         return render_template('category_template/accessories.html', items=items, cart=user_cart)
    elif name == 'beauty':
         return render_template('category_template/beauty.html', items=items, cart=user_cart)
    elif name == 'sports_outdoor':
         return render_template('category_template/sports_outdoor.html', items=items, cart=user_cart)
    
    elif name == 'most_sellers':
        # Logic for best sellers: Count quantity of products in orders with specific status
        from sqlalchemy import func, desc
        # Assuming 'Teslim Edildi' or similar is the success status. 
        # If 'Teslim Edildi' is strictly required: .filter(Order.status == 'Teslim Edildi')
        # However, for broader display we might initially include confirmed orders too.
        # User explicitly asked for "Teslim Edildi":
        ranked_products = db.session.query(
            Product, func.sum(Order.quantity).label('total_sold')
        ).join(Order, Order.product_link == Product.id)\
         .filter(Order.status == 'Teslim Edildi')\
         .group_by(Product)\
         .order_by(desc('total_sold')).all()
         
        # ranked_products is a list of tuples (Product, total_sold)
        # We just need the product objects, maybe with rank info attached or just ordered list
        items = [p[0] for p in ranked_products]
        return render_template('category_template/most_sellers.html', items=items, cart=user_cart)

    elif name == 'sales':
        # Logic for sales: Sort by discount percentage descending
        all_products = Product.query.filter(Product.previous_price > Product.current_price).all()
        # Calculate discount % and sort
        # Discount = (prev - curr) / prev
        items = sorted(all_products, key=lambda p: (p.previous_price - p.current_price) / p.previous_price, reverse=True)
        return render_template('category_template/sales.html', items=items, cart=user_cart)
    
    # Fallback to electronics or generic if needed, or 404
    return render_template('category_template/electronics.html', items=items, cart=user_cart)
