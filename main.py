from website import create_app

app= create_app()

if __name__ == '__main__':
    app.run(debug=True) # debug true ile source kodda her değişiklik yaptığımızda baştan run edicek appi