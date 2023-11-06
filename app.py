"""
This defines the Flask scripting for the Sakura front-end
"""

import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.config['DEBUG'] = True

TODAY = datetime.today()

def read_plants_data():
    with open('plants.json', 'r') as file:
        data = json.load(file)
    return data['plants']

def write_plants_data(plants_data):
    with open('plants.json', 'w') as file:
        json.dump({'plants': plants_data}, file, indent=4)

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

# Define a multiplier based on the month to represent seasonal changes
def seasonal_water_multiplier(month):
    # Example: Increase watering frequency by 50% in summer months (June to August)
    if 6 <= month <= 8:
        return 1.5
    if 4 <= month <= 10:
        return 1.3
    return 1.0

def calculate_watering_frequency(min_precip, max_precip, local_precip):
    # Assume local_precip is the local average precipitation you have determined for your area
    # min_precip and max_precip are from the Trefle API data

    # Calculate the average precipitation requirement
    avg_precip_need = (min_precip + max_precip) / 2
    # Calculate the deficit
    precip_deficit = max(avg_precip_need - local_precip, 0)

    # Now convert this deficit into a watering frequency
    # The following is just an example and should be adjusted based on actual gardening knowledge:
    # If precip_deficit is 0, the plant does not need additional water (it may even need less)
    if precip_deficit == 0:
        return 'Check soil moisture before watering'
    
    # Example: If deficit is 25 mm, water once a week; adjust thresholds as needed
    if precip_deficit <= 25:
        base_frequency = 7  # days
    elif precip_deficit <= 50:
        base_frequency = 5
    else:
        base_frequency = 3
    
    # Adjust the frequency based on the season
    current_month = datetime.datetime.now().month
    frequency_multiplier = seasonal_water_multiplier(current_month)
    
    # Reduce the base frequency by the multiplier, ensuring it's at least every other day
    adjusted_frequency = max(base_frequency / frequency_multiplier, 2)
    
    return int(adjusted_frequency)

@app.route('/add-plant', methods=['POST'])
def add_plant():
    plant_name = request.form['plant_name']
    position = int(request.form['position'])
    date_added = datetime.now().strftime("%Y-%m-%d")
    water_schedule = 3
    food_schedule = 2
    if position in [1,2]:
        repotting_schedule = 6
    else:
        repotting_schedule = 0
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
        plant['next_water'] = calculate_next_water_date(plant['date_added'], int(plant['water_schedule']))
        plant['today_water'] = "Today!" if plant['next_water'] == TODAY.strftime("%Y-%m-%d") else plant['next_water']
        plant['food_event'] = is_event_today_or_tomorrow(plant['date_added'], int(plant['food_schedule']), 'months')
        plant['repotting_event'] = is_event_today_or_tomorrow(plant['date_added'], int(plant['repotting_schedule']), 'months')
    # Organize data by position for display
    organized_data = {position: [] for position in range(4)}
    for plant in plants_data:
        organized_data[plant['position']].append(plant)
    return render_template('index.html', organized_data=organized_data)

if __name__ == '__main__':
    app.run(debug=True)
