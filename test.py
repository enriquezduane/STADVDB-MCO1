import mysql.connector
import time

# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="rootpassword",
    database="steam_games_data_warehouse"
)

def run_test_case(query, description, expected_output_type=None):  # Added description and output type
    start_time = time.time()
    cursor = db.cursor()
    try:
      cursor.execute(query)
      if expected_output_type == "count": # Check if we expect a single count
          results = cursor.fetchone()[0] # Fetch single count value
      else:
          results = cursor.fetchall()
    except Exception as e:
      results = f"Error: {e}"
    end_time = time.time()
    execution_time = end_time - start_time


    return execution_time, results


# Test cases (improved structure and added expected output type)
test_cases = [
    {"description": "Roll Up - Average Metacritic Score and Total Recommendations by Year",
     "query": """
        SELECT 
            dt.year,
            AVG(dg.metacritic_score) AS avg_metacritic_score,
            SUM(fgs.recommendations) AS total_recommendations
        FROM 
            fact_game_sales fgs
        JOIN dim_game dg ON fgs.game_key = dg.game_key
        JOIN dim_time dt ON fgs.time_key = dt.time_key
        GROUP BY 
            dt.year
        ORDER BY 
            dt.year;
     """,
      "expected_output_type": None
    },
    {"description": "Drill Down - Games Released and Average Price by Month ({year})",
     "query": """
        SELECT 
            dt.month,  -- Drill down to month
            COUNT(DISTINCT fgs.game_key) AS games_released,
            AVG(dg.price) AS avg_price
        FROM 
            fact_game_sales fgs
        JOIN dim_game dg ON fgs.game_key = dg.game_key
        JOIN dim_time dt ON fgs.time_key = dt.time_key
        WHERE 
            dt.year = {year}  -- Filter for a specific year
        GROUP BY 
            dt.month  -- Group by month
        ORDER BY 
            dt.month; 
     """,
      "expected_output_type": None,
      "parameters": [2021, 2022, 2023]

    },
    {"description": "Slice and Dice - Game count by Price Range and Metacritic Score ({platform})",
     "query": """
        SELECT 
            CASE 
                WHEN dg.price < 10 THEN 'Under $10'
                WHEN dg.price >= 10 AND dg.price < 30 THEN '$10 - $29.99'
                ELSE '$30 and above'
            END AS price_range,
            CASE 
                WHEN dg.metacritic_score < 50 THEN 'Low'
                WHEN dg.metacritic_score >= 50 AND dg.metacritic_score < 75 THEN 'Medium'
                ELSE 'High'
            END AS metacritic_range,
            COUNT(*) AS game_count
        FROM 
            fact_game_sales fgs
        JOIN dim_game dg ON fgs.game_key = dg.game_key
        JOIN dim_platform dp ON fgs.platform_key = dp.platform_key
        WHERE 
            dp.{platform} = TRUE  -- Slicing by platform
        GROUP BY 
            price_range, metacritic_range  -- Dicing
        ORDER BY 
            price_range, metacritic_range;
     """,
      "expected_output_type": None,
      "parameters": [{"platform": "windows"}, {"platform": "mac"}, {"platform": "linux"}]

    },
    {"description": "Pivot - Number of Games Released per Platform Combination by Year",
     "query": """
        SELECT 
            dt.year,
            SUM(CASE WHEN dp.windows = TRUE AND dp.mac = FALSE AND dp.linux = FALSE THEN 1 ELSE 0 END) AS windows_only,
            SUM(CASE WHEN dp.windows = FALSE AND dp.mac = TRUE AND dp.linux = FALSE THEN 1 ELSE 0 END) AS mac_only,
            SUM(CASE WHEN dp.windows = FALSE AND dp.mac = FALSE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS linux_only,
            SUM(CASE WHEN dp.windows = TRUE AND dp.mac = TRUE AND dp.linux = FALSE THEN 1 ELSE 0 END) AS windows_mac,
            SUM(CASE WHEN dp.windows = TRUE AND dp.mac = FALSE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS windows_linux,
            SUM(CASE WHEN dp.windows = FALSE AND dp.mac = TRUE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS mac_linux,
            SUM(CASE WHEN dp.windows = TRUE AND dp.mac = TRUE AND dp.linux = TRUE THEN 1 ELSE 0 END) AS all_platforms
        FROM 
            fact_game_sales fgs
        JOIN dim_time dt ON fgs.time_key = dt.time_key
        JOIN dim_platform dp ON fgs.platform_key = dp.platform_key
        GROUP BY 
            dt.year
        ORDER BY 
            dt.year;
     """,
      "expected_output_type": None


    },
]

# execute tests and record results (multiple runs)
num_runs = 3  # Number of test runs
test_results = []

for test_case in test_cases:
    if "parameters" in test_case:  # Parameterized query
        for params in test_case["parameters"]:
            execution_times = []
            if isinstance(params, dict):
                query = test_case["query"].format(**params)
                description = test_case["description"].format(**params)  # Format description
            else:  # Assumes other parameter types are suitable for % formatting
                query = test_case["query"].format(year=params)
                description = test_case["description"].format(year=params) #Assumes its a year parameter, format accordingly


            for _ in range(num_runs):
                execution_time, _ = run_test_case(query, description)
                execution_times.append(execution_time)
            avg_execution_time = sum(execution_times) / num_runs
            test_results.append({
                "test_case": {"description": description},  # Store formatted description
                "execution_times": execution_times,
                "avg_execution_time": avg_execution_time
            })
    else:  # Non-parameterized query
        execution_times = []
        for _ in range(num_runs):
            execution_time, _ = run_test_case(test_case["query"], test_case["description"])
            execution_times.append(execution_time)
        avg_execution_time = sum(execution_times) / num_runs
        test_results.append({
            "test_case": test_case,  # No formatting needed
            "execution_times": execution_times,
            "avg_execution_time": avg_execution_time
        })

# Write execution times to the file
with open("dataset/test_results.txt", "w") as f:
    for result in test_results:
        f.write(f"Test Case: {result['test_case']['description']}\n")
        for i, execution_time in enumerate(result['execution_times']):
             f.write(f"Run {i+1} Execution Time: {execution_time:.4f} seconds\n")
        f.write(f"Average Execution Time: {result['avg_execution_time']:.4f} seconds\n")
        f.write("-" * 20 + "\n")  # Separator between test cases

db.close()
print("Test results written to test_results.txt")