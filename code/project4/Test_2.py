from requests import post

"""
请求参数说明：

- `url`(`str`)：目标请求地址，例如 `""`。  
- `data_compare`(`dict`)：对比数据参数，包含 `tag`【最高气温，最低气温，白天平均温度8-18，夜晚平均温度，高峰模式运行时长，夜晚模式运行时长，空调供水温度，水源侧进水温度，冷热量，能耗】（严格按照顺序，逗号分隔），
`start`（开始时间），`end`（结束时间），`second`（时间间隔，单位秒）。  
- `data` (`dict`)：查询数据参数，与 `data_compare` 结构相同，表示单独日期的数据查询请求。  
- `similar_dates`(`list[str]`)：相似日期的列表，每个元素为日期字符串，格式为 `"YYYY-MM-DD"`。
"""

data = {
	"url": "",
	"data_compare": {"tag": "JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP",
	"start": "2024-07-30 00:00:00", "end": "2024-08-30 00:00:00", "second": "600"},
	"data": {"tag": "JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP,JIFANG/JIFANG/JF_COP",
	"start": "2024-08-31 00:00:00", "end": "2024-09-1 00:00:00", "second": "600"},
	"similar_dates":[
	  "2024-08-29",
	  "2024-08-28",
	  "2024-08-27",
	  "2024-08-26",
	  "2024-08-25"
	]
}

r = post(url='http://127.0.0.1:1820/Operating_conditions_curve', json=data)
print(r.text)

