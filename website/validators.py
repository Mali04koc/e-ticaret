import re

def validate_signup_data(email, phone, password, confirm_password):
    """
    Validates user signup data.
    Returns: (is_valid, message)
    """

    # 1. Email Validation
    # Simple regex for email format
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return False, "Geçersiz email adresi lütfen kontrol ediniz."

    # 2. Phone Validation
    # Must contain 11 digits and start with '05'
    # Remove any spaces or dashes just in case, though input type='tel' might send them
    clean_phone = phone.replace(" ", "").replace("-", "")
    
    if not clean_phone.isdigit():
        return False, "Telefon numarası sadece rakamlardan oluşmalıdır."
    
    if len(clean_phone) != 11:
        return False, "Telefon numarası 11 haneli olmalıdır."
    
    if not clean_phone.startswith("05"):
        return False, "Telefon numarası '05' ile başlamalıdır."

    # 3. Password Validation
    if password != confirm_password:
        return False, "Girilen şifreler birbiriyle uyuşmuyor."

    if len(password) < 6:
        return False, "Şifre en az 6 karakter olmalıdır."

    return True, "Başarılı"
