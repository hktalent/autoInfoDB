#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import requests as requestsSs
import urllib3,re,os,os.path,json,zipfile

from  zipfile import ZipFile
urllib3.disable_warnings()
requestsSs.packages.urllib3.disable_warnings()

requests = requestsSs.session()
myTime=(13, 15)

headers1={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) Gecko/20100101 Firefox/91.0",
"Accept": "text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01",
"Accept-Language": "en-US,en;q=0.5",
"X-Requested-With": "XMLHttpRequest",
"Connection": "close",
"Referer": "http://db.auto.sina.com.cn/2326/peizhi/"}


szLf="db/allLists.json"
def saveDb(o,szFileName=szLf,isJson=True):
	f=open(szFileName,"wb")
	szTmp=o
	if isJson:
		szTmp=json.dumps(o)
	szTmp=szTmp.encode('utf-8')
	f.write(szTmp)
	f.close()

def getFileInfo(s):
	aL=None
	if os.path.exists(s):
		f=open(s,"rb")
		aL=f.read()
		f.close()
	return aL

def fnDebugInfo(s):
	print(s)

# 图片数据有相同的,直接使用
g_imgs={}
# 图片数据的缓存和下载
def getUrlImg(url,id,szName):
	if url in g_imgs:
		return g_imgs[url]
	
	# 处理过的本地数据
	szKey=id + "_"+szName
	if "http" not in url:
		g_imgs[url]=szKey
		return url

	szTmp1="db/" + szKey +".jpg"
	s=getFileInfo(szTmp1)
	if None == s:
		r=requests.get(url,headers=headers1,stream=True,verify=False,timeout=myTime)
		with open(szTmp1, 'wb') as f:
			for chunk in r:
				f.write(chunk)
	g_imgs[url]=szKey
	return szKey

# get all auto info
aL=[]
if not os.path.exists(szLf):
	url="https://db.auto.sina.com.cn/api/cms/car/getBrandList.json?callback=&_=1630642377288"
	r1 = requests.get(url,headers=headers1,verify=False,timeout=myTime)
	a = json.loads(r1.text)["data"]
	
	for k in a:
		x=a[k]
		for i in x:
			# zhName,enName,pyName,logo,power
			i["logo"]=getUrlImg("http:"+i["logo"],i["id"],"id")
			# i["logo"]=requests.get("http:"+i["logo"],headers=headers1,verify=False,timeout=myTime).text
			aL.append(i)
			print(i["id"] + " "+ i["zhName"] + " is ok")
	saveDb(aL)
	# print(szTmp)
else:
	aL=json.loads(getFileInfo(szLf))

szIds=""
bSave=False
for j in aL:
	# 没有数据就说明还没有获取过
	if not("data" in j) or None == j["data"]:
		bSave=True
		# 得到销售信息 serialId
		fnDebugInfo("开始获取 " + j["id"] + " 的serialId ...")
		r2 = requests.get("https://db.auto.sina.com.cn/api/cms/car/getSerialList.json?sellStatus=1,2,3&brandid=" + j["id"],headers=headers1,verify=False,timeout=myTime)
		aT = json.loads(r2.text)["data"]
	else:
		aT=j["data"]

	for x in aT:
		# 销售的列表
		y = x["serialList"]
		# 遍历每一款车中更细款的信息、包含价格、图片
		for z in y:
			# 图片获取
			if "serialWhiteLogo" in z and "http" in z["serialWhiteLogo"]:
				fnDebugInfo("开始获取 " + z["serialId"] + " 的 serialWhiteLogo图片数据 ...")
				z["serialWhiteLogo"]=getUrlImg(z["serialWhiteLogo"],z["serialId"],"serialId")
				# z["serialWhiteLogo"]=requests.get(z["serialWhiteLogo"],verify=False,timeout=myTime).text
			# 通过 "serialId 获取更详细的配置信息
			if not("data" in z) or None == z["data"]:
				fnDebugInfo("开始获取 " + z["serialId"] + " 的 data详细数据 ...")
				r3 = requests.get("https://db.auto.sina.com.cn/api/cms/car/getCarBySerialId.json?status=1,2,3&serialid=" + z["serialId"],headers=headers1,verify=False,timeout=myTime)
				aT1 = json.loads(r3.text)["data"]
			else:
				aT1=z["data"]

			for w in aT1:
				if "photo" in w and "http" in w["photo"]:
					fnDebugInfo("开始获取 " + w["id"] + " 的 photo详细数据 ...")
					w["photo"]=getUrlImg(w["photo"],w["id"],"photoSerialId")
					# w["photo"]=requests.get(w["photo"],headers=headers1,verify=False,timeout=myTime).text
				if 0 < len(szIds):
					szIds= szIds + ","
				szIds= szIds + w["id"]
			z["data"]=aT1
	j["data"]=aT
# 有改变就保存
if bSave:
	saveDb(aL)

szCurlDir=os.path.dirname(os.path.abspath(__file__))
# 一次性获取所有汽车信息
fnDebugInfo("start get all car info ...")
if 0 < len(szIds):
	a=szIds.split(',')
	fnDebugInfo("共 " + str(len(a)) + " 款车")

	xxx=1
	nStep=100
	
	with ZipFile("db/allAutoCarsInfo.zip", mode='a', compression=zipfile.ZIP_DEFLATED ) as fZip:	
		for j in range(0,len(a),nStep):
			xTmp1=a[j:j+nStep]
			szParms = ",".join(xTmp1)
			
			print("  do " + str(xxx)+" / "+str(len(a)) + " ...\r",sep="",end="",flush=True)

			# rsp = requests.post("https://db.auto.sina.com.cn/api/car/getFilterCarInfo.json",headers=headers1,stream=True,data={"carid":szIds,"callback":"","_":1630642383503},verify=False,timeout=(1300, 1500))
			rsp = requests.get("https://db.auto.sina.com.cn/api/car/getFilterCarInfo.json?carid="+szParms+"&callback=&_=1630642383503" + str(xxx),headers=headers1,stream=True,verify=False,timeout=(1300, 1500))
			# rsp.raise_for_status()
			if rsp.status_code not in [403,404,500,405]:
				szTmpFile=str(j) + ".json"
				with open(szTmpFile, 'wb') as f1:
					aX=[]
					for chunk in rsp:
						f1.write(chunk)
						xxx=xxx+1
				fZip.write(szTmpFile)
				os.remove(szTmpFile)

			else:
				print(rsp.status_code)
				break
