
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
NUTRITIONIX_USER_ID = '0'

def get_nutrition_data(query):
    url = 'https://trackapi.nutritionix.com/v2/search/instant'
    headers = {
        'x-app-id': NUTRITIONIX_APP_ID,
        'x-app-key': NUTRITIONIX_APP_KEY,
        'x-remote-user-id': NUTRITIONIX_USER_ID,
    }
    params = {
        'query': query,
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        #response = requests.get("https://trackapi.nutritionix.com/v2/search/instant?query=apple")
        response.raise_for_status()
        data = response.json()
        result = []

        if 'branded' in data:
            branded_foods = data['branded']
            result.extend([(food['food_name'], food.get('nf_calories', 'N/A'),'Branded') for food in branded_foods])

        if 'common' in data:
            common_foods = data['common']
            result.extend([(food['food_name'], food.get('nf_calories', 'N/A'),'Common') for food in common_foods])
        
        return result
    except requests.exceptions.HTTPError as errh:
        print ("HTTP Error:",errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:",errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:",errt)
    except requests.exceptions.RequestException as err:
        print("RequestException:", type(err).__name__, "-", err)
    return None

def get_nutrition_info(food_name, category):
    url = 'https://trackapi.nutritionix.com/v2/natural/nutrients' if category == 'Common' else 'https://trackapi.nutritionix.com/v2/search/item'
    
    headers = {
        'x-app-id': NUTRITIONIX_APP_ID,
        'x-app-key': NUTRITIONIX_APP_KEY,
        'x-remote-user-id': NUTRITIONIX_USER_ID,
    }

    params = {
        'query': food_name,
    }

    try:
        response = requests.post(url, headers=headers, json=params)
        response.raise_for_status()
        data = response.json()
        nutrition_info = data.get('foods', [{}])[0]
        return {
            'nf_calories': nutrition_info.get('nf_calories', 'N/A'),
            'nf_protein': nutrition_info.get('nf_protein', 'N/A'),
            'nf_total_carbohydrate': nutrition_info.get('nf_total_carbohydrate', 'N/A'),
            'nf_total_fat': nutrition_info.get('nf_total_fat', 'N/A'),
        }
        #return data.get('foods', [{}])[0]  # Return the first food item or an empty dictionary
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("RequestException:", type(err).__name__, "-", err)

    return {
        'nf_calories': 'N/A',
        'nf_protein': 'N/A',
        'nf_total_carbohydrate': 'N/A',
        'nf_total_fat': 'N/A',
    }


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

@app.route('/home2',methods=['GET', 'POST'])
def home2_page():
    # Check if the user is logged in
    user = session.get('user')
    if not user:
        # Redirect to login page if the user is not logged in
        return redirect(url_for('login_page'))

    # Render home2.html with the user's name
    selected_item = None
    if request.method == 'POST':
        search_query = request.form.get('search_query', '').lower()
        result = get_nutrition_data(search_query)
        #selected_item = None
        # Check if the search query exists in the grocery data
        '''if result:
            return render_template('home2.html', username=user['name'], result=result)
        else:
            result = None
            print(search_query)
            return render_template('home2.html', username=user['name'], result=result, error=search_query)
    return render_template('home2.html', username=user['name'], result=None, error=None)'''
        if result:
            selected_item = {
                'name': result[0][0],
                'category': result[0][2],
                'nf_calories': 'N/A',
                'nf_protein': 'N/A',
                'nf_total_carbohydrate': 'N/A',
                'nf_total_fat': 'N/A',
            }

            return render_template('home2.html', username=user['name'], result=result, selected_item=selected_item)
        else:
            result = None
            return render_template('home2.html', username=user['name'], result=result, error='Item not found.', selected_item=selected_item)

    return render_template('home2.html', username=user['name'], result=None, error=None, selected_item=selected_item)

@app.route('/get_nutrition_info', methods=['POST'])
def get_nutrition_info_route():
    food_name = request.json.get('food_name', '')
    category = request.json.get('category', '')
    print(f"Received JSON data: food_name={food_name}, category={category}")
    nutrition_info = get_nutrition_info(food_name, category)

    return jsonify(nutrition_info)


if __name__ == "__main__":
    with app.app_context():
        # Create the database tables before running the application
        db.create_all()
    app.run(debug=True)