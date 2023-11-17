
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from transformers import pipeline

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SECRET_KEY'] = 'oursynsecretsynkey'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

NUTRITIONIX_APP_ID = '' #enter your api is here, get it by loging in into Nutritionix, its free
NUTRITIONIX_APP_KEY = ''
NUTRITIONIX_USER_ID = '0'

API_ID=''   #enter your api is here, get it by loging in into Edamam, its free
API_KEY=''

def fetch_recipe(ingredients):
    base_url = 'https://api.edamam.com/search'
    params = {
        'q': ','.join(ingredients),
        'app_id': API_ID,
        'app_key': API_KEY,
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'hits' in data:
            recipes = data['hits']
            if recipes:
                return recipes
            else:
                return "I couldn't find any recipes with those ingredients."
        else:
            return "Sorry, I encountered an issue with the recipe database."
    else:
        return "Sorry, I couldn't connect to the recipe database. Please try again later."

def display_recipe(recipes, index):
    selected_recipe = recipes[index - 1]['recipe']
    recipe_info = f"Recipe: {selected_recipe['label']}\n"
    recipe_info += f"URL: {selected_recipe['url']}\n"
    recipe_info += "Ingredients:\n"
    for ingredient in selected_recipe['ingredientLines']:
        recipe_info += f"- {ingredient}\n"
    return recipe_info

def get_exercise_info_natural_language(natural_language_text, gender, weight_kg, height_cm, age):
    url = 'https://trackapi.nutritionix.com/v2/natural/exercise'

    headers = {
        'x-app-id': NUTRITIONIX_APP_ID,
        'x-app-key': NUTRITIONIX_APP_KEY,
        'Content-Type': 'application/json',
    }

    data = {
        'query': natural_language_text,
        'gender': gender,
        'weight_kg': weight_kg,
        'height_cm': height_cm,
        'age': age,
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        data = response.json()
        exercise_info = data.get('exercises', [{}])[0]
        return {
            'nf_calories': exercise_info.get('nf_calories', 'N/A'),
        }
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
    }

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
            'nf_saturated_fat': nutrition_info.get('nf_saturated_fat', 'N/A'),
            'nf_cholesterol': nutrition_info.get('nf_cholesterol', 'N/A'),
            'nf_sodium': nutrition_info.get('nf_sodium', 'N/A'),
            'nf_dietary_fiber': nutrition_info.get('nf_dietary_fiber', 'N/A'),
            'nf_sugars': nutrition_info.get('nf_sugars', 'N/A'),
            'nf_potassium': nutrition_info.get('nf_potassium', 'N/A'),
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
        'nf_saturated_fat': 'N/A',
        'nf_cholesterol': 'N/A',
        'nf_sodium': 'N/A',
        'nf_dietary_fiber':'N/A',
        'nf_sugars': 'N/A',
        'nf_potassium': 'N/A',
    }

def get_nutrition_info_natural_language(natural_language_text):
    url = 'https://trackapi.nutritionix.com/v2/natural/nutrients'
    
    headers = {
        'x-app-id': NUTRITIONIX_APP_ID,
        'x-app-key': NUTRITIONIX_APP_KEY,
        'x-remote-user-id': NUTRITIONIX_USER_ID,
        'Content-Type': 'application/json',
    }

    data = {
        'query': natural_language_text,
        'timezone': "US/Eastern"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        data = response.json()
        nutrition_info = data.get('foods', [{}])[0]
        return {
            'nf_calories': nutrition_info.get('nf_calories', 'N/A'),
            'nf_protein': nutrition_info.get('nf_protein', 'N/A'),
            'nf_total_carbohydrate': nutrition_info.get('nf_total_carbohydrate', 'N/A'),
            'nf_total_fat': nutrition_info.get('nf_total_fat', 'N/A'),
            'nf_saturated_fat': nutrition_info.get('nf_saturated_fat', 'N/A'),
            'nf_cholesterol': nutrition_info.get('nf_cholesterol', 'N/A'),
            'nf_sodium': nutrition_info.get('nf_sodium', 'N/A'),
            'nf_dietary_fiber': nutrition_info.get('nf_dietary_fiber', 'N/A'),
            'nf_sugars': nutrition_info.get('nf_sugars', 'N/A'),
            'nf_potassium': nutrition_info.get('nf_potassium', 'N/A'),
        }
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
        'nf_saturated_fat': 'N/A',
        'nf_cholesterol': 'N/A',
        'nf_sodium': 'N/A',
        'nf_dietary_fiber':'N/A',
        'nf_sugars': 'N/A',
        'nf_potassium': 'N/A',
    }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)    

emotion_classifier = pipeline("text-classification", model='bhadresh-savani/distilbert-base-uncased-emotion', return_all_scores=True)
@app.route('/emotion_classification', methods=['POST'])
def emotion_classification():
    user_input = request.form['messageText'].encode('utf-8').strip().decode('utf-8')  # Ensure user_input is a string
    try:
        prediction = emotion_classifier(user_input)
        print(prediction)

        if prediction:
            max_emotion = max(prediction[0], key=lambda x: x['score'])
            return jsonify(max_emotion)
        else:
            return jsonify({'error': 'No emotions predicted.'})

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)})
    
@app.route('/get_recipe', methods=['POST'])
def get_recipe():
    ingredients = request.form.get('ingredients')
    
    if not ingredients:
        return "Please provide ingredients in the form."

    recipes = fetch_recipe(ingredients.split(','))
    selected_recipe_index = None

    if 'recipe_choice' in request.form:
        selected_recipe_index = int(request.form['recipe_choice'])

    return render_template('bot.html', recipes=recipes, selected_recipe_index=selected_recipe_index, ingredients=ingredients)

@app.route('/recipe_details', methods=['POST'])
def recipe_details():
    selected_recipe_index = int(request.form['selected_recipe'])
    ingredients = request.form.get('ingredients')
    recipes = fetch_recipe(ingredients.split(','))
    selected_recipe_info = display_recipe(recipes, selected_recipe_index)
    return render_template('bot.html', recipes=recipes, selected_recipe_index=selected_recipe_index, selected_recipe_info=selected_recipe_info, ingredients=ingredients)

@app.route('/bot', methods=['POST'])
def bot_page():
    return render_template('bot.html')

@app.route('/')
def main_page():
    return render_template('home.html')

@app.route('/info')
def info_page():
    # Add logic to retrieve and display tips information
    return render_template('info.html')

@app.route('/tips')
def tips_page():
    # Add logic to retrieve and display tips information
    return render_template('tips.html')

@app.route('/alternative')
def alternative_page():
    # Add logic to retrieve and display tips information
    return render_template('alternatives.html')

@app.route('/view_profile')
def view_profile():
    # Add logic to retrieve and display the user's profile information
    user = session.get('user')
    return render_template('view_profile.html', user=user)

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

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user = session.get('user')

    # Get the new information from the form
    new_email = request.form.get('newEmail')
    new_username = request.form.get('newUsername')
    new_password = request.form.get('newPassword')

    # Update the user's information if the fields are not empty
    if new_email:
        user['email'] = new_email
    if new_username:
        user['username'] = new_username
    if new_password:
        user['password'] = generate_password_hash(new_password, method='pbkdf2:sha256')

    # Save the updated user information
    session['user'] = user

    # Redirect back to the profile page
    return redirect(url_for('view_profile'))

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

@app.route('/get_nutrition_info_natural_language', methods=['POST']) 
def get_nutrition_info_natural_language_route():
    natural_language_text = request.json.get('natural_language_text', '')
    print(f"Received JSON data: natural_language_text={natural_language_text}")

    # Call the Nutritionix API with natural language text
    nutrition_info = get_nutrition_info_natural_language(natural_language_text)

    return jsonify(nutrition_info)

@app.route('/get_exercise_info_natural_language', methods=['POST'])
def get_exercise_info_natural_language_route():
    natural_language_text = request.json.get('natural_language_text', '')
    gender = request.json.get('gender', '')
    weight_kg = request.json.get('weight_kg', '')
    height_cm = request.json.get('height_cm', '')
    age = request.json.get('age', '')

    print(f"Received JSON data: natural_language_text={natural_language_text}, gender={gender}, weight_kg={weight_kg}, height_cm={height_cm}, age={age}")

    # Call the Nutritionix API with natural language text
    exercise_info = get_exercise_info_natural_language(natural_language_text, gender, weight_kg, height_cm, age)

    return jsonify(exercise_info)

if __name__ == "__main__":
    with app.app_context():
        # Create the database tables before running the application
        db.create_all()
    app.run(debug=True)
