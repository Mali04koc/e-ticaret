#formsları kontrol edicek login
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, PasswordField, EmailField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, length, NumberRange
from flask_wtf.file import FileField, FileRequired


class SignUpForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    password1 = PasswordField('Enter Your Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Your Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
    # This field will accept either Email or Phone
    identifier = StringField('Email or Phone', validators=[DataRequired()])
    password = PasswordField('Enter Your Password', validators=[DataRequired()])
    submit = SubmitField('Log in')


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Şifreniz', validators=[DataRequired(), length(min=6)])
    new_password = PasswordField('Yeni Şifre', validators=[DataRequired(), length(min=6)])
    confirm_new_password = PasswordField('Yeni Şifreyi Onayla', validators=[DataRequired(), length(min=6)])
    change_password = SubmitField('Şifreyi Değiştir')


class ShopItemsForm(FlaskForm):
    product_name = StringField('Name of Product', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('home_living', 'Ev & Yaşam'),
        ('fashion', 'Moda & Giyim'),
        ('electronics', 'Elektronik'),
        ('gaming', 'Oyun & Hobi'),
        ('accessories', 'Saat & Aksesuar'),
        ('beauty', 'Kozmetik & Kişisel Bakım'),
        ('sports_outdoor', 'Spor & Outdoor')
    ], validators=[DataRequired()])
    current_price = FloatField('Current Price', validators=[DataRequired()])
    previous_price = FloatField('Previous Price', validators=[DataRequired()])
    in_stock = IntegerField('In Stock', validators=[DataRequired(), NumberRange(min=0)])
    product_picture = FileField('Product Picture', validators=[DataRequired()])

    add_product = SubmitField('Ürün Ekle')
    update_product = SubmitField('Güncelle')


class OrderForm(FlaskForm):
    order_status = SelectField('Order Status', choices=[
        ('Onaylanmayı Bekliyor', 'Onaylanmayı Bekliyor'),
        ('Onaylandı', 'Onaylandı'),
        ('Kargoya Verildi', 'Kargoya Verildi'),
        ('Teslim Edildi', 'Teslim Edildi'),
        ('İptal Edildi', 'İptal Edildi')
    ])

    update = SubmitField('Update Status')


class AddressForm(FlaskForm):
    address_title = StringField('Adres Başlığı', validators=[DataRequired()])
    general_address = StringField('Adres Detayı', validators=[DataRequired()])
    city = StringField('Şehir', validators=[DataRequired()])
    district = StringField('İlçe', validators=[DataRequired()])
    zip_code = StringField('Posta Kodu', validators=[DataRequired()])
    recipient_name = StringField('Teslim Alacak Kişi', validators=[DataRequired()])
    phone = StringField('Telefon Numarası', validators=[DataRequired()])
    submit = SubmitField('Adres Kaydet')


class ChangeEmailForm(FlaskForm):
    new_email = EmailField('Yeni E-Posta', validators=[DataRequired()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    submit = SubmitField('E-Posta Güncelle')


class ChangePhoneForm(FlaskForm):
    new_phone = StringField('Yeni Telefon Numarası', validators=[DataRequired()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    submit = SubmitField('Telefon Numarası Güncelle')





