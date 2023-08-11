import requests
import json
import os
apikey = os.getenv("APIKEY")
x = requests.get(f'http://api.themoviedb.org/3/search/movie?api_key={apikey}&query="Batman"').json()
file = open("data.json", "w")
json.dump(x, file, indent=6)
file.close()