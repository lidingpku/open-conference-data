import rdflib
import json
import os
import csv
import datetime

class MyUtil:
	@staticmethod
	def init_dir(filename):
		dirname = os.path.dirname(filename)
		if not os.path.exists(dirname):
			os.makedirs(dirname)

	@staticmethod
	def print_pretty_json(data):
		print json.dumps(data, indent=4, sort_keys=True)
		
	@staticmethod
	def load_config():
		# load config file
		with open("config.json") as f:
			global_config = json.loads( f.read())
			#print json.dumps(global_config, indent=4, sort_keys=True)
			return global_config
		return None

	@staticmethod
	def query_graph(filename_data, filename_query, filename_output):
		from subprocess import call
		
		command= "/opt/apache-jena-2.10.1/bin/arq --data {0} --query {1} --results CSV > {2}".format(filename_data, filename_query, filename_output)
		#print command
		call(command, shell=True)
		
	@staticmethod
	def rewrite_uri2qname(text):
		map_uri_qname = [ 
			["http://www.w3.org/1999/02/22-rdf-syntax-ns#","rdf:"],
			["http://www.w3.org/2002/07/owl#","owl:"],
			["http://xmlns.com/foaf/0.1/","foaf:"],
			["http://purl.org/dc/terms/","dcterms:"],
			["http://purl.org/dc/elements/1.1/","dc:"],
			["http://swrc.ontoware.org/ontology#","swrc:"],
			["http://data.semanticweb.org/ns/swc/ontology#","swc:"],
			["http://www.w3.org/2002/12/cal/ical#","ical:"],
			["http://www.w3.org/2003/01/geo/wgs84_pos#","geo:"],
			["http://data-gov.tw.rpi.edu/2009/data-gov-twc.rdf#","dgtwc:"],
			["http://purl.org/ontology/bibo/", "bibo:"],
			["http://www.cs.vu.nl/~mcaklein/onto/swrc_ext/2005/05#","swc_ext:"],			
			["http://www.w3.org/2000/01/rdf-schema#","rdfs:"]
		]
		for entry in map_uri_qname:
			text = text.replace(entry[0], entry[1])
		return text

global_config= MyUtil.load_config()

list_raw_data =[
"iswc-2006-complete.rdf",
"iswc-aswc-2007-complete.rdf",
"iswc-2008-complete.rdf",
"iswc-2009-complete.rdf",
"iswc-2010-complete.rdf",
"iswc-2011-complete.rdf",
"iswc-2012-complete.rdf"
]

filename = {}
filename["combined"]= os.path.join(global_config['home'], 'local/final/combined.vocab.csv')
MyUtil.init_dir(filename["combined"])

with open(filename["combined"], 'wb') as f:
	writer = csv.writer(f)

	for raw_data in list_raw_data:
		print "processing ", raw_data, datetime.datetime.now()

		filename["data"] = os.path.join(global_config['home'], 'local/raw/data.semanticweb.org/dumps/conferences/', raw_data)
		filename["query"] = os.path.join(global_config['home'], 'data/query/iswc-vocab.sparql')
		filename["output"] = os.path.join(global_config['home'], 'local/output', raw_data + '.vocab.csv')

		#print filename
		MyUtil.init_dir(filename["output"])

		MyUtil.query_graph(filename["data"], filename["query"], filename["output"])
		
			
		with open(filename["output"],'rb') as f:
			reader = csv.reader(f)
			try:
				for row in reader:
					if not row[0].startswith('http://'):
						print "[SKIP ROW]", row
						continue
						
					for index in range(0, len(row)):
						row[index] = MyUtil.rewrite_uri2qname(row[index])
						
					conf_name = raw_data.replace("iswc-aswc", "iswc")[0:9]
					row.append(conf_name)
					writer.writerow(row)
			except csv.Error as e:
				sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))
			
