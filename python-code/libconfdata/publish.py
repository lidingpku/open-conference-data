'''
require
* installation of ARQ becuase rdflib does not support sparql 1.1.

functions
* rdf ==> csv-table(conference)
	- person(chair,pc,reviewer)
	- paper(track)
	- program(time/location grid)
	- proceedings
	- conference
* csv-table ==> json-table ([REF-1])
* json-table ==> rdf ([REF-2])
* json-table ==> json-conference
* json-conference ==> html+rdfa (proceedings, program) ([REF-3])


[REF-1]
title: syntax for json-table which offers parse/validation instructions
source: http://simile.mit.edu/wiki/Exhibit/Template/JSON_Data_File
source: http://json-schema.org/examples.html

csv-table to json-table
{
    "properties": {
        "title": {
            "type": "string"
        },
        "authors": {
            "type": "string-array",
            "delimiter": ","
        },
        "abstract": {
            "type": "string",
            "optional": true
        },
        "year": {
            "type": "integer"
        }
    },
    "items": [
        {
            "title": "paper 1",
            "authors": "John Doe, John Smith",
            "year": 2001
        },
        {
            "title": "paper 2",
            "authors": "Bob",
            "abstract": "This paper advances AI research.",
            "year": 2002
        }
    ]
}

[REF-2]
title:  simple mappings to create RDF out of json-table
source: use mapping instructions to deal with simple properties
source: use python to deal with complex properties
{
    "map2rdf": {
        "title": {
            "p":["RDFS.label", "DCTERMS.title"],
            "value-datatype": "XSD.string"
        },
        "authors": {
            "p":[SWRC.listAuthor],
            "value-datatype": "XSD.string"
        },
        "authors": {
            "p-seq":[BIBO.authorList],
            "p-member":[SWRC.hasAuthor, FOAF.maker],
            "p-member-inverse":[SWRC.isAuthorOf, FOAF.made],
            "value-class-named-entity": "FOAF.person"
        },
        "abstract": {
            "p":["SWRC.abstract"],
            "value-datatype": "XSD.string"
        },
        "eeOpenAccess": {
            "p":["SWRC.url"],
            "value-class-resource": "FOAF.Document"
        },
        "uri_proceedings": {
            "p":["SWRC.isPartOf"],
            "p-inverse":["SWRC.hasPart"],
            "value-class-resource": "SWRC.Proceedings"
        },
        "year": {
            "p":["SWRC.year"],
            "value-datatype": "XSD.integer"
        }
    }
}


[REF-3]
title: template for render html using json-conference
* source: https://pypi.python.org/pypi/jsontemplate/0.87

sample json-conference

{
    "proceedings": {
        "title": "Proceedings of ISWC'2012",
        "categories": [
            {
                "title": "Research Track",
                "papers": [
                    {
						"uri":"http://xyz-1",
                        "title": "paper 1",
                        "authors": "John Doe, John Smith",
						"url":"http://xyz-1.pdf",
                        "year": 2001
                    },
                    {
						"uri":"http://xyz-2",
                        "title": "paper 2",
                        "authors": "Bob",
                        "abstract": "This paper advances AI research.",
						"url":"http://xyz-2.pdf",
                        "year": 2002
                    }
                ]
            }
        ]
    },
    "conference": {
        "label": "11th International Semantic Web Conference",
        "acronym": "ISWC2012",
        "homepage": "http://iswc2012.semanticweb.org",
        "logo": "http://dig.csail.mit.edu/2012/ISWC2012-MentoringLunch/iswc_logo.png"
    }
}

'''

import jsontemplate
from pkg_resources import resource_string, resource_listdir
import rdflib
from rdflib import Namespace
from rdflib.query import Result, ResultSerializer, ResultParser
from rdflib import plugin
from io import UnicodeReader, UnicodeWriter
import codecs
import json
import datetime
import time

class UtilJson:
			
	@staticmethod
	def add_init_list(json_data, pre_keys, key, value, uniqe=False):
		temp = json_data
		for k in pre_keys:
			if not k in temp:
				temp[k] = {}
			temp = temp[k]

		if not key in temp:
			temp[key]=[]
			
		if uniqe and value in temp[key]:
			#skip duplicate insertion
			return 
			
		temp[key].append(value)

class ConfData(object):
	CONFIG={"arq":"/opt/apache-jena-2.10.1/bin/arq"}
	
	@staticmethod
	def rdfxml2ttl(filename_input, filename_output):
		graph = rdflib.Graph()
		graph.load(filename_input)
		with open(filename_output,"w") as f:
			content = graph.serialize(format='turtle') 
			f.write( content )
		

	@staticmethod
	def csv2html(id_data, global_config):
		#create json_conf data	
		json_conf ={}

		######################
		#conf-paper
		filename_csv_conf_paper = "%s/data/output/%s-%s.csv" % (
			global_config["home"], 
			id_data, 
			"conf-paper")
					
		indexed_proceedings ={}
		with open(filename_csv_conf_paper) as f:
			csvreader = UnicodeReader(f)
			headers =  csvreader.next()
			for row in csvreader:
				if len(row)<len(headers):
					#print "skipping row %s" % row 
					continue

				entry = dict(zip(headers, row))
				
#				print entry
				proceeding_title = "%s -- %s" % (entry["label_proceedings"], entry["subtitle_proceedings"])
				UtilJson.add_init_list(
					indexed_proceedings, 
					[proceeding_title],
					entry["category"],
					entry)
				
		
		#update json_conf
		for proceedings in sorted(indexed_proceedings.keys(), reverse=True):
			#print proceedings
			json_proceedings ={}
			json_proceedings["title"] =proceedings
			UtilJson.add_init_list(json_conf, [], "proceedings", json_proceedings)
			for category in sorted(indexed_proceedings[proceedings].keys()):
				#print category
				json_category = {}
				json_category["title"] =category
				UtilJson.add_init_list(json_proceedings, [], "categories", json_category)
				json_category["papers"] =indexed_proceedings[proceedings][category]
		
		######################
		#conf-person

		filename_csv_conf_paper = "%s/data/output/%s-%s.csv" % (
			global_config["home"], 
			id_data, 
			"conf-person")
					
		indexed_persons ={}
		with open(filename_csv_conf_paper) as f:
			csvreader = UnicodeReader(f)
			headers =  csvreader.next()
			for row in csvreader:
				if len(row)<len(headers):
					#print "skipping row %s" % row 
					continue

				entry = dict(zip(headers, row))
				
				#only keep direct conference role
				if entry["role_event_type"] != "http://data.semanticweb.org/ns/swc/ontology#ConferenceEvent":
					continue
				
				#print entry
				UtilJson.add_init_list(
					indexed_persons, 
					[entry["role_event_label"]],
					entry["role_label"],
					entry)
				
		#update json_conf
		for role_event_label in sorted(indexed_persons.keys()):
			#print role_event_label
			josn_role_event ={}
			josn_role_event["title"] =role_event_label
			UtilJson.add_init_list(json_conf, [], "events", josn_role_event)
			for role_label in sorted(indexed_persons[role_event_label].keys()):
				#print role_label
				json_role_label = {}
				json_role_label["title"] =role_label
				UtilJson.add_init_list(josn_role_event, [], "roles", json_role_label)
				json_role_label["persons"] =indexed_persons[role_event_label][role_label]
	
		
					

		######################
		# write xyz-proceedings
		filename_html_proceedings = "%s/data/output/%s-%s.html" % (
			global_config["home"], 
			id_data, 
			"proceedings")		
		
		json_template_program = resource_string('resources.files', 'proceedings.jsont')
		content= jsontemplate.expand(json_template_program, json_conf)
		with codecs.open(filename_html_proceedings,"w","utf-8") as f:
			f.write(u'\ufeff')
			f.write(content)
	
		######################
		#conf-event

		filename_csv_conf_event = "%s/data/output/%s-%s.csv" % (
			global_config["home"], 
			id_data, 
			"conf-event")
					
		indexed_events ={}
		dict_events ={}
		map_events ={}
		with open(filename_csv_conf_event) as f:
			csvreader = UnicodeReader(f)
			headers =  csvreader.next()
			for row in csvreader:
				if len(row)<len(headers):
					#print "skipping row %s" % row 
					continue

				entry = dict(zip(headers, row))
				
				#print entry
				
				dict_events[entry["event_uri"]]=entry
				
				UtilJson.add_init_list(
					map_events,
					[], 
					entry["super_event_uri"],
					entry["event_uri"],
					True)

				if len(entry['start'])>0:
					date = entry['start'][0:10]
					entry['start'] = entry['start'][11:-3]
					date_end =date
					if len(entry['end'])>0:
						date_end = entry['end'][0:10]
						entry['end'] = entry['end'][11:-3]
					#only keep same day events
					if date_end==date:
						UtilJson.add_init_list(
							indexed_events,
							[], 
							date,
							entry)
		#print json.dumps(map_events, indent=4)
			
		#update json_conf
		for date in sorted(indexed_events.keys()):
			josn_date_program ={}
			josn_date_program["title"] = datetime.datetime(*time.strptime(date,"%Y-%m-%d")[0:5]).strftime("%Y-%m-%d (%A)")
			UtilJson.add_init_list(json_conf, [], "program", josn_date_program)
			josn_date_program["events"] =indexed_events[date]
		
			for entry in indexed_events[date]:
				
				entry["super_event_type"] = dict_events[entry["super_event_uri"]]["event_type"]
				if entry["super_event_type"] == "http://data.semanticweb.org/ns/swc/ontology#TrackEvent":
					entry["track"] = dict_events[entry["super_event_uri"]]["label"]
				else:
					entry["track"] = ""
					
					
				if entry["event_type"] == "http://data.semanticweb.org/ns/swc/ontology#SessionEvent":
					if entry["event_uri"] in map_events:
						for sub_event_uri in map_events[entry["event_uri"]]:
							UtilJson.add_init_list(entry, [], "talks", dict_events[sub_event_uri])
 
		######################
		# write xyz-program
		filename_html_program = "%s/data/output/%s-%s.html" % (
			global_config["home"], 
			id_data, 
			"program")		
		
		json_template_program = resource_string('resources.files', 'program.jsont')
		content= jsontemplate.expand(json_template_program, json_conf)
		with codecs.open(filename_html_program,"w","utf-8") as f:
			f.write(u'\ufeff')
			f.write(content)	
	
	
	@staticmethod
	def json_conf2html(data_json_conf):
		'''http://stackoverflow.com/questions/1395593/managing-resources-in-a-python-project'''
		json_template_proceedings = resource_string('resources.files', 'proceedings.jsont')
		return jsontemplate.expand(json_template_proceedings, data_json_conf)
		
		
	@staticmethod
	def sparql_rdf2csv(graph, text_sparql):
		'''http://stackoverflow.com/questions/1395593/managing-resources-in-a-python-project'''
		#json_template_proceedings = resource_string('resources.files', 'proceedings.jsont')
		print len(graph)
		qres = graph.query(text_sparql)
		print len(qres)
		ret = []
		for row in qres:
			row_new = []
			for cell in row:
				row_new.append(cell)
			#print row_new
				
		return ret

	@staticmethod
	def sparql_rdf2csv(filename_rdf, filename_query, filename_output):
		from subprocess import call
		
		command= "{3} --data {0} --query {1} --results CSV > {2}".format(
			filename_rdf, 
			filename_query, 
			filename_output,
			ConfData.CONFIG["arq"])
		#print command
		call(command, shell=True)


###################################################################		
# load global config
global_config={
"home":"/home/dingli/dl/project/open-conference-data",
"created":"2013-05-24"
}

###################################################################		
# convert data from RDF/XML to ttl
list_data = [
	"iswc-2006","iswc-aswc-2007","iswc-2008",
	"iswc-2009","iswc-2010","iswc-2011","iswc-2012"
	]
for id_data in list_data:
	filename_input = "%s/data/iswc/%s-complete.rdf" % (global_config["home"], id_data)
	filename_output = "%s/data/iswc/%s-complete.ttl" % (global_config["home"], id_data)
	#one time job, uncomment it to re-run it
#	ConfData.rdfxml2ttl(filename_input,filename_output)

###################################################################		
# convert rdf(ttl) into csv and then html
list_data = ["swws-2001"
		,"iswc-2002"
		,"iswc-2003","iswc-2004","iswc-2005"		
		]
list_query = ["conf-person","conf-paper","conf-event"]
for id_data in list_data:
	for id_query in list_query:
		filename_rdf = "%s/data/iswc/%s-complete.ttl" % (global_config["home"], id_data)
		filename_query = "resources/files/%s.sparql" % (id_query)
		filename_output = "%s/data/output/%s-%s.csv" % (global_config["home"], id_data, id_query)
#		ConfData.sparql_rdf2csv(filename_rdf, filename_query, filename_output)
	
	ConfData.csv2html(id_data, global_config)
	
	
list_data = [
		"iswc-2006"
		#,"iswc-2006","iswc-aswc-2007","iswc-2008","iswc-2009","iswc-2010","iswc-2011"
		,"iswc-2012"
		]
list_query = ["conf-person","conf-paper","conf-event"]
for id_data in list_data:
	for id_query in list_query:
		filename_rdf = "%s/data/iswc/%s-complete.rdf" % (global_config["home"], id_data)
		filename_query = "resources/files/%s.sparql" % (id_query)
		filename_output = "%s/data/output/%s-%s.csv" % (global_config["home"], id_data, id_query)
#		ConfData.sparql_rdf2csv(filename_rdf, filename_query, filename_output)

