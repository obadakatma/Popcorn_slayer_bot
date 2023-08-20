import requests
import json
import os
apikey = os.getenv("APIKEY")
x = requests.get(f'http://api.themoviedb.org/3/search/tv?api_key={apikey}&query="how i met your mother"')
file = open("data.json", "w")
json.dump(x.json(), file, indent=6)
file.close()