#import xml.etree.cElementTree as ElementTree
#use standard ElementTree because cElementTree does not support parser argument in 2.7 http://bugs.python.org/issue9708
import xml.etree.ElementTree as ElementTree
import json
import os
import htmlentitydefs
from datetime import datetime


'''
tips
* need DTD to parse entity, http://stackoverflow.com/questions/9898277/how-to-use-python-parse-xml-doc-which-contains-character
* performance comparison, http://effbot.org/zone/celementtree.htm
* http://code.activestate.com/lists/python-list/97976/
* http://stackoverflow.com/questions/16624790/parsing-large-xml-data-using-pythons-elementtree
* clean memory: http://effbot.org/zone/element-iterparse.htm#incremental-parsing
** http://stackoverflow.com/questions/10074200/should-memory-usage-increase-when-using-elementtree-iterparse-when-clearing
* cElementTree does not support parser argument in 2.7 http://bugs.python.org/issue9708
'''

class MyCounter:
	def __init__(self):
		self.data = {}
		
	def inc(self, key, count=1):
		if not key in self.data:
			self.data[key]=0
		self.data[key] += count

class JsonFileManager:
	def __init__(self):
		self.visited=[]

		
	def complete(self):
		for filename in self.visited:
			with open(filename,'a') as f:
				f.write("]")
		
	def append(self, filename, json_data):
		text = json.dumps(json_data, sort_keys=True, indent=4)
		#print filename, datetime.now()
		
		if filename in self.visited:
			with open(filename,'a') as f:
				f.write(",\n" + text)
		else:
			self.visited.append(filename)
			with open(filename,'wb') as f:
				f.write("[\n" + text)

class MyUtilDblp:
	BIB_TYPE_SELECT = set(['inproceedings', 'proceedings'])
	BIB_TYPE = set(['article', 'inproceedings', 'proceedings', 'book', 'incollection', 'phdthesis', "mastersthesis", "www"])
	
	@staticmethod
	def load_config():
		# load config file
		with open("config.json") as f:
			global_config = json.loads( f.read())
			#print json.dumps(global_config, indent=4, sort_keys=True)
			return global_config
		return None	
	
	@staticmethod
	def dblp_xml2json(elem):
		json_data = {}
		json_data["_meta"]= elem.attrib
		json_data["_meta"]["type"]= elem.tag
			
		for child in elem:
			if child.tag in ['author', 'editor']:
				key  = child.tag +"s"
				if not key in json_data:
					json_data[key] =[]
				json_data[key].append(child.text)
			else:
				json_data[child.tag] = child.text
				if len(child.attrib)>0:
					json_data[child.tag + "_attrib"] = child.attrib
		
		return json_data	

	@staticmethod
	def clear_element(elem, root):
		elem.clear()
		root.clear()


	@staticmethod
	def dblp_extract_semweb(filename_dblp_xml, filename_output):
		json_file_manager = JsonFileManager()
		
		parser = ElementTree.XMLParser()
		parser.entity.update((x, unichr(i)) for x, i in htmlentitydefs.name2codepoint.iteritems())
		
		context = ElementTree.iterparse(filename_dblp_xml,parser=parser, events=("start", "end"))
		event, root = context.next()

		counter = MyCounter()
		counter.inc("total")
		for event, elem in context:
			if event == "end" and elem.tag in MyUtilDblp.BIB_TYPE:
				if counter.data["total"] %10000 ==0:
					print "[{0}] processed {1}".format(datetime.now(), counter.data)
				counter.inc("total")
				counter.inc(elem.tag)
				
				#only process select bib_type
				if elem.tag in MyUtilDblp.BIB_TYPE_SELECT:
					#extract xkey
					xkey = elem.attrib["key"]	
					for child in elem:
						if child.tag == 'crossref':
							if None!=child.text:
								xkey = child.text
						
					#skip irrelevant elements
					if None!=xkey and xkey.startswith("conf/semweb/"):
						counter.inc('semweb')
						
						# write json data to corresponding file
						#filename_output = os.path.join(dir_output, xkey.replace("/","_"))
						json_data = MyUtilDblp.dblp_xml2json(elem)
							
						json_file_manager.append(filename_output, json_data)
						#text = json.dumps(json_data, sort_keys=True, indent=4)
				
				#clean memory (both the element and the root reference to the element)
				MyUtilDblp.clear_element(elem, root)
		
		#final write to close json array in each file
		json_file_manager.complete()
		print "[{0}] processed {1}".format(datetime.now(), counter.data)

global_config= MyUtilDblp.load_config()
filename ={}
filename["dblp"]= os.path.join(global_config['home'], 'local/raw/dblp.xml')
filename["dblp_dtd"]= os.path.join(global_config['home'], 'local/raw/dblp_dtd.xml')
filename["dblp_json"]= os.path.join(global_config['home'], "data/raw/dblp_semweb.json")


MyUtilDblp.dblp_extract_semweb(filename["dblp"], filename["dblp_json"])
