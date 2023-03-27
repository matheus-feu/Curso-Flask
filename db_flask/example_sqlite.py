import sqlite3

from flask import Flask, g, render_template

app = Flask(__name__)

DATABASE = 'database.db'


# Abrir conexão com o banco de dados, antes do processamento de cada requisição
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


# Fechar conexão com o banco de dados, após o processamento de cada requisição
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    cur = get_db().cursor()
    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    return render_template('index.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)
