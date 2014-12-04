import rdflib
from rdflib.namespace import RDF, FOAF, RDFS, OWL, DC, DCTERMS, SKOS
from rdflib import URIRef, Literal, Namespace, XSD
import json
from libx import UnicodeReader, UnicodeWriter, MyCounterKeyValue, UtilSyntax, MyCounter
import re
import os
import hashlib	
import json
import sys
import datetime

SWRC = Namespace('http://swrc.ontoware.org/ontology#')
SWC = Namespace('http://data.semanticweb.org/ns/swc/ontology#')
BIBO = Namespace('http://purl.org/ontology/bibo/')
ICAL = Namespace('http://www.w3.org/2002/12/cal/ical#')
DCTYPE = Namespace('http://purl.org/dc/dcmitype/')

VERSION_INFO = "iswc metadata 2001-2005 beta (2013-06-20) clean up categories"

class DataIswc:
	
	
	def __init__(self, local_config, global_config):
		self.graph = rdflib.Graph()
		self.graph.bind("foaf", FOAF)
		self.graph.bind("dc", DC)
		self.graph.bind("owl", OWL)
		self.graph.bind("swrc", SWRC)
		self.graph.bind("swc", SWC)
		self.graph.bind("bibo", BIBO)
		self.graph.bind("dcterms", DCTERMS)
		self.graph.bind("ical", ICAL)
		self.graph.bind("dctype", DCTYPE)
		
		self.local_config = local_config
		self.global_config = global_config
		self.map_name_res = {}
		self.map_name_name = {}

	def load_metadata(self):
		filename_manual= "{0}/data/entity/organisation.csv".format(self.global_config["home"])
		if os.path.exists(filename_manual):
			with open (filename_manual) as f:
				csvreader = UnicodeReader(f)
				headers =  csvreader.next()
				for row in csvreader:
					entry = dict(zip(headers, row))
					
					self.map_name_name[entry["altLabel"]] =	{
						"prefLabel":entry["title"],
						"dbpediaUri":entry["uri"]}

		print "{0} name mappings loaded".format(len(self.map_name_name))

	def run(self):
		self.load_metadata()
		self.process_organization()
		self.process_person()
		self.process_proceedings()
		self.process_paper()
		self.process_event()
		self.process_misc()
		filename_output = "{0}/data/final/{1}-complete.ttl".format(
			self.global_config["home"],
			self.local_config["tag"])
		with open(filename_output,"w") as f:
			content = self.graph.serialize(format='turtle') 
			f.write( content )
			

	NS_ROOT = "http://data.semanticweb.org/"
	PREFIX_ORG = "organization"
	PREFIX_PERSON = "person"
	
	PROP2URI ={
		#datatype property
		"label":{"p":[RDFS.label],"xsd":XSD.string},
		"hasAcronym":{"p":[SWC.acronym],"xsd":XSD.string},
		"acronym":{"p":[SWC.acronym],"xsd":XSD.string},
		"name":{"p":[RDFS.label,FOAF.name],"xsd":XSD.string},
		"title":{"p":[RDFS.label,DC.title, DCTERMS.title],"xsd":XSD.string},
		"abstract":{"p":[SWRC.abstract],"xsd":XSD.string},
		"hasAbstract":{"p":[SWRC.abstract],"xsd":XSD.string},
		"year":{"p":[SWRC.year],"xsd":XSD.string},
		"pages":{"p":[SWRC.pages],"xsd":XSD.string},
		"keywords":{"p":[SWRC.listKeyword],"xsd":XSD.string, "delimiter":","},
		"publisher":{"p":[SWRC.publisher],"xsd":XSD.string},
		"series":{"p":[SWRC.series],"xsd":XSD.string},
		"volume":{"p":[SWRC.volume],"xsd":XSD.string},
		"subtitle":{"p":[SWRC.subtitle],"xsd":XSD.string},
		"alt-name":{"p":[SKOS.altLabel],"xsd":XSD.string, "delimiter":","},
		"other-names":{"p":[SKOS.altLabel],"xsd":XSD.string, "delimiter":","},
		"dtStart":{"p":[ICAL.dtstart],"xsd":XSD.dateTime},
		"start":{"p":[ICAL.dtstart],"xsd":XSD.dateTime},
		"dtEnd":{"p":[ICAL.dtend],"xsd":XSD.dateTime},
		"end":{"p":[ICAL.dtend],"xsd":XSD.dateTime},
		"tzid":{"p":[ICAL.tzid],"xsd":XSD.string},
		"locationRoom":{"p":[SWC.hasLocation,SWC.room],"xsd":XSD.string},
		"room":{"p":[SWC.hasLocation,SWC.room],"xsd":XSD.string},
		"locationAddress":{"p":[SWC.hasLocation,SWC.address],"xsd":XSD.string},
		"address":{"p":[SWC.hasLocation,SWC.address],"xsd":XSD.string},
		"orderInSuperEvent":{"p":[SWC.orderInSession, SWC.order_in_super_event],"xsd":XSD.integer},
		"order_in_super_event":{"p":[SWC.orderInSession, SWC.order_in_super_event],"xsd":XSD.integer},
		"category":{"p":[SWRC.category],"xsd":XSD.string},
		
		#object property
		"link_open_access":{"p":[SWRC.url,SWRC.link_open_access]}, 
		"link_open_access":{"p":[SWRC.url,SWRC.link_open_access]}, 
		"link_publisher":{"p":[SWRC.url,SWRC.link_publisher]}, 
		"link_publisher":{"p":[SWRC.url,SWRC.link_publisher]}, 
		"linkDocument":{"p":[SWRC.url,SWRC.link_document]}, 
		"link_document":{"p":[SWRC.url,SWRC.link_document]}, 
		"depiction":{"p":[FOAF.depiction]}, 
		"logo":{"p":[FOAF.logo]}, 
		"homepage":{"p":[FOAF.homepage]}
	}
	
	def get_namespace(self, prefix):
		if DataIswc.PREFIX_ORG == prefix:
			return "{0}{1}/".format(DataIswc.NS_ROOT, prefix)
		elif DataIswc.PREFIX_PERSON == prefix:
			return "{0}{1}/".format(DataIswc.NS_ROOT, prefix)
		else:
			return DataIswc.NS_ROOT

	def expand_uri(self, uri):
		for key in self.local_config["prefix_ns_map"]:
			uri = uri.replace(key, self.local_config["prefix_ns_map"][key])
		return uri
		
	def create_named_entity(self, namespace, name):
		#remove extra white space around
		name = name.strip()
		
		#use canonical name
		dbpediaUri = ""
		if name in self.map_name_name:
			#print self.map_name_name[name]
			#key = UtilSyntax.convert(name)
			key=name
			name = self.map_name_name[key]["prefLabel"]
			dbpediaUri = self.map_name_name[key]["dbpediaUri"]				
		
		localname = DataIswc.create_localname(name)
		if localname in self.map_name_res:
			return self.map_name_res[localname]
		else:
			uri = "{0}{1}".format(namespace, localname)
			res_entity = URIRef(uri)
			self.create_triple_simple(res_entity, "name", name)
			
			self.map_name_res[localname] = res_entity
			if len(dbpediaUri)>0:
				self.graph.add( (res_entity, OWL.sameAs, URIRef(dbpediaUri)))
			
			if namespace == self.get_namespace(DataIswc.PREFIX_PERSON):
				self.graph.add( (res_entity, RDF.type, FOAF.Person))
			elif namespace == self.get_namespace(DataIswc.PREFIX_ORG):
				self.graph.add( (res_entity, RDF.type, FOAF.Organization))
				
			return res_entity
	
	@staticmethod
	def create_localname(name):
		name = name.encode('ascii', 'ignore')
		name = re.sub("[\.'\(\)\"]","", name)
		name = re.sub("[ /`]+","-", name)
		name = name.lower()
		return name
		
		
	def create_role_to_event(self, uri_event, role_type, role_label, res_entity):
		if len(uri_event)==0:
			return
		if len(role_type)==0:
			return
		if len(role_label)==0:
			return
		
		uri_event = self.expand_uri(uri_event)
		res_event = 	URIRef(uri_event)
		res_role_type = URIRef(self.expand_uri(role_type))
		uri_role = "%s/%s" %(uri_event, self.create_localname(role_label) )
		res_role = URIRef(uri_role)
		
		self.graph.add(	 (res_role, RDF.type, res_role_type) )
		self.graph.add(	 (res_role, RDFS.label, Literal(role_label)) )
		self.graph.add(	 (res_role, SWC.isRoleAt, res_event) )
		self.graph.add(	 (res_role, SWC.heldBy, res_entity) )
		self.graph.add(	 (res_event, SWC.hasRole,res_role ) )
		self.graph.add(	 (res_entity, SWC.holdsRole, res_role) )

	def create_triple_complex(self, res_subject, list_field, entry):
		for field in list_field:
			if field in entry:
				self.create_triple_simple(res_subject, field, entry[field])

	def create_triple_simple(self, res_subject, field, value):
		if len(value)==0:
			return
			
		for p in DataIswc.PROP2URI[field]["p"]:
			if "xsd" in DataIswc.PROP2URI[field]:
				if XSD.string == DataIswc.PROP2URI[field]["xsd"]:
					self.graph.add(	 (res_subject, p, Literal(value)))
				else:
					self.graph.add(	 (res_subject, p, Literal(value, datatype=DataIswc.PROP2URI[field]["xsd"])))
			else:
				self.graph.add(	 (res_subject, p, URIRef(value)))
		
	def process_misc(self):
		res_me = URIRef( self.expand_uri("[ME]") )
		res_data = URIRef( self.expand_uri("[ME]/complete") )
		self.graph.add((res_me, SWC.completeGraph, res_data ))
		self.graph.add((res_data, RDF.type, DCTYPE.Dataset ))
		self.graph.add((res_data, DCTERMS.hasVersion, Literal(VERSION_INFO)))
		self.graph.add((res_data, RDFS.comment, Literal("This dataset is created by Li Ding http://liding.org. To learn more about this dataset, go to https://github.com/lidingpku/open-conference-data/tree/master/data/iswc ")))
		self.graph.add((res_data, DCTERMS.modified, Literal(datetime.datetime.now().isoformat(), datatype=XSD.datetime)))
		self.graph.add((res_data, DCTERMS.creator, Literal("Li Ding")))
				
	def process_organization(self):	
		filename = "{0}/data/manual/{1}-organization.csv".format(
			self.global_config["home"],
			self.local_config["tag"])
			
		with open(filename) as f:
			csvreader = UnicodeReader(f)
			headers =  csvreader.next()
			for row in csvreader:
				if len(row)<len(headers):
					#print "skipping row %s" % row 
					continue

				entry = dict(zip(headers, row))

				if len(entry["name"])==0:
					#print "skipping empty name row %s" % entry
					continue

				res_organization = self.create_named_entity(self.get_namespace(DataIswc.PREFIX_ORG), entry["name"])
				
				#object properties
				self.create_triple_complex(res_organization, ["homepage","logo"], entry)
				
				#role
				self.create_role_to_event(
					entry["role_event"],
					entry["role_type"], 
					entry["role_label"],
					res_organization )
				
				
	def process_person(self):
		filename = "{0}/data/manual/{1}-person.csv".format(
			self.global_config["home"],
			self.local_config["tag"])
			
		with open(filename) as f:
			csvreader = UnicodeReader(f)
			headers =  csvreader.next()
			for row in csvreader:
								
				if len(row)!=len(headers):
					#print "skipping mismatch row %s" % row 
					continue
				
				entry = dict(zip(headers, row))

				if len(entry["name"])==0:
					#print "skipping empty name row %s" % entry
					continue
					
					
				res_person = self.create_named_entity(
					self.get_namespace(DataIswc.PREFIX_PERSON), 
					entry["name"])
				
				#object properties
				self.create_triple_complex(res_person, ["homepage"], entry)
				
				#role
				self.create_role_to_event(
					entry["role_event"],
					entry["role_type"], 
					entry["role_label"],
					res_person )
				
				#organization
				if "organization" in entry:
					for org in entry["organization"].split(";"):
						if len(org)==0:
							continue
							
						res_organization = self.create_named_entity(self.get_namespace(DataIswc.PREFIX_ORG), org)
						self.graph.add( (res_organization, FOAF.member, res_person) )
						#inverse property
						self.graph.add( (res_person, SWRC.affiliation, res_organization) )

				#alt-name
				self.create_triple_complex(res_person, ["alt-name"], entry)
				
				#email
				if len(entry["email"])>0:
					if not entry["email"].startswith("mailto:"):
						mbox = "mailto:%s" % entry["email"]
					else:
						mbox = entry["email"]
					
					mbox_sha1sum =  hashlib.sha1(mbox).hexdigest()
					#self.graph.add( (res_person, FOAF.mbox, URIRef(mbox)) )
					self.graph.add( (res_person, FOAF.mbox_sha1sum, Literal(mbox_sha1sum)) )
		

	def process_event(self):
		filename = "{0}/data/manual/{1}-event.csv".format(
			self.global_config["home"],
			self.local_config["tag"])
			
		counter_event = MyCounter()
		
		with open(filename) as f:
			csvreader = UnicodeReader(f)
			headers =  csvreader.next()
			for row in csvreader:
								
				if len(row)!=len(headers):
					#print "skipping mismatch row %s" % row 
					continue
				
				entry = dict(zip(headers, row))

				if len(entry["label"])==0:
					#print "skipping empty label row %s" % entry
					continue
					
				if len(entry["event_type"])==0:
					#print "skipping empty event_type row %s" % entry
					continue

				if entry["event_uri"].startswith("#"):
					#print "skipping empty commented row %s" % entry
					continue

				#set default super event
				if len(entry["super_event_uri"])==0:
					entry["super_event_uri"] = "[ME]"
					
				uri_super_event =self.expand_uri(entry["super_event_uri"])
				res_super_event = URIRef(uri_super_event)
					
				if len(entry["event_uri"])==0:
					counter_event.inc(uri_super_event)
					entry["event_uri"] = "%s/event-%02d" % (
						uri_super_event,
						counter_event.data[uri_super_event])
						
				uri_event =self.expand_uri(entry["event_uri"])
				res_event = URIRef(uri_event)
				
				#event type
				self.graph.add( (res_event, RDF.type, SWC[entry["event_type"]]))
				
				#super event
				self.graph.add( (res_event, SWC.isSubEventOf, res_super_event))
				self.graph.add( (res_super_event, SWC.isSuperEventOf, res_event))
		
				#simple properties
				self.create_triple_complex(
					res_event, 
					["label","acronym", "abstract",
					 "order_in_super_event",
					 "start", "end", "tzid",
					 "room","address",
					 "homepage", "link_document", "logo"],
					entry)
				
				#linking paper event
				if "TalkEvent" == entry["event_type"]:
					if entry["label"] in self.map_name_res:
						res_paper = self.map_name_res[entry["label"]]
						self.graph.add( ( res_event, SWC.hasRelatedDocument, res_paper))
						self.graph.add( ( res_paper, SWC.relatedToEvent, res_event))
					else:
						print "missing paper link "+entry["label"]
						sys.exit(0)
					
				#role -chair
				for role in ["Chair","Presenter"]:
					role_lower = role.lower()
					if len(entry[role_lower+"_person"])>0:
						for name in entry[role_lower+"_person"].split(","):
							if len(name)==0:
								continue;
							
							res_person = self.create_named_entity(
								self.get_namespace(DataIswc.PREFIX_PERSON),
								name)
								
							self.create_role_to_event(
								uri_event,
								"swc:"+role, 
								entry[role_lower+"_label"],
								res_person )


	def create_container(self,elements,contType,uri_subject=None) :
		'''http://dev.w3.org/2004/PythonLib-IH/NewRDFLib/rdflib/Graph.py'''
		if None==uri_subject:
			container = BNode()
		else:
			container = URIRef(uri_subject)
			
		self.graph.add((container,RDF.type,contType))
		for i in range(0,len(elements)) :
			uri_pred = "%s_%d" % (RDF,i+1) 
			pred = URIRef(uri_pred)
			self.graph.add( (container,pred,elements[i]) )
		return container


	def process_paper(self):
#		filename = "{0}/data/manual/full_iswc_paper_pdf.csv".format(
		filename = "{0}/data/manual/iswc-publication-paper.csv".format(
			self.global_config["home"])
			
		counter_paper = MyCounter()
		with open(filename) as f:
			csvreader = UnicodeReader(f)
			headers =  csvreader.next()
			for row in csvreader:
								
				if len(row)!=len(headers):
					#print "skipping mismatch row %s" % row 
					continue
				
				entry = dict(zip(headers, row))

				if entry["year"]!= self.local_config["year"]:
					#skip mismatched year
					continue

				if len(entry["title"])==0:
					print "skipping empty title row %s" % entry
					continue
					
				if len(entry["proceedings_uri"])==0:	
					print "skipping empty proceedings row %s" % entry
					continue
				
				counter_paper.inc(entry["proceedings_uri"])
				id_paper = counter_paper.data[entry["proceedings_uri"]]
				uri_paper = "%s/paper-%02d" % (entry["proceedings_uri"], id_paper) 
				uri_paper_author_list = "%s/paper-%02d/author_list" % (entry["proceedings_uri"], id_paper) 
				#print json.dumps(entry, indent=4)
				#print uri_paper
				res_proceedings = URIRef(entry["proceedings_uri"])
				res_paper = URIRef(uri_paper)
				
				self.graph.add( (res_paper, RDF.type, SWRC.InProceedings ) )

				#part-of proceedings
				self.graph.add( (res_paper, SWC.isPartOf, res_proceedings) )
				self.graph.add( (res_proceedings, SWC.hasPart, res_paper) )				
				
				#author
				self.graph.add( (res_paper, SWRC.listAuthor, Literal(entry["author"])) )
				list_res_author = []
				for author in entry["author"].split(","):
					res_author = self.create_named_entity(
						self.get_namespace(DataIswc.PREFIX_PERSON), 
						author)
					self.graph.add( (res_author, RDF.type, FOAF.Person) )
					
					list_res_author.append(res_author)
					self.graph.add( (res_paper, SWRC.author, res_author) )
					self.graph.add( (res_paper, FOAF.maker, res_author) )
					self.graph.add( (res_author, FOAF.made, res_paper) )
				
				res_paper_author_list = self.create_container(list_res_author, RDF.Seq, uri_paper_author_list)
				self.graph.add( (res_paper, BIBO.authorList, res_paper_author_list) )
				
				#simple properties
				self.create_triple_complex(
					res_paper, 
					["abstract", "keywords", "year", "pages", "title", "category",
					 "link_open_access", "link_publisher"],
					entry)
				
				#cache
				self.map_name_res[entry["title"]] = res_paper

				

	def process_proceedings(self):
#		filename = "{0}/data/manual/full_iswc_proceedings.csv".format(
		filename = "{0}/data/manual/iswc-publication-proceedings.csv".format(
			self.global_config["home"])
			
		counter_paper = MyCounter()
		with open(filename) as f:
			csvreader = UnicodeReader(f)
			headers =  csvreader.next()
			for row in csvreader:
								
				if len(row)!=len(headers):
					print "skipping mismatch row %s" % row 
					continue
				
				entry = dict(zip(headers, row))

				if entry["year"]!= self.local_config["year"]:
					#skip mismatched year
					continue

				if len(entry["title"])==0:
					print "skipping empty title row %s" % entry
					continue
					
				if len(entry["proceedings_uri"])==0:	
					print "skipping empty proceedings_uri row %s" % entry
					continue
				
				uri_proceedings = self.expand_uri(entry["proceedings_uri"])
				uri_proceedings_editor_list = "%s/editor_list" % (uri_proceedings) 
				uri_event = self.expand_uri(entry["event_uri"])

				#print json.dumps(entry, indent=4)
				#print uri_proceedings
				res_proceedings = URIRef(uri_proceedings)
				res_event = URIRef(uri_event)
				
				self.graph.add( (res_proceedings, RDF.type, SWRC.Proceedings ) )

				#relation to event
				self.graph.add( (res_proceedings, SWC.relatedToEvent, res_event) )
				self.graph.add( (res_event, SWRC.hasRelatedDocument, res_proceedings) )				
				
				#editor
				if len(entry["editor"])>0:
					self.graph.add( (res_proceedings, SWRC.listEditor, Literal(entry["editor"])) )
					list_res_editor = []
					for editor in entry["editor"].split(","):
						res_editor = self.create_named_entity(
							self.get_namespace(DataIswc.PREFIX_PERSON), 
							editor)
						list_res_editor.append(res_editor)
						self.graph.add( (res_proceedings, SWRC.editor, res_editor) )
						self.graph.add( (res_proceedings, FOAF.maker, res_editor) )
						self.graph.add( (res_editor, FOAF.made, res_proceedings) )
					
					res_proceedings_editor_list = self.create_container(list_res_editor, RDF.Seq, uri_proceedings_editor_list)
					self.graph.add( (res_proceedings, SWC.editorList, res_proceedings_editor_list) )
				
				
				#simple properties
				self.create_triple_complex(
					res_proceedings, 
					["title", "subtitle","abstract", "keywords", "year", "pages", "publisher","series", "volume",
					 "link_open_access", "link_publisher", "depiction"],
					entry)				
			
						
# load config file
with open("config.json") as f:
	global_config = json.load( f)



list_local_config = [
{	"year":"2001", 
	"tag":"swws-2001", 
	"prefix_ns_map":{
		"[ISWC]": "{0}conference/iswc".format(DataIswc.NS_ROOT),
		"[ME]": "{0}conference/swws/2001".format(DataIswc.NS_ROOT),
		"swc:": "http://data.semanticweb.org/ns/swc/ontology#"
	}
},
{	"year":"2002", 
	"tag":"iswc-2002", 
	"prefix_ns_map":{
		"[ISWC]": "{0}conference/iswc".format(DataIswc.NS_ROOT),
		"[ME]": "{0}conference/iswc/2002".format(DataIswc.NS_ROOT),
		"swc:": "http://data.semanticweb.org/ns/swc/ontology#"
	}
},
{	"year":"2003", 
	"tag":"iswc-2003", 
	"prefix_ns_map":{
		"[ISWC]": "{0}conference/iswc".format(DataIswc.NS_ROOT),
		"[ME]": "{0}conference/iswc/2003".format(DataIswc.NS_ROOT),
		"swc:": "http://data.semanticweb.org/ns/swc/ontology#"
	}
},
{	"year":"2004", 
	"tag":"iswc-2004", 
	"prefix_ns_map":{
		"[ISWC]": "{0}conference/iswc".format(DataIswc.NS_ROOT),
		"[ME]": "{0}conference/iswc/2004".format(DataIswc.NS_ROOT),
		"swc:": "http://data.semanticweb.org/ns/swc/ontology#"
	}
},
{	"year":"2005", 
	"tag":"iswc-2005", 
	"prefix_ns_map":{
		"[ISWC]": "{0}conference/iswc".format(DataIswc.NS_ROOT),
		"[ME]": "{0}conference/iswc/2005".format(DataIswc.NS_ROOT),
		"swc:": "http://data.semanticweb.org/ns/swc/ontology#"
	}
},
{	"year":"2013", 
	"tag":"iswc-2013", 
	"prefix_ns_map":{
		"[ISWC]": "{0}conference/iswc".format(DataIswc.NS_ROOT),
		"[WORKSHOP]": "{0}workshop".format(DataIswc.NS_ROOT),
		"[ME]": "{0}conference/iswc/2013".format(DataIswc.NS_ROOT),
		"swc:": "http://data.semanticweb.org/ns/swc/ontology#"
	}
}
]

for local_config in list_local_config:
#	if local_config["year"] =="2013":
	
		print local_config
		data = DataIswc(local_config, global_config)
		data.run()
