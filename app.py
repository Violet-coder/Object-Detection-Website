import sqlite3
from flask import Flask, request, render_template, url_for, redirect, g, flash, get_flashed_messages, session , jsonify
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf.file import FileField, FileRequired, FileAllowed


import thumbnail, object_detection
from model import User, User_photo
from savephoto import insert_user_photo_to_db, query_user_photo_by_name
from datetime import timedelta
import hashlib
import os


app = Flask(__name__)
app.config["DATABASE"] = 'database.db'
app.config["SECRET_KEY"] = '1779'  # The secret key to open the cookie.
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)


def connect_db():
    """Connect to specific database"""
    db = sqlite3.connect(app.config["DATABASE"])
    return db


def init_db():
    with app.app_context():
        db = connect_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


def insert_user_to_db(user):
    sql_insert = "INSERT INTO users(name, email, password, salt, photo_id) VALUES (?, ?, ?, ? , ?)"
    args = [user.name, user.email, user.password, user.salt,user.photo_id]
    g.db.execute(sql_insert, args)
    g.db.commit()


def query_users_from_db():
    users = []
    sql_select = "SELECT * FROM users"
    args = []
    cur = g.db.execute(sql_select, args)
    for item in cur.fetchall():
        user = User()
        user.fromList(item[1:])
        users.append(user)
    return users


def query_user_by_name(username):
    sql_select = "SELECT * FROM users WHERE name = ?"
    args = [username]
    cur = g.db.execute(sql_select, args)
    items = cur.fetchall()
    if len(items) < 1:
        return None
    else:
        first_item = items[0]
        user = User()
        user.fromList(first_item[1:])
    return user


def delete_user_by_name(username):
    delete_sql = "DELETE FROM users WHERE name = ? "
    args = [username]
    g.db.execute(delete_sql, args)
    g.db.commit()


def update_by_name(new_photoid, username):
    sql_update = "UPDATE users SET photo_id= ? WHERE name = ?"
    args = [new_photoid, username]
    g.db.execute(sql_update, args)
    g.db.commit()


def hash(password, salt):
    key = hashlib.pbkdf2_hmac(
        'sha256',  # The hash digest algorithm for HMAC
        password.encode('utf-8'),  # Convert the password to bytes
        salt,  # Provide the salt
        100000  # It is recommended to use at least 100,000 iterations of SHA-256
    )
    return key


@app.route('/register/', methods=['GET', 'POST'])
def user_register():
    if request.method == "POST":
        user = User()
        user.name = request.form["username"]
        user.email = request.form["email"]
        # To see if the user has already exists
        if len(user.name) > 100:
            flash("The length of username is illegal!", category='error')
            return render_template('register.html')
        user_x = query_user_by_name(user.name)
        if user_x:
            flash("The name already exists!", category='error')
            return render_template('register.html')
        if request.form["password_confirm"] != request.form["password"]:
            flash("Two passwords are inconsistent!", category='error')
            return render_template('register.html')
        salt = os.urandom(32)
        user.salt = salt
        user.password = hash(request.form["password"], salt)
        # If this is a new user, operate insert operation
        user.photo_id = 0
        insert_user_to_db(user)
        flash("You have successfully registered!", category='ok')
        return redirect(url_for("user_login", username=user.name))
    return render_template('register.html')

@app.route('/api/register/', methods=['POST'])
def user_register_api():
    user = User()
    user.name = request.form["username"]
    user.email = "1779@uoft.com"
    # To see if the user has already exists
    if len(user.name) > 100:
        return jsonify({"Error":"The length of username is illegal!"}), 400
    user_x = query_user_by_name(user.name)
    if user_x:
        return jsonify({"Error":"The name already exists!"}), 400
    #if request.form["password_confirm"] != request.form["password"]:
        # return jsonify({"Error":"Two passwords are inconsistent!"}), 401
    salt = os.urandom(32)
    user.salt = salt
    user.password = hash(request.form["password"], salt)
    # If this is a new user, operate insert operation
    user.photo_id = 0
    insert_user_to_db(user)
    return jsonify({"Success":"You have successfully registered!"})


@app.route('/', methods=['GET', 'POST'])
def user_login():
    if 'username' in session:
        return redirect(url_for('user_visit', username=session["username"]))
    if request.method == "POST":
        username = request.form["username"]
        userpassword = request.form["password"]
        user_x = query_user_by_name(username)
        # examine if this username exists
        if not user_x:
            flash("The username does not exist. Please try again.", category='error')
            return render_template('login.html')
        else:
            new_key = hash(userpassword, user_x.salt)
            if new_key != user_x.password:
                flash("Password error.", category='error')
                return render_template('login.html')
            else:
                session["username"] = user_x.name
                session['authenticated'] = True  # login status
                session['error'] = None
                return redirect(url_for('user_visit', username=session["username"]))
    return render_template('login.html')


@app.route('/logout')
def user_logout():
    session.pop("username", None)
    session.pop('authenticated', None)
    if 'error' in session:
        session['error'] = None
    return redirect(url_for('user_login'))



class UploadForm(FlaskForm):
    file = FileField('Upload your photo: ',
                     validators=[FileRequired(),
                                 FileAllowed(['png', 'jpg', 'JPG', 'PNG', 'jpeg', 'JPEG'], 'Images only!')])
    submit = SubmitField('Submit')

@app.route('/upload/<username>', methods=['GET', 'POST'])
def upload_photo(username):
    if 'username' not in session:
        session['error'] = 'Log in first please!'
        return redirect(url_for('user_login'))
    form = UploadForm()
    if request.method=='POST':
        if form.validate_on_submit():
            base_path = os.path.dirname(__file__)
            size = form.file.data.content_length
            print(size)
            if size/float(1024*1024) < 5:
                print('1')
                user = User()
                user.name = session["username"]
                photo_id = query_user_by_name(user.name).photo_id
                photo_id = photo_id + 1
                update_by_name(photo_id, username)
                photo_address = os.path.join(base_path, 'static/org_photo', username + str(photo_id) + ".jpg")
                form.file.data.save(photo_address)
                photo_detected_address = os.path.join(base_path, 'static/det_photo', username + str(photo_id) + ".jpg")
                photo_thumbnail_address = os.path.join(base_path, 'static/thumbnail', username + str(photo_id) + ".jpg")
                object_detection.object_detection(photo_address, photo_detected_address)
                thumbnail.Thumbnail(photo_address, photo_thumbnail_address)
                user_photo = User_photo()
                user_photo.name = session["username"]
                user_photo.org_photo = photo_address
                user_photo.det_photo = photo_detected_address
                user_photo.thumbnail = photo_thumbnail_address
                insert_user_photo_to_db(user_photo)
                return redirect(url_for('user_visit', username=username))
            else:
                flash('Please upload image under 5M.')
                return render_template("upload_page.html", form=form, username=username)
        else:
            flash('Image only.')
            return render_template("upload_page.html", form=form, username=username)
    return render_template("upload_page.html", form=form, username=username)

@app.route('/api/upload', methods=['POST'])
def upload_photo_api( ):
    username = request.form["username"]
    userpassword = request.form["password"]
    file = request.files['file']
    size = len(file.read())
    user_x = query_user_by_name(username)
    # examine if this username exists
    if not user_x:
        return jsonify({"Error": "The username does not exist. Please try again."}), 400
    else:
        new_key = hash(userpassword, user_x.salt)
        if new_key != user_x.password:
            return jsonify({"Error": "Password error."}), 400
        if size/float(1024*1024) > 5:
            return jsonify({"Error": "Please do not upload unreasonably big files."}), 400
        else:
            base_path = os.path.dirname(__file__)
            user = User()
            user.name = username
            photo_id = query_user_by_name(user.name).photo_id
            photo_id = photo_id + 1
            update_by_name(photo_id, username)
            photo_address = os.path.join(base_path, 'static/org_photo', username + str(photo_id) + ".jpg")
            file.save(photo_address)
            photo_detected_address = os.path.join(base_path, 'static/det_photo', username + str(photo_id) + ".jpg")
            photo_thumbnail_address = os.path.join(base_path, 'static/thumbnail', username + str(photo_id) + ".jpg")
            object_detection.object_detection(photo_address, photo_detected_address)
            thumbnail.Thumbnail(photo_address, photo_thumbnail_address)
            user_photo = User_photo()
            user_photo.name = username
            user_photo.org_photo = photo_address
            user_photo.det_photo = photo_detected_address
            user_photo.thumbnail = photo_thumbnail_address
            insert_user_photo_to_db(user_photo)
            return jsonify({"Success": "You have uploaded successfully."})



# Define the user_page
@app.route('/user/<username>', methods=['GET', 'POST'])
def user_visit(username):
    if 'authenticated' not in session:
        session['error'] = "Log in first please!"
        return redirect(url_for('user_login'))
    count = []
    thumbnail_addresses = []
    imgURL = {}
    photo_num = query_user_by_name(username).photo_id
    print(photo_num)
    for i in range(photo_num):
        photo_thumbnail_address = 'static/thumbnail/' + str(username) + str(i+1) + ".jpg"
        thumbnail_addresses.append(photo_thumbnail_address)
        count.append(i+1)
    imgURL = dict(zip(count, thumbnail_addresses))
    return render_template("user_page.html", username=username, thumbnail_addresses=thumbnail_addresses,
                           count=count, imgURL=imgURL)


# Define the detail_page
@app.route('/user/<username>/<photo_id>', methods=['GET', 'POST'])
def detail_function(username, photo_id):
    if 'authenticated' not in session:
        session['error'] = "Log in first please!"
        return redirect(url_for('user_login'))
    org_address = '../static/org_photo/'+ str(username) + str(photo_id) + ".jpg"
    det_address = '../static/det_photo/'+ str(username) + str(photo_id) + ".jpg"
    return render_template("detail_page.html", username=username, org_address=org_address,
                           det_address=det_address)





if __name__ == "__main__":
    app.run()
