import requests

r = requests.get("https://www.longtermtrends.net/data-m2-money-stock/")
print(r.text)