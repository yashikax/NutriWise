
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'oursynsecretsynkey'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

NUTRITIONIX_APP_ID = 'ecd1d15d'
NUTRITIONIX_APP_KEY = '2742b9b2de10e8f1280716792f7d0ccd'

def get_nutrition_data(query):
    url = 'https://api.nutritionix.com/v1_1/search/'
    params = {
        'appId': NUTRITIONIX_APP_ID,
        'appKey': NUTRITIONIX_APP_KEY,
        'query': query,
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Extract relevant information from the API response
    if 'hits' in data:
        hits = data['hits']
        if hits:
            first_hit = hits[0]['fields']
            return {
                'name': first_hit['item_name'],
                'calories': first_hit['nf_calories'],
            }

    return None

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)    

@app.route('/')
def main_page():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user'] = {'name': user.name, 'username': user.username, 'email' : user.email, 'password' : user.password}
            # Login successful, you can redirect to another page or perform other actions
            return redirect(url_for('home2_page'))
        else:
            # Invalid login, you can display an error message
            return render_template('login.html', error="Invalid username or password")
            

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def registration_page():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(name=name, email=email, username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        # Registration successful, you can redirect to the login page or perform other actions
        return redirect(url_for('login_page'))

    return render_template('registration.html')

@app.route('/bmi', methods=['GET', 'POST'])
def bmi_page():
    if request.method == 'POST':
        # Get the form data
        weight = float(request.form['weight'])
        height = float(request.form['height'])

        # Calculate BMI
        bmi = calculate_bmi(weight, height)

        # Render the BMI template with the calculated BMI
        return render_template('bmi.html', bmi=bmi)

    # If it's a GET request, just render the BMI template
    return render_template('bmi.html')

def calculate_bmi(weight, height):
    # Calculate BMI (example formula, you may need to adjust based on your requirements)
    bmi = weight / (height ** 2)
    return round(bmi, 2)

@app.route('/home2')
def home2_page():
    # Check if the user is logged in
    user = session.get('user')
    if not user:
        # Redirect to login page if the user is not logged in
        return redirect(url_for('login_page'))

    # Render home2.html with the user's name
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').lower()
        result = get_nutrition_data(search_query)
        # Check if the search query exists in the grocery data
        if result:
            return render_template('home2.html', username=user['name'], result=result)
        else:
            result = None
            return render_template('home2.html', username=user['name'], result=result, error='Item not found.')
    return render_template('home2.html', username=user['name'], result=None, error=None)
    

if __name__ == "__main__":
    with app.app_context():
        # Create the database tables before running the application
        db.create_all()
    app.run(debug=True)