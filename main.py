# entry point for the guestbook application.
import sqlite3
from flask import *
from contextlib import closing


# create and init our app.
app = Flask(__name__)
app.config.from_object("config")


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


# for each request, init a db connection before and and close it afterwards.
@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


# show all guestbook entries.
@app.route('/')
def show_guestbook():
    cur = g.db.execute('select name, body, id from entries order by id desc')
    entries = [dict(name=row[0], body=row[1], id=row[2]) for row in cur.fetchall()]
    return render_template('show_entries.html', entries=entries)


# let the admin login.
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash("Login successful!")
            return redirect(url_for('show_guestbook'))
    return render_template('login.html', error=error)


# let the admin log out.
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_guestbook'))


# let anyone add a new entry to the database.
@app.route('/add', methods=['POST'])
def add_entry():
    g.db.execute('insert into entries (name, body) values (?, ?)',
                 [request.form['name'], request.form['body']])
    g.db.commit()
    flash('Signature added! Thank you.')
    return redirect(url_for('show_guestbook'))


# let admin delete entries.
@app.route('/delete', methods=['POST'])
def delete_entry():
    if not session.get('logged_in'):
        # action forbidden
        abort(401)

    print "The id is " + request.form['id']
    g.db.execute('delete from entries where id=?',
                 [request.form['id']])
    g.db.commit()
    flash('Successfully deleted entry.')
    return redirect(url_for('show_guestbook'))

if __name__ == '__main__':
    app.run()
