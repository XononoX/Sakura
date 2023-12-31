
import json
import pandas as pd
import requests
import boto3
from datetime import datetime, timedelta

tokens = {}
with open("creds", "r") as creds:
    for line in creds:
        key, value = line.strip().split("=")
        tokens[key] = value.replace('"', '')


def trefle_find_plant(query: str):
    call = f"https://trefle.io/api/v1/plants/search?q={query}&token={TREFLE_TOKEN}"
    print(f"Running trefle API search:\n{call}")
    response = requests.get(call)

    if response.status_code == 200:
        data = response.json()

        filename = "trefle_jsons/" + query.replace(" ", "_") + "_plant.json"
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    else:
        print(f"Failed to retrieve plants data, Status Code: {response.status_code}")
def trefle_find_species(query: str):
    call = f"https://trefle.io/api/v1/species/search?q={query}&token={TREFLE_TOKEN}"
    print(f"Running trefle API search:\n{call}")
    response = requests.get(call)

    if response.status_code == 200:
        data = response.json()

        filename = "trefle_jsons/" + query.replace(" ", "_") + "_species.json"
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    else:
        print(f"Failed to retrieve species data, Status Code: {response.status_code}")
def trefle_pull_request(query: str):
    response = requests.get(query)

    if response.status_code == 200:
        data = response.json()

        filename = "trefle_jsons/" + "request.json"
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    else:
        print(f"Failed to retrieve request, Status Code: {response.status_code}")
def trefle_pull_plant(slug: str):
    call = f"https://trefle.io/api/v1/plants/{slug}?token={TREFLE_TOKEN}"
    print(f"Running trefle API search:\n{call}")
    response = requests.get(call)

    if response.status_code == 200:
        data = response.json()
        
        filename = f"trefle_jsons/{slug}_plant.json"
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    else:
        print(f"Failed to retrieve plants data, Status Code: {response.status_code}")
def trefle_pull_species(slug: str):
    call = f"https://trefle.io/api/v1/species/{slug}?token={TREFLE_TOKEN}"
    print(f"Running trefle API search:\n{call}")
    response = requests.get(call)

    if response.status_code == 200:
        data = response.json()

        filename = f"trefle_jsons/{slug}_species.json"
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    else:
        print(f"Failed to retrieve species data, Status Code: {response.status_code}")
def trefle_pull_plant_id(id: int):
    id_str = str(id)
    print(f"Finding plant id: {id_str}")
    call = f"https://trefle.io/api/v1/plants/{id_str}?token={TREFLE_TOKEN}"
    print(f"Running trefle API search:\n{call}")
    response = requests.get(call)

    if response.status_code == 200:
        data = response.json()
        
        filename = f"trefle_jsons/{id_str}_plant.json"
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    else:
        print(f"Failed to retrieve plants data, Status Code: {response.status_code}")
def trefle_pull_species_id(id: int):
    id_str = str(id)
    print(f"Finding species id: {id_str}")
    call = f"https://trefle.io/api/v1/species/{id_str}?token={TREFLE_TOKEN}"
    print(f"Running trefle API search:\n{call}")
    response = requests.get(call)

    if response.status_code == 200:
        data = response.json()

        filename = f"trefle_jsons/{id_str}_species.json"
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    else:
        print(f"Failed to retrieve species data, Status Code: {response.status_code}")


def perenual_pull_species_list(page=1):
    call = f"https://perenual.com/api/species-list?key={tokens['PERENUAL_TOKEN']}&page={page}"
    print(f"Running perenual API search:\n{call}")
    response = requests.get(call)

    if response.status_code == 200:
        data = response.json()

        filename = "perenual_jsons/plant_list.json"
        if page != 1:
            filename = f"perenual_jsons/plant_list_page_{page}.json"
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
    else:
        print(f"Failed to retrieve plants data, Status Code: {response.status_code}")
def perenual_query_api(query: str):
    query = query.lower()
    call = f"https://perenual.com/api/species-list?key={tokens['PERENUAL_TOKEN']}&q={query.lower()}"
    print(f"Running perenual API search:\n{call}")
    response = requests.get(call)

    if response.status_code == 200:
        data = response.json()

        filename = f"perenual_jsons/query_{query.lower().replace(' ', '_')}.json"
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4)
        return data['data']
    else:
        print(f"Failed to retrieve plants data, Status Code: {response.status_code}")
        return []

    
s3 = boto3.client('s3')
bucket_name = 'plants-data'
file_name = 'plant_data.json'
def read_from_s3():
    try:
        data = s3.get_object(Bucket=bucket_name, Key=file_name)
        plants_data = json.loads(data['Body'].read().decode('utf-8'))
        return plants_data
        #return plants_data['plants']
    except Exception as e:
        print(e)
        return None  # or handle error appropriately
def write_to_s3(data):
    try:
        s3.put_object(Bucket=bucket_name, Key=file_name, Body=json.dumps(data))
        print("Success!")
    except Exception as e:
        print(e)


def read_local_plant_data(filename='plants.json'):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data['plants']
