"""
This defines the Flask scripting for the Sakura front-end
"""

import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify

from backend import read_from_s3, write_to_s3, perenual_query_api as query_api

app = Flask(__name__)
app.config['DEBUG'] = True

TODAY = datetime.today()
TOMORROW = TODAY + timedelta(days=1)
perenual_msg = "Upgrade Plans To Premium/Supreme - https://perenual.com/subscription-api-pricing. I'm sorry"

def read_plants_data():
    return read_from_s3()

def write_plants_data(plants_data):
    write_to_s3(plants_data)

def get_next_plant_id(plants_data):
    return max([plant.get('id', 0) for plant in plants_data] + [0]) + 1

# Assuming your schedules are integers representing days for water and months for food/repotting
def calculate_next_water_date(date_added, water_schedule):
    date_added = datetime.strptime(date_added, "%Y-%m-%d")
    days_since_added = (TODAY - date_added).days
    days_until_next_water = water_schedule - (days_since_added % water_schedule)
    return (TODAY + timedelta(days=days_until_next_water)).strftime("%Y-%m-%d")

def is_event_today_or_tomorrow(date_added, schedule, unit):
    if schedule == 0:
        return False
    date_added = datetime.strptime(date_added, "%Y-%m-%d")
    if unit == 'days':
        period = timedelta(days=schedule)
    elif unit == 'months':
        period = timedelta(days=schedule*30) # Approximation
    next_event_date = date_added
    while next_event_date < TODAY:
        next_event_date += period
    return next_event_date <= (TODAY + timedelta(days=1))

def get_watering(query: str):
    plants = query_api(query)

    if len(plants) == 1:
        return plants[0]['watering']
    if len(plants) == 0:
        print(f"Got no result back from perenual API with query: '{query}'")
        return "NOPE"
    if len(plants) > 10:
        print(f"Got {len(plants)} results back from perenual API, please narrow your query.")
        return "NOPE"
    if len(plants) > 1: # Just use the first one that is valid for now:
        for plant in plants:
            if plant['watering'] != perenual_msg:
                return plant['watering']
        return perenual_msg

@app.route('/add-plant', methods=['POST'])
def add_plant():
    plant_name = request.form['plant_name']
    position = int(request.form['position'])
    date_added = datetime.now().strftime("%Y-%m-%d")
    water_schedule = get_watering(plant_name)
    if water_schedule == "NOPE":
        return
    if water_schedule == perenual_msg:
        print("Perenual charges for subscription to view this plant's data, look it up and replace it!")
        water_schedule = "Average"
    food_schedule = 2
    if position in [1,2]: # Inside plants:
        repotting_schedule = 6
        if water_schedule == "Average":
            water_schedule = 5
        elif water_schedule == "Frequent":
            water_schedule = 3
        elif water_schedule == "Minimum":
            water_schedule = 10
        elif water_schedule == "None":
            water_schedule = 9999
    else:
        repotting_schedule = 0
        if water_schedule == "Average":
            water_schedule = 3
        elif water_schedule == "Frequent":
            water_schedule = 1
        elif water_schedule == "Minimum":
            water_schedule = 7
        elif water_schedule == "None":
            water_schedule = 9999
    # Check water_schedule to confirm it is now an int:
    if type(water_schedule) != int:
        raise ValueError(f"Water schedule is not an int??: {water_schedule}")
    temperature_min = request.form.get('temperature_min', None)
    temperature_max = request.form.get('temperature_max', None)
    
    plants_data = read_plants_data()
    
    plant_id = get_next_plant_id(plants_data)
    plant_data = {
        "id": plant_id,
        "position": position,
        "name": plant_name,
        "date_added": date_added,
        "water_schedule": water_schedule,
        "food_schedule": food_schedule,
        "repotting_schedule": repotting_schedule,
        "temperature_min": temperature_min,
        "temperature_max": temperature_max
    }
    
    plants_data.append(plant_data)
    write_plants_data(plants_data)
    
    return redirect(url_for('home'))

@app.route('/')
def home():
    # Retrieve updated table data from the database
    # Pass this data to the template
    plants_data = read_plants_data()
    for plant in plants_data:
        next_water = calculate_next_water_date(plant['date_added'], int(plant['water_schedule']))
        if next_water == TODAY.strftime("%Y-%m-%d"):
            plant['next_water'] = "Today!"
        elif next_water == TOMORROW.strftime("%Y-%m-%d"):
            plant['next_water'] = "Tomorrow"
        else:
           plant['next_water'] = next_water
        plant['food_event'] = is_event_today_or_tomorrow(plant['date_added'], int(plant['food_schedule']), 'months')
        plant['repotting_event'] = is_event_today_or_tomorrow(plant['date_added'], int(plant['repotting_schedule']), 'months')
    # Organize data by position for display
    organized_data = {position: [] for position in range(4)}
    for plant in plants_data:
        organized_data[plant['position']].append(plant)
    return render_template('index.html', organized_data=organized_data)

if __name__ == '__main__':
    app.run(debug=True)
