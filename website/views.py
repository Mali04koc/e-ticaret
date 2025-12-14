from flask import Blueprint

views = Blueprint('views', __name__) # bu viewsın url endpointleri içerdiğini söyler

# url endpointlerimizi ve view fonksiyonlarımızı barındırır

@views.route('/') #home sayfamıza geldiğini gösterir,def home(views.route(/)): views zaten blueprintim nesnemiz.Decorator ile fonksiyon içine blueprint nesnesi gönderilir.
def home():
    return "Anasayfaya hoşgeldiniz!"