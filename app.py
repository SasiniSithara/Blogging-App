from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

app = Flask(__name__)
# app.debug = True

# config mysql
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = os.environ.get('MYSQL_CURSORCLASS')

# init mysql
mysql = MySQL(app)

# Articles = Articles()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    # create cursor for Database
    cur = mysql.connection.cursor()

    #Execute following SQL command to get all the articles
    result = cur.execute("SELECT * FROM articles")

    # To fetch all the articles in dictionary format
    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html')
    
    # Close the connection
    cur.close()

@app.route('/article/<string:id>/')
def article(id):
    # create cursor for Database
    cur = mysql.connection.cursor()

    # Get Article by Id
    result = cur.execute("SELECT * FROM articles where id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO users(name, email, username, password) VALUES (%s, %s, %s, %s)", (name, email, username, password))

        mysql.connection.commit()

        cur.close()

        flash('You are successfully registered and can login', 'success')

        return redirect(url_for('index'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE username= %s", [username])

        if ( result>0 ):
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # compare passwords
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username

                flash ('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_Authenticated(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash ('Unauthorised, Plese login', 'danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/logout')
@is_Authenticated
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@is_Authenticated
def dashboard():
    # create cursor for Database
    cur = mysql.connection.cursor()

    #Execute following SQL command to get all the articles
    result = cur.execute("SELECT * FROM articles")

    # To fetch all the articles in dictionary format
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html')
    
    # Close the connection
    cur.close()

class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


# Add article
@app.route('/add_article', methods = ['GET', 'POST'])
@is_Authenticated
def add_article():
    form = ArticleForm(request.form)
    if(request.method == 'POST' and form.validate()):
        title = form.title.data
        body = form.body.data

        # Create cursor for storing the article
        cur = mysql.connection.cursor()

        # Execute the SQL command
        cur.execute("INSERT INTO articles(title, body, author) VALUES (%s, %s, %s)", (title, body, session['username']))

        # Commit the changes to the Database
        mysql.connection.commit()

        # Close connection
        cur.close()

        # Show a flash success message
        flash ('Article Created', 'success')

        # redirect to the dashboard
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)

# Edit article
@app.route('/edit_article/<string:id>', methods = ['GET', 'POST'])
@is_Authenticated
def edit_article(id):
    # create cursor for Database
    cur = mysql.connection.cursor()

    # Get Article by Id
    result = cur.execute("SELECT * FROM articles where id = %s", [id])

    article = cur.fetchone()

    # get form
    form = ArticleForm(request.form)

    # Populate Article form fields
    form.title.data = article['title']
    form.body.data = article['body']


    if(request.method == 'POST' and form.validate()):
        # title = form.title.data --> It doesn't let the article to be updated
        # body = form.body.data
        title = request.form['title']
        body = request.form['body']
        # Create cursor for storing the article
        cur = mysql.connection.cursor()

        # Execute the SQL command
        cur.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title, body, id))

        # Commit the changes to the Database
        mysql.connection.commit()

        # Close connection
        cur.close()

        # Show a flash success message
        flash ('Article Updated', 'success')

        # redirect to the dashboard
        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


# Delete article
@app.route('/delete_article/<string:id>', methods=["POST"])
@is_Authenticated
def delete_article(id):
    # create cursor for Database
    cur = mysql.connection.cursor()

    # Get Article by Id
    cur.execute("DELETE FROM articles where id = %s", [id])

    # Commit the changes to the Database
    mysql.connection.commit()

    # Close connection
    cur.close()

    # Show a flash success message
    flash ('Article deleted', 'success')

    # redirect to the dashboard
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key = 'secret989'
    app.run(debug=True)