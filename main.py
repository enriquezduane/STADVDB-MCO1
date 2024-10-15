import json
import re
from datetime import datetime

def clean_game_data(json_file_path):
    """Cleans and transforms game data from a JSON file, returning a list of dictionaries."""

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        cleaned_games = []

        for game_id, game_data in data.items():
            cleaned_game = {}
            cleaned_game['game_id'] = int(game_id)
            cleaned_game['name'] = game_data.get('name')

            try:  # date conversion
                release_date_str = game_data.get('release_date')
                if release_date_str:
                    cleaned_game['release_date'] = datetime.strptime(release_date_str, '%b %d, %Y').strftime('%Y-%m-%d') # YYYY-MM-DD
                else:
                    cleaned_game['release_date'] = None  # or another default value
            except ValueError:
                cleaned_game['release_date'] = None


            cleaned_game['required_age'] = int(game_data.get('required_age', 0))  # default to 0
            cleaned_game['price'] = float(game_data.get('price', 0.0))  # default to 0.0
            cleaned_game['website'] = game_data.get('website')

            # convert bool strings to actual booleans
            for field in ['windows', 'mac', 'linux']:
                cleaned_game[field] = game_data.get(field) == True # standardize as True/False, handle nulls

            cleaned_game['metacritic_score'] = int(game_data.get('metacritic_score', 0))
            cleaned_game['metacritic_url'] = game_data.get('metacritic_url')
            cleaned_game['achievements'] = int(game_data.get('achievements', 0))
            cleaned_game['recommendations'] = int(game_data.get('recommendations', 0))
            cleaned_game['short_description'] = game_data.get('short_description')

            cleaned_game['user_score'] = int(game_data.get('user_score', 0))
            cleaned_game['positive'] = int(game_data.get('positive', 0))
            cleaned_game['negative'] = int(game_data.get('negative', 0))


            # clean estimated owners by removing spaces and converting to a numeric range
            estimated_owners = game_data.get('estimated_owners')
            if estimated_owners:
                match = re.match(r"(\d+) - (\d+)", estimated_owners)
                if match:
                    cleaned_game['estimated_owners_min'] = int(match.group(1))
                    cleaned_game['estimated_owners_max'] = int(match.group(2))
            
            cleaned_game['average_playtime_forever'] = int(game_data.get('average_playtime_forever', 0))
            cleaned_game['peak_ccu'] = int(game_data.get('peak_ccu', 0))

            cleaned_games.append(cleaned_game)


        return cleaned_games

    except json.JSONDecodeError as json_err:
        print(f"JSON decoding error: {json_err}")
        return None  # indicate error
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
    
def write_cleaned_data_to_file(cleaned_data, output_file_path):
    """Writes the cleaned game data to a file (JSON or CSV)."""

    try:
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            if output_file_path.endswith('.json'):
                json.dump(cleaned_data, outfile, indent=4) # write as JSON
            elif output_file_path.endswith('.csv'):
                # write as CSV
                import csv
                fieldnames = cleaned_data[0].keys() # get column headers
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(cleaned_data)                
            else:
                raise ValueError("Unsupported file format. Please use .json or .csv")
        print(f"Cleaned data written to {output_file_path}")

    except Exception as e:
        print(f"Error writing to file: {e}")
        

if __name__ == "__main__":
    json_file_path = 'dataset/games.json'
    output_file_path = 'cleaned_games.json'
    cleaned_data = clean_game_data(json_file_path)

    if cleaned_data:
        write_cleaned_data_to_file(cleaned_data, output_file_path)