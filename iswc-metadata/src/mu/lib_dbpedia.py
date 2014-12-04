from lib_unicode import *
import os
import re
import requests
import rdflib
import simplejson as json
from lib_format import *
import copy


class DbpediaApi(object):
    # http://dbpedia.org/Ontology
    ENTITY_TYPE_ORGANIZATION = "organisation"
    ENTITY_TYPE_PERSON = "person"
    ENTITY_TYPE_PLACE = "place"

    LIST_HEADER = ["altLabel", "title", "subtitle", "uri", "source", "status", "redirects", "disambiguates",
                   "matched_entity_type", "row_type"]

    def __init__(self, dir_data, entity_type):
        # init config
        self.config = {
            "entity_type": entity_type,
            "fn_data": "%s/%s.csv" % (dir_data, entity_type),
            "fn_new": "%s/%s.new.csv" % (dir_data, entity_type),
        }

        #init map_name
        self.map_name = {}
        self.map_name_pre = {}

        if os.path.exists(self.config["fn_data"]):
            #load data
            with open(self.config["fn_data"], 'r') as f:
                csvreader = UnicodeReader(f)
                headers = csvreader.next()
                for row in csvreader:
                    #print row
                    entry = dict(zip(headers, row))

                    altLabel = entry["altLabel"]
                    prefLabel = entry["title"]

                    self.map_name[prefLabel] = entry
                    if len(prefLabel) > 0:
                        self.map_name[altLabel] = entry
        else:
            #create the first version of data file with header row
            with open(self.config["fn_data"], 'w') as f:
                csvwriter = UnicodeWriter(f)
                headers = DbpediaApi.LIST_HEADER
                csvwriter.writerow(headers)

        #init new row
        self.list_new_entity = []

        self.detect_cycle()

    def detect_cycle(self):
        for name in self.map_name:
            entry = self.map_name[name]
            if name == entry['title']:
                continue

            self.__detect_cycle(name, [])

    def __detect_cycle(self, cur, visited):
        if cur in visited:
            raise RuntimeError("encounter cycle cur=[{}], visited=[{}]".format(cur, visited))
        else:
            if cur in self.map_name:
                entry = self.map_name[cur]
                if cur != entry['title']:
                    visited_new = copy.deepcopy(visited)
                    visited_new.append(cur)
                    self.__detect_cycle(entry['title'], visited_new)


    def write_new_data(self, filemode="w"):
        headers = DbpediaApi.LIST_HEADER

        print "{0} new mapping entries added ".format(len(self.list_new_entity))

        #start the new data file, to be merged to original data
        with open(self.config["fn_new"], filemode) as f:
            csvwriter = UnicodeWriter(f)
            for entry in self.list_new_entity:
                row = UtilString.json2list(entry, headers)
                csvwriter.writerow(row)

    def find_cached_name(self, name):
        #preprocess and skip invalid cases
        if None == name:
            return None
        name = name.strip()
        if len(name) == 0:
            return None

        #check if name already exists
        if name in self.map_name:
            return self.map_name[name]
        else:
            return None


    def process_names(self, names):
        names = names.strip()

        #recursively find the matching names
        entry = self.find_cached_name(names)
        if entry:
            if names != entry['title']:
                return self.process_names(entry['title'])

        #no further mapping

        #break names into a list
        temp = names
        #        if len(temp)>10:
        #            temp =re.sub("\\s+and\\s+", ";", temp)
        #            temp =re.sub("\\s+&\\s+", ";", temp)
        list_name = temp.split(";")
        if len(list_name) > 1:
            print "{} ==> {}".format(names, list_name)

        #process individual names
        ret = {}
        for name in list_name:
            name = name.strip()
            if len(name) == 0:
                continue
            ret[name] = self.process_one_name(name)
        return ret

    def process_one_name(self, name):
        name = name.strip()

        #recursively find the matching names
        entry = self.find_cached_name(name)
        if entry:
            if name != entry['title']:
                return self.process_one_name(entry['title'])
            else:
                return entry

        #the name does not exist    

        #try to link it 
        entry = DbpediaApi.link_dbpedia(name, self.config["entity_type"])

        #cache
        self.map_name[name] = entry
        self.list_new_entity.append(entry)
        #print cnt_row

        #            csvwriter.writerow(row)
        #            print "\t".join(UtilSyntax.convert(row))

        return entry

    @staticmethod
    def is_entry_skip(entry):
        if None == entry:
            return False
        if not "status" in entry:
            return False
        return entry["status"].startswith("skip")


    @staticmethod
    def is_entry_auto(entry):
        if None == entry:
            return False
        if not "status" in entry:
            return False
        return entry["status"].startswith("auto")


    @staticmethod
    def link_dbpedia(name, entity_type):
        name = any2utf8(name)
        #print name
        basic = {"status": "auto-fail", "altLabel": name}

        wikipedia_data = DbpediaApi.search_wikipedia(name, entity_type)
        #print json.dumps(wikipedia_data, indent=4)

        ret_data = dict(basic.items() + wikipedia_data.items())

        if len(wikipedia_data) == 0:
            ret_data["title"] = name
            ret_data["status"] = "auto-fail-outside-wikipedia"
            return ret_data

        name_title = wikipedia_data["title"]
        name_title = any2utf8(name_title)
        ret_data["similarity"] = UtilString.levenshtein(name_title, name)

        if "uri" in ret_data:
            uri = ret_data["uri"]
            ret_data["status"] = "auto"

        if "redirects" in ret_data:
            ret_data["status"] = "auto-redirect"
        elif "disambiguates" in ret_data:
            ret_data["status"] = "auto-disambiguates"

        #print json.dumps(ret_data, indent=4)
        return ret_data


    @staticmethod
    def create_dbpedia_url(name):
        name = name.replace(" ", "_")
        url = "http://dbpedia.org/resource/%s" % name
        return url


    @staticmethod
    def retrieve_dbpedia_by_name(name):
        url = DbpediaApi.create_dbpedia_url(name)
        ret = DbpediaApi.retrieve_dbpedia(url)

        #recursively follow redirects
        if "redirects" in ret:
            ret = DbpediaApi.retrieve_dbpedia(ret["redirects"])

        return ret

    '''
<?xml version="1.0" encoding="utf-8" ?>
<rdf:RDF
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:owl="http://www.w3.org/2002/07/owl#"
    xmlns:dbpedia-owl="http://dbpedia.org/ontology/"
    xmlns:foaf="http://xmlns.com/foaf/0.1/"
    xmlns:ns5="http://www.w3.org/ns/prov#" >
  <rdf:Description rdf:about="http://en.wikipedia.org/wiki/Centre_national_de_la_recherche_scientifique">
    <foaf:primaryTopic rdf:resource="http://dbpedia.org/resource/Centre_national_de_la_recherche_scientifique" />
  </rdf:Description>
  <rdf:Description rdf:about="http://dbpedia.org/resource/Centre_national_de_la_recherche_scientifique">
    <owl:sameAs rdf:resource="http://dbpedia.org/resource/Centre_national_de_la_recherche_scientifique" />
    <dbpedia-owl:wikiPageRedirects rdf:resource="http://dbpedia.org/resource/French_National_Centre_for_Scientific_Research" />
    <foaf:isPrimaryTopicOf rdf:resource="http://en.wikipedia.org/wiki/Centre_national_de_la_recherche_scientifique" />
    <ns5:wasDerivedFrom rdf:resource="http://en.wikipedia.org/wiki/Centre_national_de_la_recherche_scientifique?oldid=225929208" />
  </rdf:Description>
</rdf:RDF>%
'''

    @staticmethod
    def retrieve_dbpedia(url):
        headers = {
            'Accept': 'application/rdf+xml'}
        r = requests.get(url, headers=headers, allow_redirects=True)
        #print r.status_code
        #print r.url
        #print r.text

        g = rdflib.Graph()
        g.parse(data=r.text)
        qres = g.query(
            """SELECT distinct ?uri ?label_en ?redirects ?disambiguates
               WHERE {
                  ?wiki <http://xmlns.com/foaf/0.1/primaryTopic> ?uri.
                  OPTIONAL {
                    ?uri rdfs:label ?label_en.
                    FILTER ( lang(?label_en) = "en" )
                  }
                  OPTIONAL {?uri <http://dbpedia.org/ontology/wikiPageRedirects> ?redirects}
                  OPTIONAL {?uri <http://dbpedia.org/ontology/wikiPageDisambiguates> ?disambiguates}
               }""")

        ret = {}

        #print "retrieve_dbpedia [{}]".format(url)

        dbpedia_data = {}
        for row in qres:
            dbpedia_data["uri"] = row[0].toPython()

            if None != row[1] and len(row[1]) > 0:
                dbpedia_data["dbpedia-label-en"] = row[1].toPython()
            if None != row[2] and len(row[2]) > 0:
                dbpedia_data["dbpedia-redirect-from"] = row[0].toPython()
                dbpedia_data["uri"] = row[2].toPython()
            if None != row[3] and len(row[3]) > 0:
                dbpedia_data["dbpedia-disambiguates"] = row[3].toPython()
        if len(dbpedia_data) > 1:
            ret = dbpedia_data

        ret["dbpedia-count-res"] = len(qres)
        ret["dbpedia-url"] = url
        ret["dbpedia-count-triple"] = len(g)

        # get all types' uri
        query = "SELECT distinct ?type WHERE { ?s a ?type  }"
        #print query
        qres = g.query(query)

        ret["types"] = []
        for row in qres:
            ret["types"].append(row[0].toPython())

        #for s,p,o in g: 
        #  print s,p,o

        #print ret
        return ret

    @staticmethod
    def match_entity_type(entity_type, list_of_types):
        for type in list_of_types:
            type = type.lower()
            if type.endswith(entity_type):
                return True
        return False

    @staticmethod
    def search_wikipedia(name, entity_type=None):
        '''
        get the first search result from wikipedia
        
        http://stackoverflow.com/questions/5812800/wikipedia-search-results-different-for-api-opensearch-vs-normal-web-interface
        '''

        url_dict = {
            "action": "query",
            "list": "search",
            "srsearch": name,
            "srlimit": 3,
            "srnamespace": 0,
            #        "srwhat":"title",
            "format": "json"
        }
        print "search wikipedia [{}]".format(name)

        r = requests.get("http://en.wikipedia.org/w/api.php", params=url_dict)
        #print r.url
        #print r.text

        if len(r.json()["query"]["search"]) > 0:
            if None == entity_type:
                # return first result if entity type is not specified
                entry = r.json()["query"]["search"][0]
                entry["is_first_row"] = True
                ret = DbpediaApi.retrieve_dbpedia_by_name(entry['title'])
                return dict(entry.items() + ret.items())
            else:
                # return matched result if entity type is specified
                index_in_results = 0
                default_ret = {}

                for entry in r.json()["query"]["search"]:
                    index_in_results += 1
                    entry["index_in_results"] = index_in_results

                    #print entry

                    ret = DbpediaApi.retrieve_dbpedia_by_name(entry['title'])

                    if len(default_ret) == 0:
                        entry["is_first_row"] = True
                        default_ret = dict(entry.items() + ret.items())

                    #print "---->", ret
                    if None != ret and "types" in ret and DbpediaApi.match_entity_type(entity_type, ret["types"]):
                        entry["matched_entity_type"] = True
                        return dict(entry.items() + ret.items())

                return default_ret

        return {}

    @staticmethod
    def search_dbpedia(name, entity_type):
        ''' warning: this method is less effective then searchWikipedia 
            because it only does prefix search
        '''
        url_dict = {
            "QueryClass": entity_type,
            "QueryString": name}
        headers = {
            'Accept': 'application/json'}
        r = requests.get(
            "http://lookup.dbpedia.org/api/search/KeywordSearch"
            , params=url_dict
            , headers=headers)

        json_data = r.json()
        #print r.url
        #print len(json_data["results"])

        #select the best entry to return
        best_entry = {}
        best_similarity = None
        index_in_results = 0
        for entry in json_data["results"]:
            index_in_results += 1
            entry["index_in_results"] = index_in_results

            for key in ["templates", "categories"]:
                entry.pop(key, None)

            classes = entry.pop("classes")
            entry['types'] = []
            for class_ in classes:
                entry['types'].append(class_[u'uri'])

            similarity = UtilString.levenshtein(name, entry[u'label'])
            #ret_list.append(entry)
            #print entry

            if None == best_similarity or (best_similarity > similarity and similarity < len(name)):
                best_similarity = similarity
                best_entry = entry

        return best_entry
        
