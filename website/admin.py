# websitemizin admin sayfasıyla ilgilenecek

from flask import Blueprint, render_template, flash, send_from_directory, redirect, request
from flask_login import login_required, current_user
from .forms import ShopItemsForm, OrderForm
from werkzeug.utils import secure_filename
from .models import Product, Order, Customer, Coupon
from . import db
import os


admin = Blueprint('admin', __name__)


@admin.context_processor
def inject_pending_orders_count():
    if current_user.is_authenticated and current_user.id == 1:
        pending_count = Order.query.filter_by(status='Onaylanmayı Bekliyor').count()
        return dict(pending_orders_count=pending_count)
    return dict(pending_orders_count=0)


@admin.route('/media/<path:filename>')
def get_image(filename):
    return send_from_directory('../media', filename)


@admin.route('/view-customers')
@login_required
def view_customers():
    if current_user.id == 1:
        customers = Customer.query.filter(Customer.id != 1).all() # Exclude admin
        return render_template('admin_template/view_customers.html', customers=customers)
    return render_template('404.html')


@admin.route('/toggle-ban/<int:customer_id>')
@login_required
def toggle_ban(customer_id):
    if current_user.id == 1:
        customer = Customer.query.get(customer_id)
        if customer:
            customer.is_banned = not customer.is_banned
            db.session.commit()
            status = "yasaklandı" if customer.is_banned else "erişime açıldı"
            flash(f'Kullanıcı {status}.')
        return redirect('/view-customers')
    return render_template('404.html')


@admin.route('/manage-coupons')
@login_required
def manage_coupons():
    if current_user.id == 1:
        coupons = Coupon.query.all()
        return render_template('admin_template/manage_coupons.html', coupons=coupons)
    return render_template('404.html')


@admin.route('/define-coupon', methods=['GET', 'POST'])
@login_required
def define_coupon():
    if current_user.id != 1:
        return render_template('404.html')

    customers = Customer.query.filter(Customer.id != 1).all()
    
    if request.method == 'POST':
        code_input = request.form.get('code') # e.g. SUMMER%10 or WELCOME50
        target_id = request.form.get('target_customer') # 'all' or ID
        
        if not code_input:
            flash('Kupon kodu giriniz.', category='error')
            return redirect('/define-coupon')
            
        # Parse Logic
        is_percentage = False
        discount_val = 0.0
        
        try:
            if '%' in code_input:
                is_percentage = True
                # Expecting TEXT%NUMBER e.g. SUMMER%20
                parts = code_input.split('%')
                discount_val = float(parts[-1])
            else:
                is_percentage = False
                # Expecting TEXTNUMBER e.g. WELCOME50
                # We need to extract the number from the end
                import re
                match = re.search(r'(\d+)$', code_input)
                if match:
                    discount_val = float(match.group(1))
                else:
                    flash('Kupon kodunda indirim miktarı bulunamadı (Örn: SUMMER%20 veya WELCOME50)', category='error')
                    return redirect('/define-coupon')
        except ValueError:
            flash('Geçersiz indirim formatı.', category='error')
            return redirect('/define-coupon')

        # Create Coupon
        new_coupon = Coupon(
            code=code_input,
            discount_value=discount_val,
            is_percentage=is_percentage,
            target_customer_id = int(target_id) if target_id and target_id != 'all' else None
        )
        
        try:
            db.session.add(new_coupon)
            db.session.commit()
            flash(f'Kupon tanımlandı: {code_input}', category='success')
            return redirect('/manage-coupons')
        except Exception as e:
            print(e)
            flash('Kupon oluşturulurken hata (Kod benzersiz olmalı).', category='error')
    
    # Pre-select customer if passed in args
    selected_customer_id = request.args.get('customer_id')
    return render_template('admin_template/define_coupon.html', customers=customers, selected=selected_customer_id)


@admin.route('/delete-coupon/<int:id>')
@login_required
def delete_coupon(id):
    if current_user.id == 1:
        coupon = Coupon.query.get(id)
        db.session.delete(coupon)
        db.session.commit()
        flash('Kupon silindi.')
        return redirect('/manage-coupons')
    return render_template('404.html')


@admin.route('/add-shop-items', methods=['GET', 'POST'])
@login_required
def add_shop_items():
    if current_user.id == 1:
        form = ShopItemsForm()

        if form.validate_on_submit():
            product_name = form.product_name.data
            current_price = form.current_price.data
            in_stock = form.in_stock.data
            category = form.category.data
            
            # For new items, previous_price is same as current (no discount initially)
            previous_price = current_price
            flash_sale = None

            file = form.product_picture.data
            file_name = secure_filename(file.filename)
            
            # Save to static/uploads
            import os
            from flask import current_app
            
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            file_path = os.path.join(upload_folder, file_name)
            file.save(file_path)

            new_shop_item = Product()
            new_shop_item.product_name = product_name
            new_shop_item.current_price = current_price
            new_shop_item.previous_price = previous_price
            new_shop_item.in_stock = in_stock
            new_shop_item.flash_sale = flash_sale
            new_shop_item.category = category

            # Store web-accessible path in DB
            new_shop_item.product_picture = f'/static/uploads/{file_name}'

            try:
                db.session.add(new_shop_item)
                db.session.commit()
                flash(f'{product_name} başarıyla eklendi')
                print('Product Added')
                return render_template('admin_template/add_shop_items.html', form=form)
            except Exception as e:
                print(e)
                flash('Ürün Eklenemedi!!')

        return render_template('admin_template/add_shop_items.html', form=form)

    return render_template('404.html')


@admin.route('/shop-items', methods=['GET', 'POST'])
@login_required
def shop_items():
    if current_user.id == 1:
        items = Product.query.order_by(Product.date_added.desc()).all()
        return render_template('shop_items.html', items=items)
    return render_template('404.html')


@admin.route('/update-products-list')
@login_required
def update_products_list():
    if current_user.id == 1:
        items = Product.query.order_by(Product.date_added.desc()).all()
        return render_template('admin_template/update_products_list.html', items=items)
    return render_template('404.html')


@admin.route('/update-product-price/<int:item_id>', methods=['POST'])
@login_required
def update_product_price(item_id):
    if current_user.id == 1:
        new_price = request.form.get('new_price')
        new_stock = request.form.get('new_stock')
        
        if new_price:
            try:
                new_price = float(new_price)
                if new_stock:
                    new_stock = int(new_stock)
                
                if new_price < 0 or (new_stock is not None and new_stock < 0):
                    flash('Fiyat ve stok 0 dan küçük olamaz.', category='error')
                    return redirect('/update-products-list')
                
                product = Product.query.get(item_id)
                if product:
                    # Logic: New Price -> Current Price, Old Current -> Previous Price
                    # Only if changed
                    if new_price != product.current_price:
                        product.previous_price = product.current_price
                        product.current_price = new_price
                        
                        # Calculate Discount
                        if product.current_price < product.previous_price:
                            discount = ((product.previous_price - product.current_price) / product.previous_price) * 100
                            product.flash_sale = f"%{int(discount)} İndirim"
                        else:
                            product.flash_sale = None
                    
                    if new_stock is not None:
                        product.in_stock = new_stock
                        
                    db.session.commit()
                    flash(f'{product.product_name} güncellendi.', category='success')
                    
            except ValueError:
                flash('Geçersiz fiyat veya stok değeri.', category='error')
            except Exception as e:
                print(e)
                flash('Güncelleme hatası.', category='error')
                
        return redirect('/update-products-list')
    return render_template('404.html')


@admin.route('/update-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def update_item(item_id):
    if current_user.id == 1:
        form = ShopItemsForm()

        item_to_update = Product.query.get(item_id)

        form.product_name.render_kw = {'placeholder': item_to_update.product_name}
        form.previous_price.render_kw = {'placeholder': item_to_update.previous_price}
        form.current_price.render_kw = {'placeholder': item_to_update.current_price}
        form.in_stock.render_kw = {'placeholder': item_to_update.in_stock}
        form.flash_sale.render_kw = {'placeholder': item_to_update.flash_sale}

        if form.validate_on_submit():
            product_name = form.product_name.data
            current_price = form.current_price.data
            previous_price = form.previous_price.data
            in_stock = form.in_stock.data
            flash_sale = form.flash_sale.data

            file = form.product_picture.data

            file_name = secure_filename(file.filename)
            file_path = f'./media/{file_name}'

            file.save(file_path)

            try:
                Product.query.filter_by(id=item_id).update(dict(product_name=product_name,
                                                                current_price=current_price,
                                                                previous_price=previous_price,
                                                                in_stock=in_stock,
                                                                flash_sale=flash_sale,
                                                                product_picture=file_path))

                db.session.commit()
                flash(f'{product_name} başarıyla güncellendi')
                print('Product Upadted')
                return redirect('/shop-items')
            except Exception as e:
                print('Ürün güncellenemedi', e)
                flash('Ürün güncellenemedi!!!')

        return render_template('update_item.html', form=form)
    return render_template('404.html')


@admin.route('/delete-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def delete_item(item_id):
    if current_user.id == 1:
        try:
            item_to_delete = Product.query.get(item_id)
            # Soft Delete / Toggle Status
            item_to_delete.is_active = not item_to_delete.is_active
            db.session.commit()
            
            status_text = "Pasife alındı" if not item_to_delete.is_active else "Aktif edildi"
            flash(f'Ürün durumu güncellendi: {status_text}', category='success')
            
            # Check referrer to redirect back to the correct page
            if 'update-products-list' in request.referrer:
                return redirect('/update-products-list')
            return redirect('/shop-items')
            
        except Exception as e:
            print('Item update failed', e)
            flash('İşlem başarısız!!')
        return redirect('/shop-items')

    return render_template('404.html')


@admin.route('/view-orders')
@login_required
def order_view():
    if current_user.id == 1:
        orders = Order.query.all()
        return render_template('admin_template/view_orders.html', orders=orders)
    return render_template('404.html')


@admin.route('/update-order/<int:order_id>', methods=['GET', 'POST'])
@login_required
def update_order(order_id):
    if current_user.id == 1:
        form = OrderForm()
        order = Order.query.get(order_id)

        if form.validate_on_submit():
            new_status = form.order_status.data
            
            # Stock Reduction Logic
            if new_status == 'Teslim Edildi' and order.status != 'Teslim Edildi':
                product = Product.query.get(order.product_link)
                if product:
                    product.in_stock -= order.quantity
                    if product.in_stock < 0:
                        product.in_stock = 0
                    flash(f'Stok güncellendi: {product.product_name} (Yeni Stok: {product.in_stock})', category='info')

            order.status = new_status

            try:
                db.session.commit()
                flash(f'Sipariş {order_id} başarıyla güncellendi ({new_status})')
                return redirect('/view-orders')
            except Exception as e:
                print(e)
                flash(f'Sipariş güncellenemedi: {e}', category='error')
                return redirect('/view-orders')

        return render_template('admin_template/order_update.html', form=form)

    return render_template('404.html')


@admin.route('/most-sellers')
@login_required
def most_sellers():
    if current_user.id == 1:
        from sqlalchemy import func
        
        # Query: Sum quantity of users orders where status is 'Teslim Edildi', grouped by product
        results = db.session.query(
            Order.product_link, 
            func.sum(Order.quantity).label('total_sold')
        ).filter(Order.status == 'Teslim Edildi').group_by(Order.product_link).order_by(func.sum(Order.quantity).desc()).all()
        
        # Prepare data for template
        most_selling_products = []
        for r in results:
            product = Product.query.get(r.product_link)
            if product:
                most_selling_products.append({
                    'product': product,
                    'total_sold': r.total_sold,
                    # Optional: Calculate total revenue if prices didn't change too much, or stored in order
                    # For now just showing quantity
                })
                
        return render_template('admin_template/most_sellers.html', products=most_selling_products)
    return render_template('404.html')


@admin.route('/customers')
@login_required
def display_customers():
    if current_user.id == 1:
        customers = Customer.query.all()
        return render_template('customers.html', customers=customers)
    return render_template('404.html')


@admin.route('/admin-page')
@login_required
def admin_page():
    if current_user.id == 1:
        return render_template('admin_template/admin_index.html')
    return render_template('404.html')









