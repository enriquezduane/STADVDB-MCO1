import json
import mysql.connector
from datetime import datetime

# Load JSON data
with open('dataset/cleaned_games.json', 'r') as file:
    game_data = json.load(file)

# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="rootpassword",
    database="steam_games_data_warehouse"
)
cursor = db.cursor()

def etl_process(data):
    for game in data:
        # Insert into dim_game
        game_query = """INSERT INTO dim_game (game_id, name, required_age, price, metacritic_score, achievements)
                        VALUES (%s, %s, %s, %s, %s, %s)"""
        game_values = (game['game_id'], game['name'], game['required_age'], game['price'],
                       game['metacritic_score'], game['achievements'])
        cursor.execute(game_query, game_values)
        game_key = cursor.lastrowid

        # Insert into dim_platform
        platform_query = """INSERT INTO dim_platform (windows, mac, linux)
                            VALUES (%s, %s, %s)"""
        platform_values = (game['windows'], game['mac'], game['linux'])
        cursor.execute(platform_query, platform_values)
        platform_key = cursor.lastrowid

        # Insert into dim_time
        release_date = datetime.strptime(game['release_date'], '%Y-%m-%d')
        time_query = """INSERT INTO dim_time (release_date, year, month, day)
                        VALUES (%s, %s, %s, %s)"""
        time_values = (release_date, release_date.year, release_date.month, release_date.day)
        cursor.execute(time_query, time_values)
        time_key = cursor.lastrowid

        # Insert into dim_ownership
        ownership_query = """INSERT INTO dim_ownership (estimated_owners_min, estimated_owners_max)
                             VALUES (%s, %s)"""
        ownership_values = (game['estimated_owners_min'], game['estimated_owners_max'])
        cursor.execute(ownership_query, ownership_values)
        ownership_key = cursor.lastrowid

        # Insert into fact_game_sales
        fact_query = """INSERT INTO fact_game_sales (game_key, platform_key, time_key, ownership_key,
                        recommendations, positive_reviews, negative_reviews,
                        average_playtime_forever, peak_ccu)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        fact_values = (game_key, platform_key, time_key, ownership_key,
                       game['recommendations'], game['positive'],
                       game['negative'], game['average_playtime_forever'], game['peak_ccu'])

        cursor.execute(fact_query, fact_values)

    db.commit()

# Run ETL process
etl_process(game_data)

# Close database connection
db.close()
