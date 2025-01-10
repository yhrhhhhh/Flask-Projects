from requests import post

data = {"load_level": 85,"temperature": 13, "frozen_temp": 8}

r = post(url='http://127.0.0.1:1820/select_cop', json=data)
print(r.text)
