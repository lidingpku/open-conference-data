from libx import UnicodeReader, UnicodeWriter, MyCounterKeyValue, UtilSyntax, UtilLinkDbpedia, MyCounter
import re
import os
import hashlib	
import json
import sys
from subprocess import call


# load config file
with open("config.json") as f:
	global_config = json.load( f)

filename = os.path.join(
	global_config["home"],
#	"data/manual/full_iswc_paper_pdf.csv")
	"data/manual/iswc-publication-paper.csv")
class MyCounter:
	def __init__(self):
		self.data = {}
	
	def inc(self, key, cnt=1):
		if not key in self.data:
			self.data[key]=0
		self.data[key] += cnt

	def list(self, min_count=0):
		ret = {}
		for k,v in self.data:
			if v >= min_count:
				ret[k]=v
				
		return ret

with open(filename) as f:
	csvreader = UnicodeReader(f)
	headers =  csvreader.next()
	
	counter = MyCounter()
	for row in csvreader:
		entry = dict(zip(headers, row))
		
		entry["proceedings_uri"] = entry["proceedings_uri"].replace("demos/proceedings","demos-proceedings")
		dir_id = entry["year"]+"-"+ os.path.basename(entry["proceedings_uri"]) 
		counter.inc(dir_id)
		counter.inc(dir_id+"-downloaded", 0)
		
		state = {"paper_uri", entry["paper_uri"]}
		if len(entry["link_open_access"])>0:
			
			
			if entry["link_open_access"].lower().endswith(".html") or entry["link_open_access"].lower().endswith(".htm"):
				print "skip ", entry["link_open_access"]
				continue
				
			filename_output = os.path.join(
				global_config["home"],
				"local/open_access",
				dir_id,
				os.path.basename(entry["link_open_access"])
				)
			dirname =  os.path.dirname(filename_output)
			if not os.path.exists(dirname):
				os.makedirs(dirname)

			#print "---".join([entry["link_open_access"], filename_output])

			if os.path.exists(filename_output):
				counter.inc(dir_id+"-downloaded")
			else:
				command= "wget \"{0}\" -P {1}".format(
					entry["link_open_access"], 
					dirname)
				print command
				call(command, shell=True)
				
				
	for key in sorted(counter.data.keys()):
		print "%s\t%d" % (key,counter.data[key])
