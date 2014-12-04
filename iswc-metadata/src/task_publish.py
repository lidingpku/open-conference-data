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
from mu.lib_unicode import UnicodeReader, UnicodeWriter
import codecs
import re
import simplejson as json
import datetime
import time
import os
import sys
import icalendar
import pytz
import uuid

#print sys.getdefaultencoding()
reload(sys)
sys.setdefaultencoding("utf-8")
#print sys.getdefaultencoding()

class UtilJson:
    @staticmethod
    def add_init_dict(json_data, pre_keys, key, value):
        temp = json_data
        for k in pre_keys:
            if not k in temp:
                temp[k] = {}
            temp = temp[k]

        temp[key]=value
            
    @staticmethod
    def add_init_list(json_data, pre_keys, key, value, unique=False):
        temp = json_data
        for k in pre_keys:
            if not k in temp:
                temp[k] = {}
            temp = temp[k]

        if not key in temp:
            temp[key]=[]
            
        if unique and value in temp[key]:
            #skip duplicate insertion
            return 
            
        temp[key].append(value)


class ConfData(object):
    CONFIG = {"arq": os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apache-jena-2.10.1/bin/arq") }
    

    @staticmethod
    def update_index_data(id_data, global_config, data, data_local):
        """
        {"person":
            { "person_uri":[entry1, entry2]
            }
        }
        """

        for entity_type in ["person","organization"]:
            # read data
            id_query = "index-{}".format(entity_type)
            filename_csv_index = "%s/data/www/%s-%s.csv" % (
                global_config["home"], 
                id_data, 
                id_query)
                    

            with open(filename_csv_index) as f:
                csvreader = UnicodeReader(f)
                headers =  csvreader.next()
                for row in csvreader:
                    if len(row)<len(headers):
                        #print "skipping row %s" % row 
                        continue

                    entry = dict(zip(headers, row))
                    entry["year"] = entry["conf_uri"].split("/")[-1]

                    UtilJson.add_init_list(
                        data, 
                        [entity_type],
                        entry["uri"],
                        entry)               

                    UtilJson.add_init_list(
                        data_local,
                        [entity_type],
                        entry["uri"],
                        entry)



    @staticmethod
    def csv2html(id_data, global_config):
        #create json_conf data    
        json_conf ={}

        ######################
        #conf-paper
        filename_csv_conf_paper = "%s/data/www/%s-%s.csv" % (
            global_config["home"], 
            id_data, 
            "conf-paper")
                    
        indexed_proceedings ={}
        list_title = []
        with open(filename_csv_conf_paper) as f:
            csvreader = UnicodeReader(f)
            headers =  csvreader.next()
            while len(headers)<=1:
                print "skipping header row {0}".format( headers )
                headers =  csvreader.next()

            for row in csvreader:
                if len(row)<len(headers):
                    print "skipping row {0}".format( row )
                    continue

                entry = dict(zip(headers, row))
                
#                print entry
                if entry["subtitle_proceedings"]:
                    proceeding_title = "{} -- {}".format(entry["label_proceedings"], entry["subtitle_proceedings"])
                    if proceeding_title not in list_title:
                        list_title.insert(0, proceeding_title)
                else:
                    proceeding_title = "{}".format(entry["label_proceedings"])
                    if proceeding_title not in list_title:
                        list_title.append(proceeding_title)

                UtilJson.add_init_list(
                    indexed_proceedings, 
                    [proceeding_title],
                    entry["category"],
                    entry)
                
        
        #update json_conf
        for proceedings in list_title:
            #print proceedings
            json_proceedings ={}
            json_proceedings["title"] =proceedings
            UtilJson.add_init_list(json_conf, [], "proceedings", json_proceedings)
            for category in sorted(indexed_proceedings[proceedings].keys()):
                #print category
                json_category = {}
                if len(indexed_proceedings[proceedings].keys()) > 1:
                    json_category["title"] =category
                UtilJson.add_init_list(json_proceedings, [], "categories", json_category)
                json_category["papers"] =indexed_proceedings[proceedings][category]
        
        ######################
        #conf-person

        filename_csv_conf_person = "%s/data/www/%s-%s.csv" % (
            global_config["home"], 
            id_data, 
            "conf-person")
                    
        indexed_persons ={}
        with open(filename_csv_conf_person) as f:
            csvreader = UnicodeReader(f)
            headers =  csvreader.next()
            for row in csvreader:
                if len(row)<len(headers):
                    #print "skipping row %s" % row 
                    continue


                entry = dict(zip(headers, row))

                #print entry
                name = entry["name"]
                name = name.strip()
                name = re.sub("\s+"," ",name)

                
                cnt_paper = int(entry["cnt_paper"])
                if cnt_paper >0:
                    index_1 = entry["proceedings_label"]
                    if len(entry["proceedings_label"])==0:
                        index_1 = "All"
                        
                    index_1 = "[Proceedings] {}".format(index_1)
                    index_2 = "Authors"

                    UtilJson.add_init_dict(
                        indexed_persons, 
                        [index_1,index_2],
                        name,
                        entry)

                #consolidate affiliation
                organization = entry["organization"]
                if len(entry["organization"])>0:
                    entry["organization"] = organization.split(";")[0]

                #only keep direct conference role
                ALLOWED_EVENT_TYPE= []
                ALLOWED_EVENT_TYPE.append("http://data.semanticweb.org/ns/swc/ontology#ConferenceEvent")
#                ALLOWED_EVENT_TYPE.append("http://data.semanticweb.org/ns/swc/ontology#WorkshopEvent")
                if entry["role_event_type"] not in ALLOWED_EVENT_TYPE:
                    continue
                

                if entry["role_type"].endswith("Chair") and entry["role_event_type"].endswith("ConferenceEvent"):
                   entry["role_event_label"] = " {} (organization Committee)".format(entry["role_event_label"])


                UtilJson.add_init_dict(
                    indexed_persons, 
                    [entry["role_event_label"],entry["role_label"]],
                    name,
                    entry)

                
        #update json_conf
        for role_event_label in sorted(indexed_persons.keys()):
            #print role_event_label
            josn_role_event ={}
            josn_role_event["title"] =role_event_label
            UtilJson.add_init_list(json_conf, [], "events", josn_role_event)


            list_role = []
            for role_label in sorted(indexed_persons[role_event_label].keys()):
                if "Chair" in role_label or "Webmaster" in role_label:
                    list_role.insert(0, role_label)
                else:
                    list_role.append(role_label)

            for role_label in list_role:
                #print role_label
                json_role_label = {}
                json_role_label["title"] =role_label
                UtilJson.add_init_list(josn_role_event, [], "roles", json_role_label)
                json_role_label["persons"] = sorted( indexed_persons[role_event_label][role_label].values())
    
        
                    

        ######################
        # write xyz-proceedings
        id_html = "proceedings"


        filename_html = "%s/data/www/%s-%s.html" % (
            global_config["home"], 
            id_data, 
            id_html)        
        
        json_template = resource_string('resources.files', '{}.jsont'.format(id_html))
        content= jsontemplate.expand(json_template, json_conf)
        with codecs.open(filename_html,"w","utf-8") as f:
            f.write(u'\ufeff')
            f.write(content)


        ######################
        # write xyz-people
        id_html = "people"
        filename_html = "%s/data/www/%s-%s.html" % (
            global_config["home"], 
            id_data, 
            id_html)        
        
        json_template = resource_string('resources.files', '{}.jsont'.format(id_html))
        content= jsontemplate.expand(json_template, json_conf)
        with codecs.open(filename_html,"w","utf-8") as f:
            f.write(u'\ufeff')
            f.write(content)


    
        ######################
        #conf-event

        filename_csv_conf_event = "%s/data/www/%s-%s.csv" % (
            global_config["home"], 
            id_data, 
            "conf-event")
                    
        dict_events ={}
        list_events = []
        conf_event_name  =""
        with open(filename_csv_conf_event) as f:
            csvreader = UnicodeReader(f)
            headers =  csvreader.next()
            for row in csvreader:
                if len(row)<len(headers):
                    #print "skipping row %s" % row 
                    continue

                entry = dict(zip(headers, row))
                
                #print entry
                
                dict_events[entry["event_uri"]] = entry
                list_events.append(entry)

                event_type = entry["event_type"].split('#')[-1]
                if event_type in ['ConferenceEvent']:
                    conf_event_name = entry["label"]
                elif event_type in ['InvitedTalkEvent', 'PanelEvent']:
                    entry['category'] = event_type.replace('Event', '')

        indexed_events ={}
        map_events ={}
        for entry in list_events:

            temp = entry["event_type"].split('#')[-1]
            temp = temp.replace("Event","")
            if not temp in ["Tutorial","Talk","Special","Break"]:
                entry["event_type_label"] = temp

            UtilJson.add_init_list(
                map_events,
                [],
                entry["super_event_uri"],
                entry["event_uri"],
                True)

            super_event_name = conf_event_name
            if entry["super_event_uri"] and entry["super_event_uri"] in dict_events:
                super_event_type = dict_events[entry["super_event_uri"]]["event_type"].split('#')[-1].replace("Event","")
                if super_event_type in ['Workshop', 'Tutorial'] :
                    super_event_name = dict_events[entry["super_event_uri"]]["label"]
                    if super_event_name.lower().find("Doctoral Consortium".lower()) < 0:
                        if not super_event_name.startswith(super_event_type):
                            super_event_name = "{}: {}".format(super_event_type, super_event_name)

            entry['start_x'] = entry['start']
            entry['end_x'] = entry['end']
            if len(entry['start'])>0:
                #skip talk event
                if len(entry['order_in_super_event'])>0:
                    continue

                date = entry['start'][0:10]
                entry['start_x'] = entry['start'][11:-3]
                date_end = date
                if len(entry['end'])>0:
                    date_end = entry['end'][0:10]
                    entry['end_x'] = entry['end'][11:-3]
                #only keep same day events
                if date_end == date:
                    UtilJson.add_init_list(
                        indexed_events,
                        [super_event_name],
                        date,
                        entry)
        #print json.dumps(map_events, indent=4)
            
        #update json_conf
        list_event_name = []
        for event_name in sorted(indexed_events.keys()):
            if conf_event_name == event_name:
                list_event_name.insert(0, event_name)
            else:
                list_event_name.append(event_name)

        for event_name in list_event_name:
            top_events_in_program = indexed_events[event_name]
            json_program = {
                'title': event_name
            }
            UtilJson.add_init_list(json_conf, [], "top_programs", json_program)

            for date in sorted(top_events_in_program.keys()):
                events_in_program_date = top_events_in_program[date]
                json_date_program ={}
                if len(top_events_in_program) >1:
                    json_date_program["title"] = datetime.datetime(*time.strptime(date,"%Y-%m-%d")[0:5]).strftime("%Y-%m-%d (%A)")
                json_date_program["events"] = events_in_program_date
                UtilJson.add_init_list(json_program, [], "date_programs", json_date_program)

                #    sorted(events_in_program_date, key=lambda item: item['start'])
                for entry in events_in_program_date:

                    entry["super_event_type"] = dict_events[entry["super_event_uri"]]["event_type"]
                    if entry["super_event_type"] == "http://data.semanticweb.org/ns/swc/ontology#TrackEvent":
                        entry["track"] = dict_events[entry["super_event_uri"]]["label"]
                    else:
                        entry["track"] = ""

                    #if entry["event_type"] == "http://data.semanticweb.org/ns/swc/ontology#SessionEvent":
                    if entry["event_uri"] in map_events:
                        for sub_event_uri in map_events[entry["event_uri"]]:
                            UtilJson.add_init_list(entry, [], "talks", dict_events[sub_event_uri])

        ######################
        # write json-data
        #print json.dumps(json_conf, indent=4)
        filename_json = "%s/data/www/%s-conf.json" % (
            global_config["home"],
            id_data)
        with codecs.open(filename_json,"w","utf-8") as f:
            json.dump(json_conf, f, indent=4)

        ######################
        # write xyz-program
        id_html = "program"
        filename_html = "%s/data/www/%s-%s.html" % (
            global_config["home"], 
            id_data, 
            id_html)        
        
        json_template = resource_string('resources.files', '{}.jsont'.format(id_html))
        content= jsontemplate.expand(json_template, json_conf)
        with codecs.open(filename_html,"w","utf-8") as f:
            f.write(u'\ufeff')
            f.write(content)    

        ######################
        # write icalendar
        id_html = "program"
        filename_ics_prefix = "%s/data/www/%s-%s" % (
            global_config["home"],
            id_data,
            id_html)

        ConfData.json_conf2ics(json_conf, filename_ics_prefix)

    @staticmethod
    def create_datetime(str_dt, timezone):
        tuple_date = re.sub('[-:T]',' ',str_dt).split(' ')
        dt_date = datetime.datetime(*[int(x) for x in tuple_date], tzinfo=timezone)
        return dt_date

    @staticmethod
    def create_ics_event(json_event, str_program):
        event = icalendar.Event()
        timezone= pytz.timezone(json_event['tzid'])

        event.add('summary', json_event['label'])
        #print json_event['start']
        event.add('dtstart', ConfData.create_datetime(json_event['start'],timezone))

        event['uid'] = '{}{}{}'.format(str_program, json_event['start'], str(uuid.uuid4()))

        event.add('dtend', ConfData.create_datetime(json_event['end'],timezone))

        event.add('location', json_event['room'])

        event_type = json_event["event_type"].split('#')[-1]
        event.add('category', event_type)

        list_description =[]
        for p in ['chair_person','presenter_person','abstract']:
            if json_event[p]:
                list_description.append('{}: {}'.format(p.replace('_person',''), json_event[p]))
        if 'talks' in json_event:
            for talk in json_event['talks']:
                temp =''
                if talk['start']:
                    temp = '{}-{}'.format(talk['start'][11:-3], talk['end'][11:-3])
                if talk['category']:
                    temp = '{} {}'.format(temp, talk['category'])
                if temp:
                    temp = '({})'.format(temp)

                temp = ' -{} {}'.format(talk['label'], temp)
                list_description.append(temp)

        event.add('description', '\r\n'.join(list_description))

        #event.add('dtstamp', datetime(2005,4,4,0,10,0,tzinfo=pytz.utc))
        event.add('dtstamp', datetime.datetime.now(timezone))
        #event.add('priority', 5)
        #

        return event

    @staticmethod
    def json_conf2ics(data_json_conf, filename_ics_prefix=None):

        if 'top_programs' not in data_json_conf:
            return

        try:
            for top_program in data_json_conf['top_programs']:
                str_program = top_program['title'].replace(' ', '_')
                print str_program

                cal = icalendar.Calendar()
                #data_json_conf['top_programs'].keys()[0]
                cal.add('prodid', '-//program of {}//'.format(top_program['title']))
                cal.add('version', '2.0')

                for date_program in top_program['date_programs']:
    #                if 'title' not in date_program:
    #                    continue

                    for session in date_program['events']:
                        #print session

                        #skip registration event
                        if session['label'].startswith('Registration'):
                            continue

                        event =ConfData.create_ics_event(session, str_program)
                        cal.add_component(event)

                        #catch
    #                    event_type = session["event_type"].split('#')[-1].replace("Event", "")
    #                    if event_type in ['Workshop', 'Tutorial']:
    #                        map_title_event[session['label']] = event

                if filename_ics_prefix:
                    filename_ics = '{}.ics'.format(filename_ics_prefix)
                    with open(filename_ics, 'wb') as f:
                        f.write(cal.to_ical())

                #only process the first one, which should be the main conference
                break
        except:
            print 'skip ....'

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

        if not os.path.exists(ConfData.CONFIG["arq"]):
            msg = "required file is missing {}".format(ConfData.CONFIG["arq"])
            print msg
            raise RuntimeError(msg)

        command= "{3} --data {0} --query {1} --results CSV > {2} 2>&1".format(
            filename_rdf, 
            filename_query, 
            filename_output,
            ConfData.CONFIG["arq"])
        #print command
        call(command, shell=True)


    @staticmethod
    def gen_index_entity_global(data_index_entity, global_config):
        for entity_type  in data_index_entity:
            print 'process {}'.format(entity_type)

            json_data = {entity_type: [] }
            for entity_uri in sorted(data_index_entity[entity_type]):
                entity_conf = data_index_entity[entity_type][entity_uri]
                json_data_sub = {}
                json_data_sub["entity_uri"] = entity_uri
                json_data_sub["conf"] = entity_conf
                json_data_sub["name"] = entity_conf[0]["name"]
                json_data[entity_type].append(json_data_sub)

            filename_output = "{}/data/www/index-{}.json".format(global_config["home"], entity_type)
            with codecs.open(filename_output,"w","utf-8") as f:
                json.dump(json_data, f, indent=4)

            id_html = "index-{}".format(entity_type)
            json_template = resource_string('resources.files', '{}.jsont'.format(id_html))
            content= jsontemplate.expand(json_template, json_data)

            filename_output = "{}/data/www/index-{}.html".format (global_config["home"], entity_type)
            with codecs.open(filename_output,"w","utf-8") as f:
                f.write(u'\ufeff')
                f.write(content)

    @staticmethod
    def gen_index_entity_one_conf(data_index_entity, global_config, id_data):
        for entity_type in data_index_entity:
            json_data = {entity_type: [] }
            line_number = 0
            for entity_uri in sorted(data_index_entity[entity_type]):
                entity_x = data_index_entity[entity_type][entity_uri]
                line_number += 1
                json_data_sub = entity_x[0]
                json_data_sub["line-number"] = line_number
                json_data_sub["entity_uri"] = entity_uri
                json_data[entity_type].append(json_data_sub)


            id_html = "index-table-{}".format(entity_type)
            json_template = resource_string('resources.files', '{}.jsont'.format(id_html))
            content= jsontemplate.expand(json_template, json_data)

            filename_output = "{}/data/www/{}-index-{}.html".format (global_config["home"], id_data, entity_type)
            with codecs.open(filename_output,"w","utf-8") as f:
                f.write(u'\ufeff')
                f.write(content)

    @staticmethod
    def run_generate_csv_and_html(global_config, allowed_year=[]):
        list_conference =[]

        data_index_entity ={}

        for year in range(2001, 2015):
            #if year not in [2014]:
            #    continue

            conference = { "id-swsa":"ISWC{}".format(year),
                        "id": "iswc-{}".format(year) }

            list_conference.append(conference)

            if len(allowed_year)>0:
                if year not in allowed_year:
                        continue

            print "processing {}".format(conference["id"])

            for id_query in ["conf-person","conf-paper","conf-event", "index-person", "index-organization"]:
                filename_rdf = "%s/data/www/%s-complete.ttl" % (global_config["home"], conference["id"])
                if "conf-paper" == id_query:
                    filename_rdf = "%s/data/www/%s-conf-paper.ttl" % (global_config["home"], conference["id"])    
                filename_query = "resources/files/%s.sparql" % (id_query)
                filename_output = "%s/data/www/%s-%s.csv" % (global_config["home"], conference["id"], id_query)
                ConfData.sparql_rdf2csv(filename_rdf, filename_query, filename_output)
            
            ConfData.csv2html(conference["id"], global_config)

            data_index_entity_local ={}
            ConfData.update_index_data(conference["id"], global_config, data_index_entity, data_index_entity_local)

            ConfData.gen_index_entity_one_conf(data_index_entity_local, global_config, conference['id'])

        #write index_page    
        filename_output = "{}/data/www/index.html".format (global_config["home"])
        json_index = {"conferences": list_conference}

        id_html = "index"
        json_template = resource_string('resources.files', '{}.jsont'.format(id_html))
        content= jsontemplate.expand(json_template, json_index)

        with codecs.open(filename_output,"w","utf-8") as f:
            f.write(u'\ufeff')
            f.write(content)    


        #write index_person and index_organization
        ConfData.gen_index_entity_global(data_index_entity, global_config)


def main():
    ###################################################################        
    # load global config
    # load config file
    with open("config.json") as f:
        global_config = json.load( f)


    # convert rdf(ttl) into csv and then html
#    ConfData.run_generate_csv_and_html(global_config, [2013])
    ConfData.run_generate_csv_and_html(global_config)

if __name__ == "__main__":
    main()
