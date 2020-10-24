import sqlite3
from flask import Flask, request, render_template, url_for, redirect, g, flash, get_flashed_messages, session

app = Flask(__name__)
app.config["DATABASE"] = 'database.db'
app.config["SECRET_KEY"] = '1779'  # The secret key to open the cookie.


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


class User_photo:
    def __init__(self, name=None, org_photo=None, thumbnail=None, det_photo=None):
        self.name = name
        self.org_photo = org_photo
        self.thumbnail = thumbnail
        self.det_photo = det_photo

    def toList(self):
        return [self.name, self.org_photo, self.thumbnail, self.det_photo]

    def fromList(self, user_info):
        self.name = user_info[0]
        self.org_photo = user_info[1]
        self.thumbnail = user_info[2]
        self.det_photo = user_info[3]

    def getAttrs(self):
        return ('name, org_photol, thumbnail, det_photo')


def insert_user_photo_to_db(user_photo):
    sql_insert = "INSERT INTO user_photo(name, org_photo, thumbnail, det_photo) VALUES (?, ?, ?, ?)"
    args = [user_photo.name, user_photo.org_photo, user_photo.thumbnail, user_photo.det_photo]
    g.db.execute(sql_insert, args)
    g.db.commit()


def query_user_photo_from_db():
    users = []
    sql_select = "SELECT * FROM user_photo"
    args = []
    cur = g.db.execute(sql_select, args)
    for item in cur.fetchall():
        user = User()
        user.fromList(item[1:])
        users.append(user)
    return users


def query_user_photo_by_nameandthumbnail(username, thumbnail):
    sql_select = "SELECT * FROM user_photo WHERE name = ? AND thumbnail = ? "
    args = [username, thumbnail]
    cur = g.db.execute(sql_select, args)
    items = cur.fetchall()
    if len(items) < 1:
        return None
    else:
        first_item = items[0]
        user_photo = User_photo()
        user_photo.fromList(first_item[1:])
    return user_photo

def query_user_photo_by_name(username):
    sql_select = "SELECT * FROM user_photo WHERE name = ? "
    args = [username]
    print('11111111')
    cur = g.db.execute(sql_select, args)
    items = cur.fetchall()
    if len(items) < 1:
        print('22222222')
        return None
    else:
        print('3333')
        image_list={}
        i=0
        for item in items:
            image_list[i]=item[3]
            i=i+1
    return image_list

@app.route('/pathtest/')
def insert():
    user_photo = User_photo()
    user_photo.name = "user1"
    user_photo.org_photo = url_for('static', filename='user1_org1.png')
    user_photo.thumbnail = url_for('static', filename='user1_thum1.png')
    user_photo.det_photo = url_for('static', filename='user1_det1.png')
    insert_user_photo_to_db(user_photo)
    user_photo = User_photo()
    user_photo.name = "user1"
    user_photo.org_photo = url_for('static', filename='user1_org2.png')
    user_photo.thumbnail = url_for('static', filename='user1_thum2.png')
    user_photo.det_photo = url_for('static', filename='user1_det2.png')
    insert_user_photo_to_db(user_photo)
    user_photo = User_photo()
    user_photo.name = "user2"
    user_photo.org_photo = url_for('static', filename='user2_org1.png')
    user_photo.thumbnail = url_for('static', filename='user2_thum1.png')
    user_photo.det_photo = url_for('static', filename='user2_det1.png')
    insert_user_photo_to_db(user_photo)
    return render_template('pathtest1.html')


@app.route('/pathtest2/')
def read():
    query_user_photo_by_name("user2", url_for('static', filename='user2_det1.png'))
    user_x = query_user_photo_by_name("user2", url_for('static', filename='user2_thum1.png'))
    print(user_x.org_photo)
    return render_template(('pathtest2.html'))


if __name__ == "__main__":
    app.run()
