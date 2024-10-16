# copy the original dataset from the downloads directory to the local directory
cp ~/Downloads/games.json ./dataset/games.json

# run the docker container to the database
docker-compose down -v
docker-compose up -d --build

# wait for the database to be ready
sleep 5

# make virtual environment
python3 -m venv venv
source venv/bin/activate

# install dependencies
pip3 install -r dependencies.txt

# run the pipeline
python3 cleanup.py
python3 etl.py

# run the tests
python3 test.py

# run the server
python3 server.py


# clean up
docker-compose down -v
rm -rf venv 
