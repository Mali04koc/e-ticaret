# kimlik doğrulama
from flask import Blueprint, render_template, flash, redirect, request
from .forms import LoginForm, SignUpForm, PasswordChangeForm, AddressForm, ChangeEmailForm, ChangePhoneForm
from .models import Customer, Address, Card, Coupon
from . import db
from flask_login import login_user, login_required, logout_user, current_user
from .validators import validate_signup_data
from sqlalchemy import or_


auth = Blueprint('auth', __name__)

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        email = form.email.data
        phone = form.phone.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        password1 = form.password1.data
        password2 = form.password2.data

        # Custom Validation
        is_valid, error_message = validate_signup_data(email, phone, password1, password2)
        
        if not is_valid:
            flash(error_message)
            return render_template('signup.html', form=form)

        # Check for existing user with same email or phone
        user_by_email = Customer.query.filter_by(email=email).first()
        if user_by_email:
            flash('Bu email adresi ile daha önce kayıt olunmuş.', category='error')
            return render_template('signup.html', form=form)
        
        user_by_phone = Customer.query.filter_by(phone=phone).first()
        if user_by_phone:
            flash('Bu telefon numarası ile daha önce kayıt olunmuş.', category='error')
            return render_template('signup.html', form=form)

        # If validations pass, proceed to check DB uniqueness and create user
        new_customer = Customer()
        new_customer.email = email
        new_customer.phone = phone
        new_customer.first_name = first_name
        new_customer.last_name = last_name
        new_customer.password = password2

        try:
            db.session.add(new_customer)
            db.session.commit()
            flash('Kayıt olundu giriş yapabilirsiniz', category='success')
            return redirect('/login')
        except Exception as e:
            print(e)
            flash('Bir hata oluştu, lütfen tekrar deneyin.', category='error')

    return render_template('signup.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data
        password = form.password.data

        # Check against email OR phone
        customer = Customer.query.filter((Customer.email == identifier) | (Customer.phone == identifier)).first()

        if customer:
            if customer.verify_password(password=password):
                if customer.is_banned:
                    flash('Hesabınız erişime kapatılmıştır. Yönetici ile iletişime geçin.', category='error')
                    return render_template('login.html', form=form)
                
                login_user(customer)
                if customer.id == 1:
                    return redirect('/admin-page')
                return redirect('/shop')
            else:
                flash('Incorrect Password', category='error')

        else:
            flash('Böyle bir kullanıcı bulunamadı.Kayıt olun.', category='error')

    return render_template('login.html', form=form)


@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def log_out():
    logout_user()
    return redirect('/')


@auth.route('/profile/<int:customer_id>')
@login_required
def profile(customer_id):
    customer = Customer.query.get(customer_id)
    return render_template('profile_templates/profile.html', customer=customer)


@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_new_password = form.confirm_new_password.data

        if current_user.verify_password(current_password):
            if new_password == confirm_new_password:
                current_user.password = confirm_new_password
                db.session.commit()
                flash('Parola Başarıyla Güncellendi')
                return redirect(f'/profile/{current_user.id}')
            else:
                flash('Yeni Parolalar Eşleşmiyor!!')

        else:
            flash('Mevcut Parola Hatalı')

    return render_template('profile_templates/change_password.html', form=form)


@auth.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        new_email = form.new_email.data
        password = form.password.data
        
        if current_user.verify_password(password):
            existing_email = Customer.query.filter_by(email=new_email).first()
            if existing_email:
                flash('Bu e-posta adresi zaten kullanımda.')
            else:
                current_user.email = new_email
                db.session.commit()
                flash('E-posta adresiniz güncellendi.')
                return redirect(f'/profile/{current_user.id}')
        else:
            flash('Şifre hatalı.')

    return render_template('profile_templates/change_email.html', form=form)


@auth.route('/change-phone', methods=['GET', 'POST'])
@login_required
def change_phone():
    form = ChangePhoneForm()
    if form.validate_on_submit():
        new_phone = form.new_phone.data
        password = form.password.data
        
        if current_user.verify_password(password):
            existing_phone = Customer.query.filter_by(phone=new_phone).first()
            if existing_phone:
                flash('Bu telefon numarası zaten kullanımda.')
            else:
                current_user.phone = new_phone
                db.session.commit()
                flash('Telefon numaranız güncellendi.')
                return redirect(f'/profile/{current_user.id}')
        else:
            flash('Şifre hatalı.')

    return render_template('profile_templates/change_phone.html', form=form)


@auth.route('/address-book', methods=['GET', 'POST'])
@login_required
def address_book():
    form = AddressForm()
    addresses = Address.query.filter_by(customer_link=current_user.id).all()
    
    if form.validate_on_submit():
        new_address = Address(
            customer_link=current_user.id,
            address_title=form.address_title.data,
            general_address=form.general_address.data,
            city=form.city.data,
            district=form.district.data,
            zip_code=form.zip_code.data,
            recipient_name=form.recipient_name.data,
            phone=form.phone.data
        )
        try:
            db.session.add(new_address)
            db.session.commit()
            flash('Yeni adres başarıyla eklendi.', category='success')
            return redirect('/address-book')
        except Exception as e:
            print(e)
            flash('Adres eklenirken bir hata oluştu.', category='error')
            
    return render_template('profile_templates/adres.html', form=form, addresses=addresses)


@auth.route('/my-coupons')
@login_required
def my_coupons():
    # Global coupons OR Private coupons for this user
    coupons = Coupon.query.filter(
        or_(
            Coupon.target_customer_id == None, 
            Coupon.target_customer_id == current_user.id
        ),
        Coupon.is_active == True
    ).all()
    return render_template('profile_templates/coupons.html', coupons=coupons)


@auth.route('/saved-cards')
@login_required
def saved_cards():
    cards = Card.query.filter_by(customer_link=current_user.id).all()
    return render_template('profile_templates/saved_cards.html', cards=cards)


@auth.route('/add-card', methods=['POST'])
@login_required
def add_card():
    card_name = request.form.get('card_name')
    card_number = request.form.get('card_number') # 16 digits
    expiry_date = request.form.get('expiry_date')
    
    # Simple validation
    if len(card_number) < 16:
        flash('Geçersiz kart numarası.', category='error')
        return redirect('/saved-cards')
        
    masked = "**** **** **** " + card_number[-4:]
    
    new_card = Card(
        customer_link=current_user.id,
        card_name=card_name,
        masked_number=masked,
        expiry_date=expiry_date
    )
    
    try:
        db.session.add(new_card)
        db.session.commit()
        flash('Kart başarıyla kaydedildi.', category='success')
    except Exception as e:
        print(e)
        flash('Kart kaydedilirken hata oluştu.', category='error')
        
    return redirect('/saved-cards')


@auth.route('/delete-card/<int:id>')
@login_required
def delete_card(id):
    card = Card.query.get(id)
    if card and card.customer_link == current_user.id:
        db.session.delete(card)
        db.session.commit()
        flash('Kart silindi.', category='success')
    else:
        flash('Kart bulunamadı veya işlem yetkiniz yok.', category='error')
        
    return redirect('/saved-cards')







