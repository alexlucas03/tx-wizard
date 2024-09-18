from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import datetime
from collections import defaultdict
from dish import Dish
import requests
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'

# Initial Data Setup
dishes = []
start_date_str = "2024-09-17"
end_date_str = "2024-12-13"
start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")

types = ['lunch', 'dinner', 'x1']
type_index = 0

delta = datetime.timedelta(days=1)
current_date = start_date
today = datetime.date.today().strftime('%Y-%m-%d')
duration = (end_date - start_date).days
ownersArray = [None] * duration * 3
i = 0
while current_date <= end_date:
    day_of_week = current_date.strftime("%A")
    
    if day_of_week != "Saturday":
        if day_of_week == "Sunday" and type_index == 0:
            type_index = 1

        owner = ownersArray[i]  # Get the owner from the ownersArray
        
        dish = Dish(date=current_date.strftime("%Y-%m-%d"), owner=owner, type=types[type_index])
        dishes.append(dish)
        i += 1
        
        if types[type_index] == 'x1':
            current_date += delta
        
        type_index = (type_index + 1) % len(types)
 
    else:
        current_date += delta

# Group dishes by month
grouped_dishes = defaultdict(lambda: defaultdict(list))
for dish in dishes:
    month = datetime.datetime.strptime(dish.date, "%Y-%m-%d").strftime("%B")
    day = datetime.datetime.strptime(dish.date, "%Y-%m-%d").strftime("%d")
    grouped_dishes[month][day].append(dish)

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    # Existing code using the logged-in `user`
    today_lunch = None
    today_dinner = None
    today_x1 = None
    today = datetime.date.today().strftime('%Y-%m-%d')

    for dish in dishes:
        if dish.date == today:
            if dish.type == "lunch":
                today_lunch = dish
            elif dish.type == "dinner":
                today_dinner = dish
            elif dish.type == "x1":
                today_x1 = dish

    # Mention formatting with fallback for None
    lunch_owner = today_lunch.owner if today_lunch and today_lunch.owner else 'Not Assigned'
    dinner_owner = today_dinner.owner if today_dinner and today_dinner.owner else 'Not Assigned'
    x1_owner = today_x1.owner if today_x1 and today_x1.owner else 'Not Assigned'

        # Construct message
    lunch_message = f"Lunch: @{lunch_owner}"
    dinner_message = f"Dinner: @{dinner_owner}"
    x1_message = f"x1: @{x1_owner}"

    url = "https://api.groupme.com/v3/bots/post"

    # Calculate loci (starting position and length of each mention)
    lunch_loci = []
    dinner_loci = []
    x1_loci = []
    if lunch_owner != 'Not Assigned':
        lunch_mention_start = 7
        lunch_loci.append([lunch_mention_start, lunch_mention_start + len(lunch_owner)])

    if dinner_owner != 'Not Assigned':
        dinner_mention_start = 8
        dinner_loci.append([dinner_mention_start, dinner_mention_start + len(dinner_owner)])

    if x1_owner != 'Not Assigned':
        x1_mention_start = 4
        x1_loci.append([x1_mention_start, x1_mention_start + len(x1_owner)])

    # Data to send in the POST request
    data = {
        "text": lunch_message,
        "bot_id": "c9ed078f3de7c89547308a050a",
        "attachments": [
            {
                "type": "mentions",
                "user_ids": [lunch_owner] if lunch_owner != 'Not Assigned' else [],
                "loci": lunch_loci
            }
        ]
    }
    # Send the POST request
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(data))

    data = {
        "text": dinner_message,
        "bot_id": "c9ed078f3de7c89547308a050a",
        "attachments": [
            {
                "type": "mentions",
                "user_ids": [dinner_owner] if dinner_owner != 'Not Assigned' else [],
                "loci": dinner_loci
            }
        ]
    }
    # Send the POST request
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(data))

    data = {
        "text": x1_message,
        "bot_id": "c9ed078f3de7c89547308a050a",
        "attachments": [
            {
                "type": "mentions",
                "user_ids": [x1_owner] if x1_owner != 'Not Assigned' else [],
                "loci": x1_loci
            }
        ]
    }
    # Send the POST request
    response = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(data))

    return render_template('index.html', grouped_dishes=grouped_dishes, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['user'] = username  # Store the username in session
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/change-owner', methods=['POST'])
def change_owner():
    data = request.get_json()  # Get the JSON data from the request
    dish_date = data.get('date')
    dish_type = data.get('type')
    new_owner = data.get('owner')

    # Find the dish that matches the date and type
    for index, dish in enumerate(dishes):
        if dish.date == dish_date and dish.type == dish_type:
            dish.owner = new_owner  # Update the owner
            
            # Update the ownersArray
            ownersArray[index] = new_owner
            return jsonify({'success': True})  # Correct use of jsonify

    return jsonify({'success': False, 'message': 'Dish not found'}), 404

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)  # Remove the user from the session
    return redirect(url_for('login'))  # Redirect to the login page

