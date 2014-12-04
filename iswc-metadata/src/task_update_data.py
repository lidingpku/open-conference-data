import os
import rdflib
from rdflib import *
from mu.lib_unicode import *

from dateutil import parser

from datetime import tzinfo, datetime
import copy
import re
import sys
#print sys.getdefaultencoding()
reload(sys)
sys.setdefaultencoding("utf-8")
#print sys.getdefaultencoding()
import json
from rdflib.namespace import RDF, FOAF, RDFS, OWL, DC, DCTERMS, SKOS

SWRC = Namespace('http://swrc.ontoware.org/ontology#')
SWC = Namespace('http://data.semanticweb.org/ns/swc/ontology#')

class TaskUpdateData:
    
    @staticmethod
    def update_data_iswc_patch(home, id_data, id_dogfood):
        #"http://data.semanticweb.org/dumps/conferences/iswc-2006-complete.rdf"
        filename_output_rdfxml = "%s/data/source/%s-complete.rdf" % (home, id_data)
        filename_output_add = "%s/data/www/%s-complete.add.ttl" % (home, id_data)
        filename_output_del = "%s/data/www/%s-complete.del.ttl" % (home, id_data)
        filename_output_new = "%s/data/www/%s-complete.ttl" % (home, id_data)
        filename_input_paper = "%s/data/www/%s-paper.ttl" % (home, id_data)
        graph_uri = "http://data.semanticweb.org/conference/%s/complete" % (id_dogfood.replace("-20",'/20'))
        
        graph = rdflib.Graph()
        graph.load(filename_output_rdfxml)
        
        graph_delta_del = Graph()
        graph_delta_add = Graph()

        #patch paper
        # graph_paper = rdflib.Graph()
        # graph_paper.load(filename_input_paper, format='n3')
        # for triple in graph_paper:
        #     if not triple in graph:
        #         graph_delta_add.add(triple)
        
        TaskUpdateData.clean_graph(graph, graph_delta_del, graph_delta_add )
        TaskUpdateData.patch_graph_with_paper(home, graph, graph_delta_del, graph_delta_add, graph_uri)
        TaskUpdateData.patch_graph_time(graph, graph_delta_del, graph_delta_add, graph_uri)
        TaskUpdateData.patch_graph_event(graph, graph_delta_del, graph_delta_add, graph_uri)
        TaskUpdateData.patch_graph_x(graph, graph_delta_del, graph_delta_add, graph_uri)
        
        cnt_triple_old = len(graph)
        for triple in graph_delta_del:
            graph.remove(triple)
        for triple in graph_delta_add:
            if not graph.__contains__(triple):
                graph.add(triple)
#                else:
                #print "-- contains tripe -->", triple
        cnt_triple_new = len(graph)
         
        print "-- {2} Triples -{0} +{1} [{3}]".format(
            len(graph_delta_del),
            len(graph_delta_add),
             len(graph),
             graph_uri)
        
        if len(graph_delta_add)>0:
            #print "--add-->", graph_delta_add.serialize(format='turtle')
            graph_delta_add.serialize(destination=filename_output_add, format='turtle', encoding="utf-8") 
            
        if len(graph_delta_del)>0:
            #print "--del-->", graph_delta_del.serialize()
            graph_delta_del.serialize(destination=filename_output_del, encoding="utf-8") 
            
        graph.serialize(destination=filename_output_new, format='turtle', encoding="utf-8") 

    @staticmethod
    def clean_node(term):
        if isinstance(term,rdflib.URIRef):
            # https://github.com/RDFLib/rdflib/blob/master/rdflib/term.py
            
            new_str = term.__str__().strip()
            if new_str!=term.__str__():
                return rdflib.URIRef(new_str)
                
        return None
        
    
    @staticmethod
    def clean_graph(graph, graph_delta_del, graph_delta_add ):
        for subject,predicate,obj in graph:
            #TODO only handle object
            modified = False

            new_subject = TaskUpdateData.clean_node(subject)
            if None != new_subject:
                modified = True
            else:
                new_subject = subject
                
            new_obj = TaskUpdateData.clean_node(obj)
            if None != new_obj:
                modified = True
            else:
                new_obj = obj
            
            new_obj = TaskUpdateData.clean_node(obj)
            if None!=new_obj:
                graph_delta_del.add([subject, predicate, obj])
                graph_delta_add.add([subject, predicate, new_obj])
                print "--cleaned triple--> " , new_obj.__str__()

    @staticmethod
    def strip_n3_string(n3string):
        m = re.match(r'("[^"]+")', n3string)
        if None!=m:
            return m.group(0)
        else:
            return None


    @staticmethod
    def replace_string(old, patterns):
        ret = old
        ret = ret.encode('ascii', 'replace_with_dash')
        for pattern in patterns:
            ret = re.sub(pattern, patterns[pattern], ret)

        if ret != old:
            return ret
        else:
            return None

    @staticmethod
    def patch_graph_event(graph, graph_delta_del, graph_delta_add, graph_uri):
        """ remove inferred subEventOf relation
        """
        sub_event = URIRef("http://data.semanticweb.org/ns/swc/ontology#isSubEventOf")
        map_s_o = {}
        for s, p, o in graph.triples((None, sub_event, None)):
            if s in map_s_o:
                set_o = map_s_o[s]
                set_o.append(o)
            else:
                set_o = [o]
                map_s_o[s]=set_o
        
        #print map_s_o
        #print len(map_s_o)

        for s, set_o in map_s_o.items():
            for o in set_o:
                if o in map_s_o:
                    for o2 in map_s_o[o]:
                        if (s, sub_event, o2) in graph:
                            graph_delta_del.add([s, sub_event, o2])

    @staticmethod
    def patch_graph_timezone_and_uri(graph, graph_delta_del, graph_delta_add, graph_uri, timezone):
        for s, p, o in graph:
            patterns_uri = {
                "[-\s]+": "-",
            }

            s_new = None
            o_new = None
            p_new = p

            if isinstance(s, URIRef):
                new_value = TaskUpdateData.replace_string( s.toPython(), patterns_uri )
                if None!= new_value:
                    print "changed s [{0}]".format( s.toPython() )
                    s_new = URIRef(new_value)

            if isinstance(o, Literal):
                #print o.datatype
                if URIRef("http://www.w3.org/2001/XMLSchema#dateTime") == o.datatype:
                    if isinstance(o.value, datetime):
                        new_datetime = datetime(
                            o.value.year, 
                            o.value.month,
                            o.value.day,
                            o.value.hour,
                            o.value.minute,
                            0,
                            0,
                            None )  # pytz.timezone('US/Eastern')
                        #new_datetime.replace(tzinfo= None)
                        #print o.value, "-->",new_datetime
                        o_new = Literal(new_datetime, datatype="http://www.w3.org/2001/XMLSchema#dateTime")
                    else:
                        if len(o)==10: # YYYY-mm-dd
                            o_new = Literal(o, datatype="http://www.w3.org/2001/XMLSchema#date")
                        else:
                            new_datetime = parser.parse(o)
                            if None != new_datetime:
                                o_new = Literal(new_datetime, datatype="http://www.w3.org/2001/XMLSchema#dateTime")

                    if p in [URIRef("http://www.w3.org/2002/12/cal/ical#dtStart"), URIRef("http://www.w3.org/2002/12/cal/ical#dtEnd")]:
                           p_new = URIRef(p.toPython().lower())

                           p_x = URIRef("http://www.w3.org/2002/12/cal/ical#tzid")
                           o_x = Literal(timezone)
                           if None==s_new:
                               graph_delta_add.add([s, p_x, o_x])
                           else:
                               graph_delta_add.add([s_new, p_x, o_x])


            elif isinstance(o, URIRef):
                new_value = TaskUpdateData.replace_string( o.toPython(), patterns_uri )
                if None!= new_value:
                    o_new = URIRef(new_value)
                    print "changed [{0}]".format( o.toPython() )

            if None!=s_new or None!=o_new:
                if None==s_new:
                    s_new =s
                if None==o_new:
                    o_new =o
                graph_delta_del.add([s, p, o])
                graph_delta_add.add([s_new, p_new, o_new])                

    @staticmethod
    def patch_graph_time(graph, graph_delta_del, graph_delta_add, graph_uri):
        if "http://data.semanticweb.org/conference/iswc/2012/complete" == graph_uri:
            TaskUpdateData.patch_graph_timezone_and_uri(graph, 
                graph_delta_del, graph_delta_add, graph_uri, "US/Eastern")
        elif "http://data.semanticweb.org/conference/iswc/2011/complete" == graph_uri:
            TaskUpdateData.patch_graph_timezone_and_uri(graph, 
                graph_delta_del, graph_delta_add, graph_uri, "Europe/Berlin")
        elif "http://data.semanticweb.org/conference/iswc-aswc/2007/complete" == graph_uri:
            TaskUpdateData.patch_graph_timezone_and_uri(graph, 
                graph_delta_del, graph_delta_add, graph_uri, "Asia/Seoul")

    @staticmethod
    def patch_graph_x(graph, graph_delta_del, graph_delta_add, graph_uri):
        if "http://data.semanticweb.org/conference/iswc/2009/complete" == graph_uri:
            s = URIRef("http://data.semanticweb.org/organization/franz-inc")
            p = FOAF.name
            o = Literal("Franz Inc.")
            graph_delta_add.add([s, p, o])

            s = URIRef("http://data.semanticweb.org/person/claudia-damato")
            p = FOAF.name
            o = Literal("Claudia d'Amato")
            graph_delta_add.add([s, p, o])

            s = URIRef("http://data.semanticweb.org/person/michael-witbrock")
            p = FOAF.name
            o = Literal("Michael Witbrock")
            graph_delta_add.add([s, p, o])

            s = URIRef("http://data.semanticweb.org/person/thomas-lukasiewicz")
            p = FOAF.name
            o = Literal("Thomas Lukasiewicz")
            graph_delta_add.add([s, p, o])

            s = URIRef("http://data.semanticweb.org/person/umberto-straccia")
            p = FOAF.name
            o = Literal("Umberto Straccia")
            graph_delta_add.add([s, p, o])

            s = URIRef("http://data.semanticweb.org/person/jans-aasman")
            p = FOAF.name
            o = Literal("Jans Aasman")
            graph_delta_add.add([s, p, o])

            s = URIRef("http://data.semanticweb.org/person/frank-van-harmelen")
            p = SWC.holdsRole
            p1 = SWC.heldBy
            o = URIRef("http://data.semanticweb.org/conference/iswc/2009/role/panelist")
            graph_delta_add.add([s, p, o])
            graph_delta_add.add([o, p1, s])

            s = URIRef("http://data.semanticweb.org/person/frardfs:labelnk-van-harmelen")
            p = SWC.holdsRole
            p1 = SWC.heldBy
            o = URIRef("http://data.semanticweb.org/conference/iswc/2009/role/panelist")
            graph_delta_del.add([s, p, o])
            graph_delta_del.add([o, p1, s])

            s = URIRef("http://data.semanticweb.org/person/frardfs:labelnk-van-harmelen")
            p = RDF.type
            o = FOAF.Person
            graph_delta_del.add([s, p, o])

    @staticmethod
    def patch_graph_with_paper(home, graph, graph_delta_del, graph_delta_add, graph_uri):
        graph_delta_add.bind("swrc", SWRC)
        graph.bind("swrc", SWRC)

        filename_paper_csv = "%s/data/source/iswc-all-papers.csv" % ( home )
        with open(filename_paper_csv) as f:
            csvreader = UnicodeReader(f)
            headers =  csvreader.next()
            for row in csvreader:
                if len(row)<len(headers):
                    #print "skipping row %s" % row 
                    continue

                entry = dict(zip(headers, row))
                
                if entry['source_uri'] == graph_uri:
                    if len(entry['paper_uri'])>0:
                        subject = URIRef(entry['paper_uri'])
                        
                        #validate if the URI has been described in original data
                        list_triples = list(graph[subject::])
                        if len(list_triples)==0:
                            raise "--uri not described in original data --> ", subject.__str__()
                            
                            
                        #patch new triples
                        for link in ['link_open_access', 'link_publisher']:
                            if len(entry[link])>0 :
                                #print "--add link--> " , entry[link]

                                obj =  URIRef(entry[link])
                                
                                for predicate in [SWRC[link], SWRC.url]:
                                    triple = [subject, predicate, obj]
                                    graph_delta_add.add(triple)
                                                    
        

def main():
    ###################################################################        
    # load global config
    # load config file
    with open("config.json") as f:
        global_config = json.load( f)



    ###################################################################        
    # run update data
    for year in range(2006,2012):
        local_config= {    "year":"{}".format(year), 
                "id-swsa": "ISWC{}".format(year),
                "id-dogfood": "iswc-{}".format(year),
                "id": "iswc-{}".format(year),
            }
        if year==2007:
            local_config["id-dogfood"]="iswc-aswc-2007"
        # elif year==2001:
        #     local_config["id-dogfood"]="swws-2001"
        print "processing {}".format(local_config["id"])

        TaskUpdateData.update_data_iswc_patch(
            global_config["home"],
            local_config["id"],
            local_config["id-dogfood"])

if __name__ == "__main__":
    main()
