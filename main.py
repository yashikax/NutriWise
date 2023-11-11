'''from flask import Flask, render_template,  send_from_directory, request

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def main_page():
    return render_template('home.html')

@app.route('/registration')
def registration_page():
    return render_template('registration.html')

# New route for handling registration form submission
@app.route('/register', methods=['POST'])
def register_submit():
    # Get the registration form data
    # Perform registration logic here
    return render_template('home.html')  # Redirect to the main page after registration

@app.route('/login', methods=['POST'])
def login_submit():
    # Get the username and password from the form submission
    username = request.form.get('username')
    password = request.form.get('password')

    # Perform authentication or any other necessary logic here
    # For simplicity, let's just print the username and password
    print(f"Username: {username}, Password: {password}")

    # Redirect to the main page after login (you can change this)
    return render_template('home.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

if __name__ == "__main__":
    app.run(debug=True)'''

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
            # Login successful, you can redirect to another page or perform other actions
            return redirect(url_for('main_page'))
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

if __name__ == "__main__":
    with app.app_context():
        # Create the database tables before running the application
        db.create_all()
    app.run(debug=True)