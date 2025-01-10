from requests import post

data = {
	'dates':["2025-01-14 00:00:00"],
	'statuses':[0]
}

r = post(url='http://127.0.0.1:1820/update_work_rest_status', json=data)
print(r.text)
