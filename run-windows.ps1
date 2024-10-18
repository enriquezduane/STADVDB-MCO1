# Copy the original dataset from the Downloads directory to the local directory
Copy-Item "$HOME\Downloads\games.json" -Destination ".\dataset\games.json"

# Run the Docker container to the database
docker-compose down -v
docker-compose up -d --build

# Wait for the database to be ready
Start-Sleep -Seconds 5

# Make virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r .\dependencies.txt

# Run the pipeline
python cleanup.py
python etl.py

# Run the tests c 
python test.py

# Run the server
python server.py

# Clean up
docker-compose down -v
Remove-Item -Recurse -Force .\venv
