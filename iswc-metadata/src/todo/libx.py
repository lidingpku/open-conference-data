import csv, codecs, cStringIO
import requests
import urllib
import sys
import json
import rdflib

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self
        
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
        row = UtilSyntax.convert(row)
        self.writer.writerow(row)
        #self.writer.writerow([s.encode("utf-8") for s in row])
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

class MyCounterKeyValue:
	def __init__(self):
		self.data = {}
	
	def inc(self, key, value, ref):
		key = UtilSyntax.convert(key)
		value = UtilSyntax.convert(value)
		if not key in self.data:
			self.data[key]={}			
		if not value in self.data[key]:
			self.data[key][value]=set()
		self.data[key][value].add(ref)

	def show(self, min_value_count=0):
		total =0
		for k in self.data:
			v = self.data[k]
			if len(v) >= min_value_count:
				msg = ""
				for v in self.data[k]:
					msg +="{0}={1},".format(v, len(self.data[k][v]))
				msg = "{0}--[{1}]--[{2}]".format(k, len(self.data[k]), msg)
				print msg
				total +=1
		print "total {0} item with >={1} values".format(total, min_value_count)

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



class UtilString:
	# http://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
	@staticmethod	
	def levenshtein(seq1, seq2):
		oneago = None
		thisrow = range(1, len(seq2) + 1) + [0]
		for x in xrange(len(seq1)):
			twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
			for y in xrange(len(seq2)):
				delcost = oneago[y] + 1
				addcost = thisrow[y - 1] + 1
				subcost = oneago[y - 1] + (seq1[x] != seq2[y])
				thisrow[y] = min(delcost, addcost, subcost)
		return thisrow[len(seq2) - 1]

	@staticmethod
	def json2list(json_data, list_header):
		row = []
		for header in list_header:
			if header in json_data:
				value = json_data[header]
			else:
				value = ""
			row.append(value)
		return row
		

class UtilLinkDbpedia:
	LIST_HEADER = ["status","altLabel","title","uri","redirects","disambiguates"]
	
	@staticmethod
	def linkDbpedia(name, entity_type):
		name = UtilSyntax.convert(name)
		#print name
		basic ={"status":"auto","altLabel":name}

		wikipedia_data = UtilLinkDbpedia.searchWikipedia(name)
		#print json.dumps(wikipedia_data, indent=4)
		if len(wikipedia_data)==0:
			ret_data = dict(basic.items()+ wikipedia_data.items())	
			ret = UtilString.json2list(ret_data, UtilLinkDbpedia.LIST_HEADER)
			return ret
			
		name_new = wikipedia_data["title"]

		dbpedia_data= UtilLinkDbpedia.validateDbpedia(name_new)
		#print json.dumps(dbpedia_data, indent=4)
		if len(dbpedia_data)==0:
			ret_data = dict(basic.items()+ wikipedia_data.items())	
			ret = UtilString.json2list(ret_data, UtilLinkDbpedia.LIST_HEADER)
			return ret

		#create final data
		ret_data = dict(basic.items()+ wikipedia_data.items() + dbpedia_data.items())	
		ret_data["similarity"]= UtilString.levenshtein(name_new, name)
		
		uri = ret_data["uri"]
		if "redirects" in ret_data:
			ret_data["status"] = "auto-redirect"
		if "disambiguates" in ret_data:
			ret_data["status"] = "auto-disambiguates"
		ret = UtilString.json2list(ret_data, UtilLinkDbpedia.LIST_HEADER)		

		#print json.dumps(ret_data, indent=4)
		return ret
		
		
	@staticmethod
	def createDbpediaUrl(name):
		name = name.replace(" ","_")
		url = "http://dbpedia.org/resource/%s" % name
		return url


	@staticmethod
	def validateDbpedia(name):
		url = UtilLinkDbpedia.createDbpediaUrl(name)
		ret = UtilLinkDbpedia.retrieveDbpedia(url)
		if "redirects" in ret:
			return UtilLinkDbpedia.retrieveDbpedia(ret["redirects"])
		else:
			return ret
			
	@staticmethod
	def retrieveDbpedia(url):
		headers = {
			'Accept':'application/rdf+xml'}
		r = requests.get(url, headers=headers, allow_redirects=True)
		#print r.status_code
		#print r.url
		#print r.text
		
		g=rdflib.Graph()
		g.parse(data=r.text)
		qres = g.query(
			"""SELECT distinct ?uri ?label_en ?redirects ?disambiguates
			   WHERE {
				  ?uri rdfs:label ?label_en.
				  FILTER ( lang(?label_en) = "en" )
				  OPTIONAL {?uri <http://dbpedia.org/ontology/wikiPageRedirects> ?redirects}
				  OPTIONAL {?uri <http://dbpedia.org/ontology/wikiPageDisambiguates> ?disambiguates}
			   }""")

		ret = {}
		for row in qres:
			ret["uri"]=row[0].toPython()
			ret["label-en"]=row[1].toPython()
			ret["cnt-triple"]=len(g)
			if None!=row[2]:
				ret["redirects"]=row[2].toPython()		
			if None!=row[3]:
				ret["disambiguates"]=row[3].toPython()		
			
		#print len(g)
		return ret
		
	@staticmethod
	def searchWikipedia(name):
		'''
		http://stackoverflow.com/questions/5812800/wikipedia-search-results-different-for-api-opensearch-vs-normal-web-interface
		'''
		
		url_dict = {
		"action":"query",
		"list":"search",
		"srsearch":name,
		"srlimit":1,
		"srnamespace":0,
#		"srwhat":"title",
		"format":"json"
		}	
		r = requests.get("http://en.wikipedia.org/w/api.php",params=url_dict)
		#print r.url
		#print r.text
		if len(r.json()["query"]["search"])>0:
			return r.json()["query"]["search"][0]
		else:
			return {}
		
	@staticmethod
	def searchDbpedia(name, entity_type):
		url_dict = {
			"QueryClass":entity_type,
			"QueryString":name}		
		headers = {
			'Accept':'application/json'}
		r = requests.get(
			"http://lookup.dbpedia.org/api/search/KeywordSearch"
			,params=url_dict
			,headers=headers)
		
		json_data = r.json()
		#print r.url
		#print len(json_data["results"])
		ret =[]
		for entry in json_data["results"]:
			for key in ["classes","templates","categories"]:
				entry.pop(key, None)
			#print entry
			ret.append(entry)
		return ret
		
		
