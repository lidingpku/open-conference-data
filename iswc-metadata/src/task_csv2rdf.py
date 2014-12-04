# -*- coding: utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import rdflib
from rdflib.namespace import RDF, FOAF, RDFS, OWL, DC, DCTERMS, SKOS
from rdflib import URIRef, Literal, Namespace, XSD
import json
from mu.lib_unicode import UnicodeReader, UnicodeWriter
from mu.lib_dbpedia import DbpediaApi
import mu.mutil

from lib_ext import *
import re
import os
import hashlib
import json
import datetime
import urllib
import unicodedata

SWRC = Namespace('http://swrc.ontoware.org/ontology#')
SWC = Namespace('http://data.semanticweb.org/ns/swc/ontology#')
BIBO = Namespace('http://purl.org/ontology/bibo/')
ICAL = Namespace('http://www.w3.org/2002/12/cal/ical#')
DCTYPE = Namespace('http://purl.org/dc/dcmitype/')

VERSION_INFO = "iswc metadata 2001-2014 (2013-10-02)"


def expand_entry(entry):
    map_data={}
    if 'uri_me' in entry:
        map_data["[ME]"]=entry['uri_me']
    map_data["[WORKSHOP]"] ='http://data.semanticweb.org/workshop'
    for key, value in entry.items():
        for k, v in map_data.items():
            temp = entry[key].replace(k, v)
            if temp != entry[key]:
                #print "\n{}\n-->\n{}".format(entry[key], temp)
                entry[key] = temp


class DataIswc(object):
    def __init__(self, local_config, global_config, dbpedia_api={}):
        self.graph = rdflib.Graph()
        self.graph.bind("foaf", FOAF)
        self.graph.bind("dc", DC)
        self.graph.bind("owl", OWL)
        self.graph.bind("swrc", SWRC)
        self.graph.bind("swc", SWC)
        self.graph.bind("skos", SKOS)
        self.graph.bind("bibo", BIBO)
        self.graph.bind("dcterms", DCTERMS)
        self.graph.bind("ical", ICAL)
        self.graph.bind("dctype", DCTYPE)

        self.local_config = local_config
        self.global_config = global_config

        self.map_name_res = {}
        #self.map_name_name = {}
        self.dbpedia_api = dbpedia_api
        self.list_name_untyped = set()

    @staticmethod
    def dbpedia_api_load(dir_data):
        dbpedia_api = {}
        if os.path.exists(dir_data):
            namespace = DataIswc.get_namespace(DataIswc.PREFIX_ORG)
            dbpedia_api[namespace] = DbpediaApi(dir_data, DbpediaApi.ENTITY_TYPE_ORGANIZATION)
            print "[{}] {} name mappings loaded".format(
                namespace,
                len(dbpedia_api[namespace].map_name))

            # namespace = DataIswc.get_namespace(DataIswc.PREFIX_PERSON)
            # dbpedia_api[namespace] = DbpediaApi(dir_data, DbpediaApi.ENTITY_TYPE_PERSON)
            # print "[{}] {} name mappings loaded".format(
            #     namespace,
            #     len(dbpedia_api[namespace].map_name))

        return dbpedia_api

    @staticmethod
    def dbpedia_api_write(dbpedia_api):
        #save new entities
        for api in dbpedia_api.values():
            print "[]{} name mappings ".format(len(api.map_name))
            api.write_new_data()


    # def load_metadata(self):
    #     filename_source= "{0}/data/entity/organisation.csv".format(self.global_config["home"])
    #     if os.path.exists(filename_source):
    #         with open (filename_source) as f:
    #             csvreader = UnicodeReader(f)
    #             headers =  csvreader.next()
    #             for row in csvreader:
    #                 entry = dict(zip(headers, row))

    #                 self.map_name_name[entry["altLabel"]] =    {
    #                     "prefLabel":entry["title"],
    #                     "dbpediaUri":entry["uri"]}

    #     print "{0} name mappings loaded".format(len(self.map_name_name))

    def run(self):
    #        self.load_metadata()
        self.init_map_person_name()

        self.process_organization()
        self.process_person()
        self.process_proceedings()
        self.process_paper()
        self.process_event()
        self.process_misc()
        filename_output = "{0}/data/www/{1}-complete.ttl".format(
            self.global_config["home"],
            self.local_config["id"])
        with open(filename_output, "w") as f:
            content = self.graph.serialize(format='turtle')
            f.write(content)

        print "{} name mappings without type".format(len(self.list_name_untyped))

    def run_paper_x(self):
        self.process_paper()
        self.process_proceedings()
        #self.process_misc()
        filename_output = "{0}/data/www/{1}-conf-paper.ttl".format(
            self.global_config["home"],
            self.local_config["id"])
        with open(filename_output, "w") as f:
            content = self.graph.serialize(format='turtle')
            f.write(content)

    NS_ROOT = "http://data.semanticweb.org/"
    PREFIX_ORG = "organization"
    PREFIX_PERSON = "person"

    PROP2URI = {
        #datatype property
        "label": {"p": [RDFS.label], "xsd": XSD.string},
        "hasAcronym": {"p": [SWC.hasAcronym], "xsd": XSD.string},
        "acronym": {"p": [SWC.hasAcronym], "xsd": XSD.string},
        "name": {"p": [RDFS.label, FOAF.name], "xsd": XSD.string},
        "title": {"p": [RDFS.label, DC.title, DCTERMS.title], "xsd": XSD.string},
        "abstract": {"p": [SWRC.abstract], "xsd": XSD.string},
        "hasAbstract": {"p": [SWRC.abstract], "xsd": XSD.string},
        "year": {"p": [SWRC.year], "xsd": XSD.string},
        "pages": {"p": [SWRC.pages], "xsd": XSD.string},
        "keywords": {"p": [SWRC.listKeyword], "xsd": XSD.string, "delimiter": ","},
        "publisher": {"p": [SWRC.publisher], "xsd": XSD.string},
        "series": {"p": [SWRC.series], "xsd": XSD.string},
        "volume": {"p": [SWRC.volume], "xsd": XSD.string},
        "subtitle": {"p": [SWRC.subtitle], "xsd": XSD.string},
        "alt-name": {"p": [SKOS.altLabel], "xsd": XSD.string, "delimiter": ","},
        "other_names": {"p": [SKOS.altLabel], "xsd": XSD.string, "delimiter": ","},
        "dtStart": {"p": [ICAL.dtstart], "xsd": XSD.dateTime},
        "start": {"p": [ICAL.dtstart], "xsd": XSD.dateTime},
        "dtEnd": {"p": [ICAL.dtend], "xsd": XSD.dateTime},
        "end": {"p": [ICAL.dtend], "xsd": XSD.dateTime},
        "tzid": {"p": [ICAL.tzid], "xsd": XSD.string},
        "locationRoom": {"p": [SWC.hasLocation, SWC.room], "xsd": XSD.string},
        "room": {"p": [SWC.hasLocation, SWC.room], "xsd": XSD.string},
        "locationAddress": {"p": [SWC.hasLocation, SWC.address], "xsd": XSD.string},
        "address": {"p": [SWC.hasLocation, SWC.address], "xsd": XSD.string},
        "orderInSuperEvent": {"p": [SWC.orderInSession, SWC.order_in_super_event], "xsd": XSD.integer},
        "order_in_super_event": {"p": [SWC.orderInSession, SWC.order_in_super_event], "xsd": XSD.integer},
        "category": {"p": [SWRC.category], "xsd": XSD.string},

        #object property
        "link_open_access": {"p": [SWRC.url, SWRC.link_open_access]},
        "link_open_access": {"p": [SWRC.url, SWRC.link_open_access]},
        "link_publisher": {"p": [SWRC.url, SWRC.link_publisher]},
        "link_publisher": {"p": [SWRC.url, SWRC.link_publisher]},
        "linkDocument": {"p": [SWRC.url, SWRC.link_document]},
        "link_document": {"p": [SWRC.url, SWRC.link_document]},
        "depiction": {"p": [FOAF.depiction]},
        "logo": {"p": [FOAF.logo]},
        "homepage": {"p": [FOAF.homepage]}
    }

    @staticmethod
    def get_namespace(prefix):
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

    def cache_map_name_res(self, name, res):
        #remove extra white space around
        name = name.strip()
        name = re.sub("\s+", " ", name)
        localname = create_ascii_localname(name)
        self.map_name_res[localname] = res

    def create_list_named_entity(self, namespace, name):

        real_name = None
        if name in self.map_name_info:
            if "real_name" in self.map_name_info[name]:
                real_name=self.map_name_info[name]["real_name"]

        #remove extra white space around
        name = name.strip()
        name = re.sub("\s+", " ", name)

        ret = {}

        #use canonical name
        bool_processed = False
        map_name_entry= {}
        if namespace in self.dbpedia_api:
            api = self.dbpedia_api[namespace]
            map_name_entry = api.process_names(name)
            for name_new in map_name_entry:
                entry = map_name_entry[name_new]

                if DbpediaApi.is_entry_auto(entry):
                    #print entry
                    print "new entry [{}]=>[{}]".format(name_new, entry["title"])
                elif DbpediaApi.is_entry_skip(entry):
                    print "skip entry [{}]=>[{}]".format(name_new, entry["title"])
                else:
                    #print entry
                    bool_processed = True
        else:
            map_name_entry[name] = None

        for name_new in map_name_entry:
            entry = map_name_entry[name_new]

            if not bool_processed:
                self.list_name_untyped.add(name_new)

            localname = create_ascii_localname(name_new)
            if localname in self.map_name_res:
                ret[name_new] = self.map_name_res[localname]
            else:
                uri = "{0}{1}".format(namespace, localname)
                res_entity = URIRef(uri)
                if real_name:
                    self.create_triple_simple(res_entity, "name", real_name)
                else:
                    self.create_triple_simple(res_entity, "name", name_new)


                self.map_name_res[localname] = res_entity
                if entry and 'uri' in entry and entry['uri']:
                    self.graph.add((res_entity, OWL.sameAs, URIRef(entry['uri'])))

                if namespace == DataIswc.get_namespace(DataIswc.PREFIX_PERSON):
                    self.graph.add((res_entity, RDF.type, FOAF.Person))
                elif namespace == DataIswc.get_namespace(DataIswc.PREFIX_ORG):
                    self.graph.add((res_entity, RDF.type, FOAF.Organization))

                ret[name_new] = res_entity
        return ret

    def create_role_to_event(self, uri_event, role_type, role_label, res_entity):
        if len(uri_event) == 0:
            return
        if len(role_type) == 0:
            return
        if len(role_label) == 0:
            return

        uri_event = self.expand_uri(uri_event)
        res_event = URIRef(uri_event)
        res_role_type = URIRef(self.expand_uri(role_type))
        uri_role = "%s/%s" % (uri_event, create_ascii_localname(role_label) )
        res_role = URIRef(uri_role)

        self.graph.add((res_role, RDF.type, res_role_type))
        self.graph.add((res_role, RDFS.label, Literal(role_label)))
        self.graph.add((res_role, SWC.isRoleAt, res_event))
        self.graph.add((res_role, SWC.heldBy, res_entity))
        self.graph.add((res_event, SWC.hasRole, res_role ))
        self.graph.add((res_entity, SWC.holdsRole, res_role))

    def create_triple_complex(self, res_subject, list_field, entry):
        for field in list_field:
            if field in entry:
                self.create_triple_simple(res_subject, field, entry[field])

    def create_triple_simple(self, res_subject, field, value):
        if len(value) == 0:
            return

        for p in DataIswc.PROP2URI[field]["p"]:
            if "xsd" in DataIswc.PROP2URI[field]:
                if XSD.string == DataIswc.PROP2URI[field]["xsd"]:
                    self.graph.add((res_subject, p, Literal(value)))
                else:
                    self.graph.add((res_subject, p, Literal(value, datatype=DataIswc.PROP2URI[field]["xsd"])))
            else:
                self.graph.add((res_subject, p, URIRef(value)))

    def process_misc(self):
        res_me = URIRef(self.expand_uri("[ME]"))
        res_data = URIRef(self.expand_uri("[ME]/complete"))
        self.graph.add((res_me, SWC.completeGraph, res_data ))
        self.graph.add((res_data, RDF.type, DCTYPE.Dataset ))
        self.graph.add((res_data, DCTERMS.hasVersion, Literal(VERSION_INFO)))
        self.graph.add((res_data, RDFS.comment, Literal(
            "This dataset is created by Li Ding http://liding.org. To learn more about this dataset, go to https://github.com/lidingpku/open-conference-data/tree/master/data/iswc ")))
        self.graph.add(
            (res_data, DCTERMS.modified, Literal(datetime.datetime.now().isoformat(), datatype=XSD.datetime)))
        self.graph.add((res_data, DCTERMS.creator, Literal("Li Ding")))

    def process_organization(self):
        filename = "{0}/data/source/{1}-organization.csv".format(
            self.global_config["home"],
            self.local_config["id"])

        with open(filename) as f:
            csvreader = UnicodeReader(f)
            headers = csvreader.next()
            for row in csvreader:
                if len(row) < len(headers):
                    #print "skipping row %s" % row 
                    continue

                entry = dict(zip(headers, row))

                if len(entry["name"]) == 0:
                    #print "skipping empty name row %s" % entry
                    continue

                for res_organization in self.create_list_named_entity(DataIswc.get_namespace(DataIswc.PREFIX_ORG), entry["name"]).values():

                    #object properties
                    self.create_triple_complex(res_organization, ["homepage", "logo"], entry)

                    #role
                    self.create_role_to_event(
                        entry["role_event"],
                        entry["role_type"],
                        entry["role_label"],
                        res_organization)


    def init_map_person_name(self):
        if hasattr(self, "map_name"):
            return

        # load global entity name mappings
        filename = "{0}/data/entity/person.csv".format(
            self.global_config["home"],
            self.local_config["id"])

        map_name = {}       #othername -> name
        map_name_info = {}  #name -> (real name, list of other name)

        with open(filename) as f:
            csvreader = UnicodeReader(f)
            headers = csvreader.next()
            for row in csvreader:
                if len(row) != len(headers):
                    #print "skipping mismatch row %s" % row
                    continue

                entry = dict(zip(headers, row))

                if entry["name"]:
                    name = entry["name"].strip()
                    if ["other_names"]:
                        #real_name = entry["name"]
                        #if "real_name" in entry:
                        #    real_name = entry["real_name"]

                        map_name_info[name] = {"other_names": [x.strip() for x in entry["other_names"].split(";")]}
                        for other_name in map_name_info[name]["other_names"]:
                            map_name[other_name] = name

        self.map_name = map_name
        self.map_name_info = map_name_info

    def get_final_name(self,name):

        self.init_map_person_name()

        name = name.strip()

        if name in self.map_name:
            return self.map_name[name]
        else:
            return name

    def process_person(self):
        #load person
        filename = "{0}/data/source/{1}-person.csv".format(
            self.global_config["home"],
            self.local_config["id"])

        with open(filename) as f:
            csvreader = UnicodeReader(f)
            headers = csvreader.next()
            for row in csvreader:

                if len(row) != len(headers):
                    #print "skipping mismatch row %s" % row 
                    continue

                entry = dict(zip(headers, row))

                if len(entry["name"]) == 0:
                    #print "skipping empty name row %s" % entry
                    continue

                name = entry["name"].strip()

                name = self.get_final_name(name)

                for res_person in self.create_list_named_entity(DataIswc.get_namespace(DataIswc.PREFIX_PERSON), name).values():
                    #map other names
                    for other_name in entry["other_names"].split(","):
                        self.cache_map_name_res(other_name, res_person)

                    if name in self.map_name_info:
                        for other_name in self.map_name_info[name]["other_names"]:
                            self.cache_map_name_res(other_name, res_person)

                    #object properties
                    self.create_triple_complex(res_person, ["homepage"], entry)

                    #role
                    self.create_role_to_event(
                        entry["role_event"],
                        entry["role_type"],
                        entry["role_label"],
                        res_person)

                    #organization
                    if "organization" in entry:
                        for org in entry["organization"].split(";"):
                            if len(org) == 0:
                                continue

                            for res_organization in self.create_list_named_entity(DataIswc.get_namespace(DataIswc.PREFIX_ORG), org).values():
                                self.graph.add((res_organization, FOAF.member, res_person))
                                #inverse property
                                self.graph.add((res_person, SWRC.affiliation, res_organization))

                    #alt-name
                    self.create_triple_complex(res_person, ["other_names"], entry)



                    #email
                    if len(entry["email"]) > 0:
                        if not entry["email"].startswith("mailto:"):
                            mbox = "mailto:%s" % entry["email"]
                        else:
                            mbox = entry["email"]

                        mbox_sha1sum = hashlib.sha1(mbox).hexdigest()
                        #self.graph.add( (res_person, FOAF.mbox, URIRef(mbox)) )
                        self.graph.add((res_person, FOAF.mbox_sha1sum, Literal(mbox_sha1sum)))


    def process_event(self):


        filename = "{0}/data/source/{1}-event.csv".format(
            self.global_config["home"],
            self.local_config["id"])

        counter_event = MyCounter()

        with open(filename) as f:
            csvreader = UnicodeReader(f)
            headers = csvreader.next()
            for row in csvreader:

                if len(row) != len(headers):
                    #print "skipping mismatch row %s" % row 
                    continue

                entry = dict(zip(headers, row))

                if len(entry["label"].strip()) == 0:
                    #print "skipping empty label row %s" % entry
                    continue

                if len(entry["event_type"].strip()) == 0:
                    #print "skipping empty event_type row %s" % entry
                    continue

                if entry["event_uri"].startswith("#"):
                    #print "skipping empty commented row %s" % entry
                    continue

                #set default super event
                if len(entry["super_event_uri"]) == 0:
                    entry["super_event_uri"] = "[ME]"

                expand_entry(entry)

                uri_super_event = self.expand_uri(entry["super_event_uri"])
                res_super_event = URIRef(uri_super_event)

                if len(entry["event_uri"]) == 0:
                    counter_event.inc(uri_super_event)
                    entry["event_uri"] = "%s/event-%02d" % (
                        uri_super_event,
                        counter_event.data[uri_super_event])

                uri_event = self.expand_uri(entry["event_uri"])
                res_event = URIRef(uri_event)

                #event type
                self.graph.add((res_event, RDF.type, SWC[entry["event_type"]]))

                #super event
                self.graph.add((res_event, SWC.isSubEventOf, res_super_event))
                self.graph.add((res_super_event, SWC.isSuperEventOf, res_event))

                #simple properties
                self.create_triple_complex(
                    res_event,
                    ["label", "acronym", "abstract",
                     "order_in_super_event",
                     "start", "end", "tzid",
                     "room", "address",
                     "homepage", "link_document", "logo"],
                    entry)

                #linking paper event
                if "TalkEvent" == entry["event_type"]:
                    if entry["label"] in self.map_name_res:
                        res_paper = self.map_name_res[entry["label"]]
                        self.graph.add(( res_event, SWC.hasRelatedDocument, res_paper))
                        self.graph.add(( res_paper, SWC.relatedToEvent, res_event))
                    else:
                        print "missing paper link [{}]".format(entry["label"])
                        #print json.dumps(self.map_name_res, indent=4, sort_keys=True)
                        sys.exit(0)

                #role -chair
                for role in ["Chair", "Presenter"]:

                    role_lower = role.lower()
                    if len(entry[role_lower + "_person"]) > 0:
                        person_data = DataIswc.parse_person_list(entry[role_lower + "_person"])
                        for name in person_data["list"]:
                            if len(name) == 0:
                                continue

                            name = self.get_final_name(name)

                            for res_person in self.create_list_named_entity(DataIswc.get_namespace(DataIswc.PREFIX_PERSON),name).values():

                                role_label_x = entry[role_lower + "_label"]
                                event_type_x = entry["event_type"].split("#")[-1].replace("Event", "")
                                if event_type_x in ["Workshop", "Tutorial"]:
                                    role_label_x = u"{} {}".format(event_type_x, role_label_x)

                                assert (len(role.strip())>0)

                                self.create_role_to_event(
                                    uri_event,
                                    "swc:" + role,
                                    role_label_x,
                                    res_person)


    def create_container(self, elements, contType, uri_subject=None):
        '''http://dev.w3.org/2004/PythonLib-IH/NewRDFLib/rdflib/Graph.py'''
        if None == uri_subject:
            container = BNode()
        else:
            container = URIRef(uri_subject)

        self.graph.add((container, RDF.type, contType))
        for i in range(0, len(elements)):
            uri_pred = "%s_%d" % (RDF, i + 1)
            pred = URIRef(uri_pred)
            self.graph.add((container, pred, elements[i]))
        return container


    @staticmethod
    def parse_person_list(text):
        author_x = text
        author_x = re.sub("[,\s]+and[,\s]+", ",", author_x)
        author_x = re.sub("\s+", " ", author_x)
        list_author_x = [x.strip() for x in author_x.split(",")]
        if "" in list_author_x:
            #print "....."
            list_author_x.remove("")

        if len(list_author_x) > 1:
            author_x_and = "{} and {}".format(",".join(list_author_x[0:-1]), list_author_x[-1])
        else:
            author_x_and = list_author_x[0]

        ret = {}
        ret["text"] = author_x_and
        ret["list"] = list_author_x
        return ret

    def process_paper(self):
        filename = "{0}/data/source/iswc-all-papers.csv".format(
            self.global_config["home"])

        if self.local_config["id"] in ["iswc-2013","iswc-2014"]:
            filename = "{}/data/source/{}-paper.csv".format(
                self.global_config["home"],
                self.local_config["id"])

        counter_paper = MyCounter()
        with open(filename) as f:
            csvreader = UnicodeReader(f)
            headers = csvreader.next()
            for row in csvreader:

                if len(row) != len(headers):
                    #print "skipping mismatch row %s" % row 
                    continue

                entry = dict(zip(headers, row))

                if entry["year"] != self.local_config["year"]:
                    #skip mismatched year
                    continue

                if len(entry["title"]) == 0:
                    print "skipping empty title row %s" % entry
                    continue

                if len(entry["proceedings_uri"]) == 0:
                    print "skipping empty proceedings row %s" % entry
                    continue

                expand_entry(entry)

                counter_paper.inc(entry["proceedings_uri"])
                id_paper = counter_paper.data[entry["proceedings_uri"]]
                uri_paper = "%s/paper-%02d" % (entry["proceedings_uri"], id_paper)
                uri_paper_author_list = "%s/paper-%02d/author_list" % (entry["proceedings_uri"], id_paper)
                #print json.dumps(entry, indent=4)
                #print uri_paper
                res_proceedings = URIRef(entry["proceedings_uri"])
                res_paper = URIRef(uri_paper)

                self.graph.add((res_paper, RDF.type, SWRC.InProceedings ))

                #part-of proceedings
                self.graph.add((res_paper, SWC.isPartOf, res_proceedings))
                self.graph.add((res_proceedings, SWC.hasPart, res_paper))

                #author
                author_data = DataIswc.parse_person_list(entry["author"])

                # if author_x_and != entry["author"]:
                #     print "--------------"
                #     print entry["author"]
                #     print author_x_and

                # author_x_and_y = re.sub("\s+"," ",author_x_and)
                # if author_x_and != author_x_and_y:
                #     print "????"
                #     print author_x_and
                #     print author_x_and_y

                self.graph.add((res_paper, SWRC.listAuthor, Literal(author_data["text"])))
                list_res_author = []
                for author in author_data["list"]:

                    author = self.get_final_name(author)

                    for res_author in self.create_list_named_entity(DataIswc.get_namespace(DataIswc.PREFIX_PERSON), author).values():
                        self.graph.add((res_author, RDF.type, FOAF.Person))

                        list_res_author.append(res_author)
                        self.graph.add((res_paper, SWRC.author, res_author))
                        self.graph.add((res_paper, FOAF.maker, res_author))
                        self.graph.add((res_author, FOAF.made, res_paper))

                res_paper_author_list = self.create_container(list_res_author, RDF.Seq, uri_paper_author_list)
                self.graph.add((res_paper, BIBO.authorList, res_paper_author_list))

                #simple properties
                self.create_triple_complex(
                    res_paper,
                    ["abstract", "keywords", "year", "pages", "title", "category",
                     "link_open_access", "link_publisher"],
                    entry)

                #cache
                self.map_name_res[entry["title"]] = res_paper


    def process_proceedings(self):
        filename = "{0}/data/source/iswc-all-proceedings.csv".format(
            self.global_config["home"])

        counter_paper = MyCounter()
        with open(filename) as f:
            csvreader = UnicodeReader(f)
            headers = csvreader.next()
            for row in csvreader:

                if len(row) != len(headers):
                    print "skipping mismatch row %s" % row
                    continue

                entry = dict(zip(headers, row))

                if entry["year"] != self.local_config["year"]:
                    #skip mismatched year
                    continue

                if len(entry["title"]) == 0:
                    print "skipping empty title row %s" % entry
                    continue

                if len(entry["proceedings_uri"]) == 0:
                    print "skipping empty proceedings_uri row %s" % entry
                    continue

                expand_entry(entry)

                uri_proceedings = self.expand_uri(entry["proceedings_uri"])
                uri_proceedings_editor_list = "%s/editor_list" % (uri_proceedings)
                uri_event = self.expand_uri(entry["event_uri"])

                #print json.dumps(entry, indent=4)
                #print uri_proceedings
                res_proceedings = URIRef(uri_proceedings)
                res_event = URIRef(uri_event)

                self.graph.add((res_proceedings, RDF.type, SWRC.Proceedings ))

                #relation to event
                self.graph.add((res_proceedings, SWC.relatedToEvent, res_event))
                self.graph.add((res_event, SWRC.hasRelatedDocument, res_proceedings))

                #editor
                if len(entry["editor"]) > 0:
                    self.graph.add((res_proceedings, SWRC.listEditor, Literal(entry["editor"])))
                    list_res_editor = []
                    for editor in entry["editor"].split(","):
                        editor = self.get_final_name(editor)

                        for res_editor in self.create_list_named_entity(DataIswc.get_namespace(DataIswc.PREFIX_PERSON), editor).values():
                            list_res_editor.append(res_editor)
                            self.graph.add((res_proceedings, SWRC.editor, res_editor))
                            self.graph.add((res_proceedings, FOAF.maker, res_editor))
                            self.graph.add((res_editor, FOAF.made, res_proceedings))

                    res_proceedings_editor_list = self.create_container(list_res_editor, RDF.Seq,
                                                                        uri_proceedings_editor_list)
                    self.graph.add((res_proceedings, SWC.editorList, res_proceedings_editor_list))


                #simple properties
                self.create_triple_complex(
                    res_proceedings,
                    ["title", "subtitle", "abstract", "keywords", "year", "pages", "publisher", "series", "volume",
                     "link_open_access", "link_publisher", "depiction"],
                    entry)


def main():
    # load config file
    #with open("config.json") as f:
    #    global_config = json.load( f)

    global_config = mu.mutil.config_load(file_home=__file__)
    print global_config

    dir_data_entity = os.path.join(global_config["home"], "data/entity/")
    dbpedia_api = DataIswc.dbpedia_api_load(dir_data_entity)

    try:
        for year in range(2001, 2015):
            #if year != 2014:
            #    continue

            local_config = {
                "year": "{}".format(year),
                "id-swsa": "ISWC{}".format(year),
                "id-dogfood": "iswc-{}".format(year),
                "id": "iswc-{}".format(year),
                "prefix_ns_map": {
                    "[ISWC]": "{}conference/iswc".format(DataIswc.NS_ROOT),
                    "[WORKSHOP]": "{}workshop".format(DataIswc.NS_ROOT),
                    "[ME]": "{}conference/iswc/{}".format(DataIswc.NS_ROOT, year),
                    "swc:": "http://data.semanticweb.org/ns/swc/ontology#"
                }
            }

            print "processing {}".format(local_config["id"])
            if year == 2007:
                local_config["id-dogfood"] = "iswc-aswc-2007"
                local_config["prefix_ns_map"]["[ME]"] = "{}conference/iswc-aswc/{}".format(
                    DataIswc.NS_ROOT, year)
                # elif year==2001:
            #     local_config["id-dogfood"]="swws-2001"
            #     local_config["prefix_ns_map"]["[ME]"] ="{}conference/iswc/{}".format(
            #         DataIswc.NS_ROOT,
            #         local_config["id-dogfood"])

            data = DataIswc(local_config, global_config, dbpedia_api)
            data.run_paper_x()

            if not year in range(2006, 2012):
                data = DataIswc(local_config, global_config, dbpedia_api)
                data.run()

        DataIswc.dbpedia_api_write(dbpedia_api)
    except:
        DataIswc.dbpedia_api_write(dbpedia_api)
        import traceback
        traceback.print_exc()
        raise

    print "All done"

if __name__ == "__main__":
    main()
