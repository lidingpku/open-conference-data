import json
import os
from datetime import datetime

class MyCounter:
	
	def __init__(self):
		self.data = {"total":0}
		
	def inc(self, key="total", count=1, bPrint=True):
		if bPrint and self.data["total"] %1000000 ==0:
			print "[{0}] processed {1}".format(datetime.now(), self.data)
		
		if not key in self.data:
			self.data[key]=0
		self.data[key] += count
		
		

# load config file
with open("config.json") as f:
	global_config = json.loads( f.read())
	#print json.dumps(global_config, indent=4, sort_keys=True)


class FSMDblpXml:
	def __init__(self):
		self.state = "accept"
		
	def processLine(self, line):
		ret = None

		#update state
		if line.startswith("<inproceedings") or line.startswith("<proceedings"):
			if line.find("conf/semweb/")>0:
				self.state = "accept"
		elif line.startswith("</inproceedings>") :
			if "accept" == self.state:
				self.state = "reject-next"
				ret ="</inproceedings>\n"
		elif line.startswith("</proceedings>"):
			if "accept" == self.state:
				self.state = "reject-next"
				ret ="</proceedings>\n"
		elif line.startswith("<dblp>"):
			self.state = "reject-next"
			ret = line
		elif line.startswith("</dblp>"):
			self.state = "reject-next"
			ret = line
		
		if "reject-next" == self.state:
			self.state = "reject"
		elif "accept" == self.state:
			ret = line

		return ret

filename ={}
filename["dblp"]= os.path.join(global_config['home'], 'local/raw/dblp.xml')
filename["dblp_semweb"]= os.path.join(global_config['home'], 'data/raw/dblp_semweb.xml')

fsm = FSMDblpXml()
counter = MyCounter()
with open(filename["dblp_semweb"], "wb") as f_out:
	with open(filename["dblp"], "r") as f_in:
		for line in f_in:
			counter.inc()
			ret = fsm.processLine(line)
			if ret !=None:
				#print ret
				counter.inc("write")
				f_out.write(ret)
		
