from flask import Flask,render_template,url_for,request,redirect, session , jsonify
from flask_pymongo import PyMongo
import pandas as pd 
import numpy as np
import pickle
from bson.json_util import dumps

app = Flask(__name__)
app.config['MONGO_URI'] ='mongodb://localhost:27017/dataset'
app.secret_key ='something secret'
mongo = PyMongo(app)

@app.route('/')
def dashboard():
    if 'u_id' in session:
        
        books = mongo.db.books.find()
    
        return render_template('dashbord.html',books = books)
    return redirect('/login')

@app.route('/<int:id>',methods = ['GET','POST'])
def book(id):
    if 'u_id' in session:
        # if request.method == 'POST':
        #     newrating = {
        #         'User-ID' : session['u_id'],
        #         'ISBN' : id,
        #         'Book-Rating' : int(request.form['rating'])
        #     }
            
        #     # mongo.db.ratings.insert_one(newrating)
        #     current_book = mongo.db.books.find_one({'ISBN':id}) 
        #     average = ((current_book['SommeRating'] * current_book['average_rating']) + newrating['Book-Rating']) / (current_book['SommeRating'] + 1)
        #     current_book['average_rating'] = average              
        #     current_book['SommeRating'] = current_book['SommeRating'] + 1
        #     mongo.db.books.update_one({'ISBN' : id}, {"$set" : current_book})
        #     return redirect('/')
        # else:
            result = mongo.db.books.find_one_or_404({"ISBN":id})
            return render_template('book.html',res = result)
    return redirect('/login')

@app.route('/login',methods= ['POST','GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        res = {
            'email':email,
            'password':password
        }
        user =  mongo.db.users.find_one({'email':email})
        if not user == None:
            if password == user['password']:
                u_id =  mongo.db.users.find_one({'email':email})['User-ID']
                print(u_id)
                session['u_id'] = u_id
                return redirect('/')
            else:
                return "password incorrect"
        else:
            return "user does not exist"

    else:
        session.pop('u_id',None)
        return render_template('login.html')

@app.route('/signup',methods = ['GET','POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        name = firstname + lastname
        age = request.form['Age']
        password = request.form['password']
        u_id = mongo.db.users.count() + 1
        content = {
            'email':email,
            'name' : name,
            'User-ID' : u_id,
            'age':age,
            'password':password
        }
        user = mongo.db.users.find_one({'email':email})
        if user == None:
            mongo.db.users.insert_one(content)
            session['u_id'] = u_id
            return redirect('/categories')
        else:
            return 'user already exists'
    else:
        session.pop('u_id',None)
        return render_template('signup.html')

@app.route('/categories',methods =['GET','POST'])
def cats():
    if request.method == 'POST':
        cat =  request.form.getlist('cat')
        return redirect('/')
    else:
        categories = mongo.db.categories.find({}).sort([('nb',-1)])
        return render_template('categories.html',categories = categories)


@app.route('/similair')
def sim():
    res = mongo.db.books.find()
    list_res = list(res)[:5]
    return dumps(list_res)


@app.route('/logout')
def logout():
   
    session.pop('u_id',None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)