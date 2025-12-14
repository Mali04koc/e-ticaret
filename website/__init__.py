from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'kkasjıdkapsdf121341şfld' # sessionları şifreleyen anahtar

    
    return app

# websitemizin python package sayfası