from requests import post

data = {
	"url": "",
	"data": {"load_level": "JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP",
	         "start": "2024-07-30 00:00:00", "end": "2024-07-30 20:00:00", "second": "60"}
}

r = post(url='http://127.0.0.1:1820/train_cop_model', json=data)
print(r.text)
