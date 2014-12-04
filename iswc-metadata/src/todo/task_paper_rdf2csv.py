'''
http://stackoverflow.com/questions/4702518/how-to-access-members-of-an-rdf-list-with-rdflib-or-plain-sparql
'''
import rdflib
import json
import os
import csv, codecs, cStringIO


class UtilSyntax:
	@staticmethod
	def convert(input):
		if isinstance(input, dict):
			return {UtilSyntax.convert(key): UtilSyntax.convert(value) for key, value in input.iteritems()}
		elif isinstance(input, list):
			return [UtilSyntax.convert(element) for element in input]
		elif isinstance(input, unicode):
			return input.encode('utf-8')
		else:
			return input    

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
  
  
class IswcMetadataParser:

	@staticmethod
	def paper_rdf2csv(uri_data, csvwriter=None):
		#declar namespace
		RDF = rdflib.namespace.RDF
		RDFS = rdflib.namespace.RDFS
		BIB = rdflib.Namespace("http://purl.org/net/biblio#")
		FOAF = rdflib.Namespace("http://xmlns.com/foaf/0.1/")
		SWRC_EXT = rdflib.Namespace("http://www.cs.vu.nl/~mcaklein/onto/swrc_ext/2005/05#")
		SWRC = rdflib.Namespace("http://swrc.ontoware.org/ontology#")
		SWC = rdflib.Namespace("http://data.semanticweb.org/ns/swc/ontology#")
		DC = rdflib.Namespace("http://purl.org/dc/elements/1.1/")
		DCTERMS = rdflib.Namespace("http://purl.org/dc/terms/")
		BIBO = rdflib.Namespace("http://purl.org/ontology/bibo/")
		
		#Parse the file
		g = rdflib.Graph()
		g.parse(uri_data)

		#So that we are sure we get something back
		print "{0} triples in {1}".format(len(g),uri_data)
		#print g.serialize(format='n3')


		#Article for wich we want the list of authors
		#article = rdflib.term.URIRef(uri_paper)

		list_paper = []
		for s, p, o in g.triples((None,RDF['type'], SWRC["InProceedings"])):
			#print s
			list_paper.append(s)
		
		list_paper.sort()

		for paper in list_paper:
			json_data = {}
			json_data["paper_uri"]= paper.__str__()
			json_data["source_uri"]= uri_data
			json_data["uri_me"]= uri_data.replace("/complete","")
					
			for year in ["2006","2007","2008","2009","2010","2011","2012"]:
				if uri_data.find(year)>0:
					json_data["year"]= year
					break
				
			#First loop filters is equivalent to "get all authors for article x" 
			list_author= []
			for triple in g.triples((paper,SWRC_EXT["authorList"],None)):

				#This expresions removes the rdf:type predicate cause we only want the bnodes
				# of the form http://www.w3.org/1999/02/22-rdf-syntax-ns#_SEQ_NUMBER
				# where SEQ_NUMBER is the index of the element in the rdf:Seq
				list_triples = filter(lambda y: RDF['type'] != y[1], g.triples((triple[2],None,None)))

				#We sort the authors by the predicate of the triple - order in sequences do matter ;-)
				# so "http://www.w3.org/1999/02/22-rdf-syntax-ns#_435"[44:] returns 435
				# and since we want numberic order we do int(x[1][44:]) - (BTW x[1] is the predicate)
				authors_sorted =  sorted(list_triples,key=lambda x: int(x[1][44:]))

				#We iterate the authors bNodes and we get surname and givenname
				for author_bnode in authors_sorted:
					for y in g.triples((author_bnode[2],FOAF['name'],None)):
						author_name = y[2]
					#print "author(%s): %s"%(i,author_name)
					list_author.append(author_name)

			for triple in g.triples((paper,BIBO["authorList"],None)):

				#This expresions removes the rdf:type predicate cause we only want the bnodes
				# of the form http://www.w3.org/1999/02/22-rdf-syntax-ns#_SEQ_NUMBER
				# where SEQ_NUMBER is the index of the element in the rdf:Seq
				list_triples = filter(lambda y: RDF['type'] != y[1], g.triples((triple[2],None,None)))

				#We sort the authors by the predicate of the triple - order in sequences do matter ;-)
				# so "http://www.w3.org/1999/02/22-rdf-syntax-ns#_435"[44:] returns 435
				# and since we want numberic order we do int(x[1][44:]) - (BTW x[1] is the predicate)
				authors_sorted =  sorted(list_triples,key=lambda x: int(x[1][44:]))

				#We iterate the authors bNodes and we get surname and givenname
				for author_bnode in authors_sorted:
					for y in g.triples((author_bnode[2],FOAF['name'],None)):
						author_name = y[2]
					#print "author(%s): %s"%(i,author_name)
					list_author.append(author_name)
					
			json_data["authors"] = ",".join(list_author)

			#paper title
			for triple in g.triples((paper,RDFS["label"],None)):
				json_data["title"] = triple[2].value
				
			#proceedings
			for triple in g.triples((paper, SWC["isPartOf"],None)):
				json_data["proceedings_uri"] = triple[2].__str__()
				
			#abstract
			for triple in g.triples((paper, SWC["hasAbstract"],None)):
				json_data["abstract"] = triple[2].value

			for triple in g.triples((paper, SWRC["abstract"],None)):
				json_data["abstract"] = triple[2].value

			#pages
			for triple in g.triples((paper, SWRC["pages"],None)):
				json_data["pages"] = triple[2].value
				
			#pdf
			for triple in g.triples((paper, SWRC["url"],None)):
				eeOpenAccess = triple[2].__str__()
				if eeOpenAccess.endswith(".pdf"):
					json_data["eeOpenAccess"] = eeOpenAccess
				
			#keywords
			keywords = set()
			for triple in g.triples((paper, DC["subject"],None)):
				keywords.add(triple[2].value)
			for triple in g.triples((paper, DCTERMS["subject"],None)):
				keywords.add(triple[2].value)
			for triple in g.triples((paper, SWC["hasTopic"],None)):
				for topic in g.triples((triple[2], RDFS["label"],None)):
					keywords.add(topic[2].value)
#			print keywords
			list_keywords = list(keywords)
			list_keywords.sort()
#			print list_keywords
			json_data["keywords"] = ",".join(UtilSyntax.convert(list_keywords))
			print json_data["keywords"]
			
			#print json_data
			
			LIST_HEADER = [
			"authors", "title", "pages", "year", 
			"eeOpenAccess",	"eePublisher", 
			"proceedings_uri","paper_uri", 	"source_uri", 
			"keywords","abstract", "uri_me"]
			row =[]
			for header in LIST_HEADER:
				text = ""
				if header in json_data:
					text = json_data[header]
					text = text.replace("\n"," ")					
				row.append(text)

			# make sure all paper has title, iswc 2011 has some paper without title
			if not "title" in json_data:
				continue
					
			if None!=csvwriter:
				csvwriter.writerow(row)
			else:
				print UtilSyntax.convert(row)


# load config file
with open("config.json") as f:
	global_config = json.load( f)

params ={}
params["filename_csv_output"]= os.path.join(global_config['home'], 'data/raw/swrc_paper_pdf_2006_2012_by_python.csv')

list_data = [
'http://data.semanticweb.org/conference/iswc/2006/complete',
'http://data.semanticweb.org/conference/iswc-aswc/2007/complete',
'http://data.semanticweb.org/conference/iswc/2008/complete',
'http://data.semanticweb.org/conference/iswc/2009/complete',
'http://data.semanticweb.org/conference/iswc/2010/complete',
'http://data.semanticweb.org/conference/iswc/2011/complete',
'http://data.semanticweb.org/conference/iswc/2012/complete',
]

with open(params["filename_csv_output"],'w') as f_output:
	csvwriter = UnicodeWriter(f_output)
	for uri_data in list_data:
		IswcMetadataParser.paper_rdf2csv(uri_data, csvwriter)
