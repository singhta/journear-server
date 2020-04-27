#!/usr/bin/env python
import os
import subprocess

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell
from redis import Redis
from flask_sqlalchemy import SQLAlchemy
from app import create_app
from app.models import Role, User
from config import Config
from flask import Flask, request, jsonify, render_template
#from flask_cors import CORS
#from flasgger import Swagger, swag_from
#import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from flask import request
import config
import hashlib

import os
import config as cf
from flasgger import Swagger, swag_from
from flask_cors import CORS


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = config.database_uri
manager = Manager(app)
migrate = Migrate(app)
db = SQLAlchemy(app)
CORS(app)
Swagger(app)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


class user_cl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200),unique = True,nullable =False )
    email = db.Column(db.String(120),nullable = False)
    password = db.Column(db.String(200))
    #ratings = db.Column(db.Integer)
    dob = db.Column(db.String(80))
    gender  = db.Column(db.String(80))
    name = db.Column(db.String(80),nullable = False)

class journey(db.Model):
    journey_id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(200),nullable = False)
    destination = db.Column(db.String(200),nullable = False)
    time = db.Column(db.String(80),nullable = False)
    #ratings = db.Column(db.Integer)
    user = db.Column(db.String(100), nullable = False)
    user_rating  = db.Column(db.String(10))
    preference_gender = db.Column(db.String(80))


@swag_from(os.path.join(cf.BASE_PATH, "api_doc", "register.yml"))
@app.route("/api/v1/user/register", methods=['POST', 'OPTIONS'])
def register():
    try:
        db.create_all()
        request_data =request.json
        email = request_data['email']
        password = request_data['password']
        key = hashlib.sha256(password.encode('UTF-8')).hexdigest()
        name = request_data['name']
        username = email
        gender = request_data['gender']
        dob = request_data['dob']
        register = user_cl(username=username, name = name,password=key,gender=gender,dob=dob,email=email)
        db.session.add(register)
        db.session.commit()
        user = user_cl.query.filter_by(username=email).first()
        return jsonify({'Status': 200, "Message": "Success","id":user.id})
    except Exception as e:
        db.session.rollback()
        return jsonify( {'Status': 200, "Message": "Failed to register","exception":str(e)})


@swag_from(os.path.join(cf.BASE_PATH, "api_doc", "add_journey.yml"))
@app.route("/api/v1/user/add_journey", methods=['POST', 'OPTIONS'])
def add_journey():
    try:
        db.create_all()
        request_data = request.json
        source = request_data['source']
        destination = request_data['destination']
        time = request_data['time']
        user = request_data['user']
        user_rating = request_data['user_rating']
        preference_gender = request_data['preferences']['gender']

        add_journey = journey(source=source, destination = destination,time=time,user=user,user_rating=user_rating,preference_gender=preference_gender)
        db.session.add(add_journey)
        db.session.commit()
        return jsonify({'Status': 200, "Message": "Journey added"})
    except Exception as e:
        return jsonify( {'Status': 200, "Message": "Failed to add journey","exception":str(e)})


@swag_from(os.path.join(cf.BASE_PATH, "api_doc", "get_journey.yml"))
@app.route("/api/v1/user/get_journey", methods=['POST', 'OPTIONS'])
def get_journey():
    try:
        db.create_all()
        request_data =request.json
        user = request_data['user']
        get_journey = journey.query.filter_by(user=user).all()
        if get_journey is not None:
            results = []
            for obj in get_journey:
                result = {"source": obj.source,
                "destination": obj.destination,
                 "time": obj.time,
                 "user": obj.user,
                 "user_rating": obj.user_rating,
                 "preferences": {"gender": obj.preference_gender}}
                results.append(result)

            return jsonify({'Status': 200, 'Message': 'Success', 'result': results})
        else:
            return jsonify({'Status': 401, 'Message': 'Success', 'result': {}})
    except Exception as e:
        return jsonify( {'Status': 500, "Message": "Failed to fetch journey","exception":str(e)})


@swag_from(os.path.join(cf.BASE_PATH, "api_doc", "login.yml"))
@app.route("/api/v1/user/login", methods=['POST', 'OPTIONS'])
def login(email='',password='',test=False):
    db.create_all()
    if test == False:
        request_data = request.json
        email = request_data['email']
        password = request_data['password']
    users = user_cl.query.all()

    login = user_cl.query.filter_by(username=email).first()


    if login is not None:
        key = login.password
        new_key = hashlib.sha256(password.encode('UTF-8')).hexdigest()
        if key == new_key:
            return jsonify({'Status': 200, "Message": "Success","user":{"id":login.id,"username":login.username,"dob":login.dob,"gender":login.gender,"name": login.name},
                            'key': "Rh8ZtIeFWnTSzDN9OSxRbuInmiUlSQlm"})
        else:
            return jsonify({'Status': 401, "Message": "Login Failed"})
    else:
        return jsonify({'Status': 401, "Message": "Login Failed"})

# def test_adduser():
#
#     lucas=user_cl(username="lucas", email="lucas@example.com", password="test")
#     user2 = user_cl(username="lucas", email="lucas@test.com")
#
#     db.session.add(lucas)
#     db.session.commit()
#
#     assert lucas in db.session
#     assert user2 not in db.session


# def test_login():
#     lucas=user_cl(username="lucas", email="lucas@example.com", password="test")
#     db.session.add(lucas)
#     db.session.commit()
#     rv = login('lucas@example.com', 'test',True)
#     assert 'Login Successful' == rv

@app.route("/api/v1/clear_user_table", methods=['POST', 'OPTIONS'])
def clear_table():
    try:
        db.create_all()
        db.session.query(user_cl).delete()
        db.session.commit()
        return "cleared table"
    except:
        db.session.rollback()
        return "failed to clear table"

def add_fake_data(number_users):
    """
    Adds fake data to the database.
    """
    User.generate_fake(count=number_users)




if __name__ == '__main__':
    db.create_all()
    manager.run()
    #test_adduser()
    #test_login()

