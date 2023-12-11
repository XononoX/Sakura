"""
This defines the Flask scripting for the Sakura front-end
"""

import json
from dash.dependencies import Input, Output
from dash import html, State, Dash, dcc
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for

from backend import read_from_s3, read_local_plant_data, write_to_s3, perenual_query_api as query_api

# Include external stylesheets - assuming 'styles.css' is accessible at the root of your web server
external_stylesheets = [
    'https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css',
    '/styles.css'  # This path needs to be accessible from where your Dash app is running
]

app = Flask(__name__)
app.config['DEBUG'] = True
dash_app = Dash(
    __name__, server=app,
    external_stylesheets=external_stylesheets,
    url_base_pathname='/dashboard/'
    )

def read_plants_data():
    #return read_local_plant_data()
    return read_from_s3()

def write_plants_data(data):
    #with open('plants.json', 'w') as file:
    #    json.dump({'plants': data}, file, indent=4)
    write_to_s3(data)


def update_plant_data(plant_id, updates):
    plants_data = read_plants_data()
    for plant in plants_data:
        if plant['id'] == plant_id:
            plant.update(updates)
            break
    write_plants_data(plants_data)

@dash_app.callback(
    [Output('name-input', 'value'),
     Output('position-input', 'value'),
     Output('frequency-input', 'value'),
     Output('food-schedule-input', 'value'),
     Output('repotting-schedule-input', 'value')],
    [Input('plant-dropdown', 'value')]
)
def update_input_values(plant_id):
    plants_data = read_plants_data()
    if plant_id is not None:
        plant = next((p for p in plants_data if p['id'] == plant_id), None)
        if plant:
            return plant['name'], plant['position'], plant['water_schedule'], plant['food_schedule'], plant['repotting_schedule']
    return '', '', '', '', ''

@dash_app.callback(
    Output('update-output', 'children'),
    Input('update-button', 'n_clicks'),
    [State('plant-dropdown', 'value'),
     State('name-input', 'value'),
     State('position-input', 'value'),
     State('frequency-input', 'value'),
     State('food-schedule-input', 'value'),
     State('repotting-schedule-input', 'value')])
def update_plant_info( # Callback to update plant info from plotly dash form
    n_clicks, plant_id, name, position,
    water_schedule, food_schedule, repotting_schedule
    ):
    if n_clicks is None:
        return ''

    # Sanitize input values to ensure they are integers
    try:
        position = int(position) if position else 0
        water_schedule = int(water_schedule) if water_schedule else 0
        food_schedule = int(food_schedule) if food_schedule else 0
        repotting_schedule = int(repotting_schedule) if repotting_schedule else 0
    except ValueError:
        return "Please enter valid integer values for schedules and position."

    new_data = {
        'name': name,
        'position': position,
        'water_schedule': water_schedule,
        'food_schedule': food_schedule,
        'repotting_schedule': repotting_schedule
    }
    update_plant_data(plant_id, new_data)
    return f"Updated plant {plant_id} with new details."

dash_app.layout = html.Div([ # Defines the form for updating details of plant data:
    dcc.Dropdown(
        id='plant-dropdown',
        options=[{'label': f"ID: {plant['id']}, {plant['name']}", 'value': plant['id']} 
                 for plant in read_plants_data()],
        placeholder="Select a plant", style={'width': '730px', 'paddingBottom': '5px'}
    ),
    html.Div([
        dcc.Input(id='name-input', type='text', placeholder='Enter plant name', style={'width': '200px'}),
        html.Label('Plant Name', htmlFor='name-input', style={'paddingLeft': '5px'})
    ]),
    html.Div([
        dcc.Input(id='position-input', type='number', placeholder='Enter new position', style={'width': '200px'}),
        html.Label('Position (0=Front Yard, 1=Inside-Sunlight, 2=Inside-Lowlight, 3=Backyard)',
                   htmlFor='position-input', style={'paddingLeft': '5px'})
    ]),
    html.Div([
        dcc.Input(id='frequency-input', type='number', placeholder='Enter watering frequency', style={'width': '200px'}),
        html.Label('Watering Frequency (Days)', htmlFor='frequency-input', style={'paddingLeft': '5px'})
    ]),
    html.Div([
        dcc.Input(id='food-schedule-input', type='number', placeholder='Enter food schedule', style={'width': '200px'}),
        html.Label('Food Schedule (Months)', htmlFor='food-schedule-input', style={'paddingLeft': '5px'})
    ]),
    html.Div([
        dcc.Input(id='repotting-schedule-input', type='number', placeholder='Enter repotting schedule', style={'width': '200px'}),
        html.Label('Repotting Schedule (Months)', htmlFor='repotting-schedule-input', style={'paddingLeft': '5px'})
    ]),
    html.Div(
        html.Button('Update Plant Info', id='update-button',
            style={
                'backgroundColor': '#007bff',  # Use a specific color code if needed
                'color': 'white',
                'border': 'none',
                'width': '200px',
                'height': '40px'
                }
        )
    ),
    html.Div(id='update-output')
], style={'backgroundColor': 'rgb(105, 174, 105)', 'padding': '20px', 'height': '100vh'})


TODAY = datetime.today()
TOMORROW = TODAY + timedelta(days=1)
perenual_msg = "Upgrade Plans To Premium/Supreme - https://perenual.com/subscription-api-pricing. I'm sorry"


def get_next_plant_id(data):
    return max([plant.get('id', 0) for plant in data] + [0]) + 1

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
        return redirect(url_for('home'))
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
