# kimlik doğrulama
from flask import Blueprint, render_template, flash, redirect
from .forms import LoginForm, SignUpForm, PasswordChangeForm
from .models import Customer
from . import db
from flask_login import login_user, login_required, logout_user


auth = Blueprint('auth', __name__)


from .validators import validate_signup_data

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
            flash('Kayıt olundu giriş yapabilirsiniz')
            return redirect('/login')
        except Exception as e:
            print(e)
            flash(f'Hata oluştu: {str(e)}')

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
                login_user(customer)
                return redirect('/shop')
            else:
                flash('Incorrect Password')

        else:
            flash('Account does not exist please Sign Up')

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
    return render_template('profile.html', customer=customer)


@auth.route('/change-password/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def change_password(customer_id):
    form = PasswordChangeForm()
    customer = Customer.query.get(customer_id)
    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data
        confirm_new_password = form.confirm_new_password.data

        if customer.verify_password(current_password):
            if new_password == confirm_new_password:
                customer.password = confirm_new_password
                db.session.commit()
                flash('Password Updated Successfully')
                return redirect(f'/profile/{customer.id}')
            else:
                flash('New Passwords do not match!!')

        else:
            flash('Current Password is Incorrect')

    return render_template('change_password.html', form=form)







