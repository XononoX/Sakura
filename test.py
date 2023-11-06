
import json

def read_plants_data():
    with open('plants.json', 'r') as file:
        data = json.load(file)
    return data['plants']


plants_data = read_plants_data()

organized_data = {position: [] for position in range(4)}
for plant in plants_data:
    organized_data[plant['position']].append(plant)

print(organized_data)

