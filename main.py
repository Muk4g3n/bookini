from os import error
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

def demarage_froid(category , books_data ):
  books_data_df=books_data[books_data["Category"].isin(category)]
  average_all=books_data_df["average_rating"].mean()
  nb_vote_min=books_data_df["SommeRating"].quantile(0.99)
  def weighted_rating(data,min=nb_vote_min,aver=average_all):
    ar=data["average_rating"]
    vc=data["SommeRating"]
    return (vc/(vc+min)*ar) + (min/(min+vc)*aver)
  books_data_df["weighted_score"]=books_data_df.apply(weighted_rating,axis=1)
  books_data_df=books_data_df.sort_values("weighted_score",ascending=False)
  #on retour par exemple 10 livre
  return books_data_df[0:5]


@app.route('/')
def dashboard():
    if 'u_id' in session:
        
        books = mongo.db.books.find()
        category = mongo.db.users.find_one({'User-ID':session['u_id']})['Liked_categories']
        category = ['[\''+x+'\']' for x in category]
        books_data = pd.DataFrame.from_dict(books)
        books = mongo.db.books.find()
        recommendation = demarage_froid(category,books_data)
        
        # last_rated_book = mongo.db.users.find_one({"User-ID" : session['u_id']})['last_rated']

        return render_template('final.html',books = books,recommendation = recommendation)
    return redirect('/login')

@app.route('/search',methods = ['GET','POST'])
def search():
    if request.method =='POST':
        query = request.form['query']
        mongo.db.books.ensure_index([('book_title',"text"),('book_author',"text"),('publisher',"text"),('Summary',"text"),('Category',"text")])
        
        recommendation = mongo.db.books.find( { "$text": { "$search": query } } )
        return render_template('search.html',recommendation = recommendation,query=query)
        



@app.route('/<int:id>',methods = ['GET','POST'])
def book(id):
    if 'u_id' in session:

            result = mongo.db.books.find_one_or_404({"ISBN":id})
            rating = mongo.db.ratings.find_one({"ISBN":id,"User-ID":session['u_id']})
            print(rating)
            return render_template('book.html',res = result,rating=rating)
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
                return render_template('login.html',error="Password incorrect")
                
        else:
            return render_template('login.html',error="User does not exist")

    else:
        session.pop('u_id',None)
        return render_template('login.html',error=None)

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
            return render_template('signup.html',error ='user already exists')
    else:
        session.pop('u_id',None)
        return render_template('signup.html',error = None)

@app.route('/categories',methods =['GET','POST'])
def cats():
    if request.method == 'POST':
        cat =  request.form.getlist('cat')
        mongo.db.users.find_one_and_update({"User-ID" : session['u_id']},{"$set": {"Liked_categories": cat,'nb_ratings':0}})
        return redirect('/')
    else:
        categories = mongo.db.categories.find({}).sort([('nb',-1)])
        return render_template('categories.html',categories = categories)


@app.route('/similair',methods =['POST','GET'])
def sim():
    if request.method == 'POST':
        res = mongo.db.books.find()
        

        newrating = {
                'User-ID' : session['u_id'],
                'ISBN' : int(request.form['book_id']),
                'Book-Rating' : int(request.form['rating'])
            }
            
        mongo.db.ratings.insert_one(newrating)
        current_book = mongo.db.books.find_one({'ISBN':newrating['ISBN']})
        average = ((current_book['SommeRating'] * current_book['average_rating']) + newrating['Book-Rating']) / (current_book['SommeRating'] + 1)
        current_book['average_rating'] = average              
        current_book['SommeRating'] = current_book['SommeRating'] + 1
        mongo.db.books.update_one({'ISBN' : newrating['ISBN']}, {"$set" : current_book})
        mongo.db.users.update_one({'User-ID':session['u_id']},{"$set":{'last_rated' : request.form['book_id']}})

        list_res = list(res)[:5]
        return dumps(list_res)




@app.route('/logout')
def logout():
   
    session.pop('u_id',None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)