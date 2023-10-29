# Sakura
Help keep track of your plants

# Front-end
4 panels: Front Yard, Backyard, Inside (sunlight) and Inside (low-light).
Allows the user to input plant names, then displays the list of plants in each location, sorting those with events (harvest, fertilize, move, or repot) first, then those that need to be watered next.

Back-end will parse the input plant name, then query a database of plants to retrieve watering frequency, times when plants should be moved/harvested, then add valid rows to the user's S3 bucket table and push that update to the front-end table.
