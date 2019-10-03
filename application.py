# Import flask
from flask import Flask, render_template, request
from flask import redirect, url_for, flash, jsonify

# Import sqlalchamy to connect to data base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

# import forgery state token
from flask import session as login_session
import random
import string


# importt oauth2 for authontication and authorization
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests


app = Flask(__name__)


# declare my client_id

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item-Catalog"

# Connect to the database
engine = create_engine('sqlite:///catalog.db', connect_args={
    'check_same_thread': False})

Base.metadata.bind = engine

# create session to access the database
DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create STATE token to prevent request forgery.
# Store it in the session for later validation
@app.route('/login')
def login():
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits)for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# code for Googlt sign in
# connect to google and verify token id
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    google_id = credentials.id_token['sub']
    if result['user_id'] != google_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_google_id = login_session.get('google_id')
    if stored_access_token is not None and google_id == stored_google_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['google_id'] = google_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # See if a user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style ="width: 300px; height: 300px;border-radius:150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


# Create loacl authorization

# Create a new user
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


# Retrive the user object useing user_id
def getUSerInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result

    if result['status'] == '200':
        # Reset the user's session
        del login_session['access_token']
        del login_session['google_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Log out successful!'), 200)
        response.headers['Content-Type'] = 'application/json'
        return redirect(url_for('allCategories'))
        flash("Sign out successful!")
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Create JSON APIs to view App info in serializable format

# view all categories
@app.route('/category/JSON')
def categoryJSON():
    category = session.query(Category).all()
    return jsonify(categories=[i.serialize for i in category])


# view all items in a category
@app.route('/category/<int:category_id>/item/JSON')
def allItemsJSON(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(category_id=category_id).all()
    return jsonify(Item=[i.serialize for i in items])


# view a particular item
@app.route('/category/<int:category_id>/item/<int:item_id>/JSON')
def item(category_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item=item.serialize)


# show all categories
@app.route('/')
@app.route('/category/')
def allCategories():
    categories = session.query(Category).all()
    if 'username' not in login_session:
        return render_template('publiccatalog.html', categories=categories)
    else:
        return render_template('category.html', categories=categories)


# Add new Category
@app.route('/category/new/', methods=['GET', 'POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        new_category = Category(name=request.form['name'])
        session.add(new_category)
        session.commit()
        flash("New Category Created Successfully!")
        return redirect(url_for('allCategories'))
    else:
        return render_template('newcategory.html')


# Edit category
@app.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
def editCategory(category_id):

    edit_category = session.query(Category).filter_by(id=category_id).one()

    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        if request.form['name']:
            edit_category.name = request.form['name']
        session.add(edit_category)
        session.commit()
        flash("Category Edited Successfully! %s" % edit_category.name)
        return redirect(url_for('allCategories'))
    else:
        return render_template(
            'editcategory.html', category_id=category_id,
            category=edit_category)


# delete Category
@app.route('/restaurant/<int:category_id>/delete', methods=['GET', 'POST'])
def deleteCategory(category_id):
    delete_category = session.query(Category).filter_by(id=category_id).one()

    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        session.delete(delete_category)
        session.commit()
        flash("Category Deleted!")
        return redirect(url_for('allCategories', category_id=category_id))
    else:
        return render_template(
            'deletecategory.html', category=delete_category,
            category_id=category_id)


# Show items in each category
@app.route('/')
@app.route('/category/<int:category_id>/')
def showItems(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    items = session.query(Item).filter_by(
        category_id=category_id).all()

    if 'username' not in login_session:
        return render_template(
            'publicitem.html', category=category, items=items)
    else:
        return render_template('items.html', category=category, items=items)


# Add new item to the category
@app.route('/category/<int:category_id>/new/', methods=['GET', 'POST'])
def newItem(category_id):

    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=category_id)
        session.add(newItem)
        session.commit()
        flash("Added a new item Successfully!")
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template('newitem.html', category_id=category_id)


# Edit existing item
@app.route(
    '/category/<int:category_id>/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(category_id, item_id):

    if 'username' not in login_session:
        return redirect('/login')

    editItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['description']:
            editItem.description = request.form['description']
        session.add(editItem)
        session.commit()
        flash("Item Edited Successfully!")
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template(
            'edititem.html', category_id=category_id, item_id=item_id,
            item=editItem)


# Delete item
@app.route('/category/<int:category_id>/<int:item_id>/delete/', methods=[
    'GET', 'POST'])
def deleteItem(category_id, item_id):

    if 'username' not in login_session:
        return redirect('/login')

    deleteItem = session.query(Item).filter_by(id=item_id).one()

    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash("Item Deleted!")
        return redirect(url_for('showItems', category_id=category_id))
    else:
        return render_template(
            'deleteitem.html', category_id=category_id,
            item_id=item_id, item=deleteItem)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
