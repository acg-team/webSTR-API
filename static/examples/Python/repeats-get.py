import requests
import pandas as pd

api_url = "http://webstr-api.ucsd.edu"
repeats_url = api_url + '/repeats/?gene_names=DUSP22'
resp = requests.get(repeats_url)
df_repeats = pd.DataFrame.from_records(resp.json())
