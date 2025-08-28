from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = 'project_updates.db'


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            '''CREATE TABLE IF NOT EXISTS updates (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   project TEXT NOT NULL,
                   update TEXT NOT NULL,
                   date TEXT NOT NULL
               )'''
        )
        conn.commit()


@app.route('/')
def index():
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            'SELECT date, project, name, update FROM updates ORDER BY date DESC'
        )
        rows = c.fetchall()
    return render_template('dashboard.html', updates=rows)


@app.route('/update', methods=['GET', 'POST'])
def update():
    if request.method == 'POST':
        name = request.form['name']
        project = request.form['project']
        update_text = request.form['update']
        date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute(
                'INSERT INTO updates (name, project, update, date) VALUES (?,?,?,?)',
                (name, project, update_text, date),
            )
            conn.commit()
        return redirect(url_for('dashboard'))
    return render_template('update.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
