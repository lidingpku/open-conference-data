# -*- coding: utf-8 -*-
import rdflib
import sys
#print sys.getdefaultencoding()
reload(sys)
sys.setdefaultencoding("utf-8")
#print sys.getdefaultencoding()
import unicodedata
from rdflib.namespace import RDF, FOAF, RDFS, OWL, DC, DCTERMS, SKOS
from rdflib import URIRef, Literal, Namespace, XSD
import json
from mu.lib_unicode import UnicodeReader, UnicodeWriter
from mu.lib_format import UtilCsv
import re
import os
import hashlib
import json
import datetime
import jsontemplate
from pkg_resources import resource_string, resource_listdir
import codecs
from  lib_ext import *
import shutil


class IswcDirect:
    """ this class simply load the iswc csv data and generate cool stuff.
        Starting from RDF is less effective then directly from CSV.
    """
    NS_ROOT = "http://data.semanticweb.org/"

    @staticmethod
    def create_local_config(year):
        local_config = {
            "year": "{}".format(year),
            "id-swsa": "ISWC{}".format(year),
            "id-dogfood": "iswc-{}".format(year),
            "id": "iswc-{}".format(year),
            "prefix_ns_map": {
                "[ISWC]": "{}conference/iswc".format(IswcDirect.NS_ROOT),
                "[WORKSHOP]": "{}workshop".format(IswcDirect.NS_ROOT),
                "[ME]": "{}conference/iswc/{}".format(IswcDirect.NS_ROOT, year),
                "swc:": "http://data.semanticweb.org/ns/swc/ontology#"
            }
        }
        return local_config


    @staticmethod
    def debug(msg):
        print("[IswcDirect]{}".format(msg))

    @staticmethod
    def gen_conf_organizer(global_config, local_config):
        dir_home = global_config["home"]
        id_data = local_config["id"]
        id_html = "gen_conf_organizer"

        #load data
        filename_input = "{0}/data/source/{1}-person.csv".format(
            dir_home,
            id_data)

        data_json = UtilCsv.csv2json(filename_input)
        IswcDirect.debug("load {} entries from [{}]".format(len(data_json), filename_input))


        #only keep organizer
        data_json_new = []
        for entry in data_json:
            if entry["role_event"] == "[ME]" and entry["role_type"] == "swc:Chair":
                data_json_new.append(entry)

        data_json = data_json_new
        IswcDirect.debug("keep {} persons for conf organization".format(len(data_json)))

        #prepare json for templating
        data_for_jsont = {"roles": []}
        role_prev = None
        for entry in data_json:
            if None == role_prev or entry["role_label"] != role_prev["label"]:
                role_prev = {"label": entry["role_label"],
                             "persons": []}
                data_for_jsont["roles"].append(role_prev)

            #copy person metadata
            person = {}
            for p in ["name", "homepage", "organization", "country"]:
                person[p] = entry[p]

            #add person uri
            person["uri"] = "#{}".format(create_ascii_localname(person["name"], escape=True))

            role_prev["persons"].append(person)


        #print json.dumps(data_for_jsont, indent=4)
        filename_json = "%s/data/www/%s-%s.json" % (
            dir_home,
            id_data,
            id_html)
        with codecs.open(filename_json, "w", "utf-8") as f:
            json.dump(data_for_jsont, f, indent=4)

        #write html
        filename_html = "%s/data/www/%s-%s.html" % (
            dir_home,
            id_data,
            id_html)
        json_template = resource_string('resources.files', '{}.jsont'.format(id_html))
        content = jsontemplate.expand(json_template, data_for_jsont)
        with codecs.open(filename_html, "w", "utf-8") as f:
            f.write(u'\ufeff')
            f.write(content)
        IswcDirect.debug("write to file [{}]".format(filename_html))


    @staticmethod
    def gen_conf_paper(global_config, local_config):
        dir_home = global_config["home"]
        id_data = local_config["id"]
        id_html = "gen_conf_paper"

        #load data
        filename_input = "{0}/data/source/{1}-paper.csv".format(
            dir_home,
            id_data)

        data_json = UtilCsv.csv2json(filename_input)
        IswcDirect.debug("load {} entries from [{}]".format(len(data_json), filename_input))


        #prepare json for templating
        p_group = "tracks"
        p_item = "papers"

        data_for_jsont = {p_group: []}
        prev = None
        for entry in data_json:
            x_proceedings = entry["proceedings_uri"].split("/")[-1]
            if x_proceedings not in ["proceedings", "proceedings-1", "proceedings-2"]:
                #skip non conference proceedings paper
                continue

            if None == prev or entry["category"] != prev["label"]:
                prev = {"label": entry["category"],
                        p_item: []}
                data_for_jsont[p_group].append(prev)

                #copy entry_new metadata
            entry_new = {}
            for p in ["author", "title", "pages", "link_open_access", "abstract"]:
                entry_new[p] = entry[p]

            # link local
            entry_new["link_local"] = "{}".format(entry_new["link_open_access"].split("/")[-1])

            # link local
            if len(entry_new["abstract"]) == 0:
                entry_new["abstract"] = "TBA"

            if entry["pages"]:
                entry_new['page_start'] = entry["pages"].split("-")[0]


            #add uri
            entry_new["uri"] = "#{}".format(create_ascii_localname(entry_new["title"], escape=True))

            entry_new['author_latex'] = unicode2latex(entry["author"])
            entry_new['authors'] = []
            for x in entry["author"].split(","):
                person = {"name": x.strip()}
                person["uri"] = "#{}".format(create_ascii_localname(person["name"], escape=True))
                entry_new['authors'].append(person)

            prev[p_item].append(entry_new)

        filename_json = "%s/data/www/%s-%s.json" % (
            dir_home,
            id_data,
            id_html)
        with codecs.open(filename_json, "w", "utf-8") as f:
            json.dump(data_for_jsont, f, indent=4)

        #write html
        filename_html = "%s/data/www/%s-%s.html" % (
            dir_home,
            id_data,
            id_html)
        json_template = resource_string('resources.files', '{}.jsont'.format(id_html))
        content = jsontemplate.expand(json_template, data_for_jsont)
        with codecs.open(filename_html, "w", "utf-8") as f:
            f.write(u'\ufeff')
            f.write(content)
        IswcDirect.debug("write to file [{}]".format(filename_html))

        #write index-usb
        filename_html = "%s/data/paper/iswc-2013/index.html" % (
            dir_home)
        json_template = resource_string('resources.files', '{}.jsont'.format("gen_open_access_index"))
        content = jsontemplate.expand(json_template, data_for_jsont)
        with codecs.open(filename_html, "w", "utf-8") as f:
            f.write(u'\ufeff')
            f.write(content)
        IswcDirect.debug("write to file [{}]".format(filename_html))

    @staticmethod
    def create_pretty_filename(title):
        temp = title
        temp = temp.lower()
#        temp = temp.split(":")[0]
        temp = re.sub('[^a-zA-Z0-9]+', ' ', temp)
        list_word = temp.split(" ")
#        end_index = min(len(list_word), 10)
#        temp = "-".join(list_word[:end_index])
        temp = "-".join(list_word)
        return temp

    @staticmethod
    def gen_open_access_index(global_config, local_config):
        dir_home = global_config["home"]
        id_data = local_config["id"]
        id_html = "gen_open_access_index"

        data_all = []

        list_filename_input = []
        #        list_filename_input.append( "{0}/data/source/iswc-all-papers.csv".format(
        #            dir_home))
        list_filename_input.append("{0}/data/source/iswc-2013-paper.csv".format(
            dir_home))

        for filename_input in list_filename_input:

            #load data
            data_json = UtilCsv.csv2json(filename_input)
            IswcDirect.debug("load {} entries from [{}]".format(len(data_json), filename_input))


            #prepare json for templating
            p_group = "tracks"
            p_item = "papers"

            data_for_jsont = {p_group: []}
            prev = None
            for entry in data_json:
                if len(entry['title'])==0:
                    continue

                if None == prev or entry["proceedings_uri"] != prev["proceedings_uri"]:
                    prev = {"label": entry["category"],
                            "proceedings_uri": entry["proceedings_uri"],
                            p_item: []}
                    data_for_jsont = {p_group: []}

                    data_all_entry = {"label": "-".join([entry["year"], entry["proceedings_uri"].split("/")[-1]]),
                                      "data": data_for_jsont
                    }
                    data_all.append(data_all_entry)
                    data_for_jsont[p_group].append(prev)

                if None == prev or entry["category"] != prev["label"]:
                    prev = {"label": entry["category"],
                            "proceedings_uri": entry["proceedings_uri"],
                            p_item: []}
                    data_for_jsont[p_group].append(prev)

                    #copy entry_new metadata
                entry_new = {}
                for p in ["author", "title", "pages", "link_open_access", "abstract"]:
                    entry_new[p] = entry[p]

                # link local
                entry_new["link_local"] = entry_new["link_open_access"].split("/")[-1]

                #print '---->', entry_new['title']

                #if len(entry_new["link_open_access"])>0:
                #    id_data = entry_new["link_open_access"].split("/")[-2]
                #    dir_paper = os.path.join(dir_home, "data/paper/{}".format(id_data))
                #
                #    temp_filename = entry_new["link_open_access"].split("/")[-1]
                #    #print temp_filename
                #    temp_id, temp_ext = temp_filename.split('.')
                #    pretty_name = IswcDirect.create_pretty_filename(entry_new['title'])
                #    entry_new["link_local"] = '{}-{}.{}'.format(temp_id, pretty_name, temp_ext)
                #    print "{}".format(entry_new["link_local"])
                #
                #    filename_old = os.path.join(dir_paper, temp_filename)
                #    #print os.path.exists(filename_old)
                #    filename_new = os.path.join(dir_paper, entry_new["link_local"])
                #    #print os.path.exists(filename_new)
                #    os.rename(filename_old, filename_new)


                # link local
                if len(entry_new["abstract"]) == 0:
                    entry_new["abstract"] = "TBA"

                if entry["pages"]:
                    entry_new['page_start'] = entry["pages"].split("-")[0]

                #add uri
                entry_new["uri"] = "#{}".format(create_ascii_localname(entry_new["title"], escape=True))

                entry_new['author_latex'] = unicode2latex(entry["author"])
                entry_new['authors'] = []
                for x in entry["author"].split(","):
                    person = {"name": x.strip()}
                    person["uri"] = "#{}".format(create_ascii_localname(person["name"], escape=True))
                    entry_new['authors'].append(person)

                prev[p_item].append(entry_new)


        filename_input = list_filename_input[0]
        head, tail = os.path.split(filename_input)
        filename_output = "{}/data/open_access/{}".format(
            dir_home,
            tail)
        shutil.copyfile(filename_input, filename_output)

        for data_all_entry in data_all:
            data_for_jsont = data_all_entry["data"]
            path = data_all_entry["label"]

            #print json.dumps(data_for_jsont, indent=4)

            #write index-usb
            filename_html = "%s/data/open_access/%s/index.html" % (
                dir_home,
                path)
            json_template = resource_string('resources.files', '{}.jsont'.format(id_html))
            content = jsontemplate.expand(json_template, data_for_jsont)
            if os.path.exists(os.path.dirname(filename_html)):
                with codecs.open(filename_html, "w", "utf-8") as f:
                    f.write(u'\ufeff')
                    f.write(content)
                IswcDirect.debug("write to file [{}]".format(filename_html))




    @staticmethod
    def gen_schedule(global_config):

        def update_row(entry):
            map_data ={
                "SMAM2013":"[WORKSHOP]/smam/2013",
                "SemStats2013":"[WORKSHOP]/semstats/2013",
                "OrdRing2013":"[WORKSHOP]/ordring/2013",
                "DeRiVE2013":"[WORKSHOP]/derive/2013",
                "LISC2013":"[WORKSHOP]/lisc/2013",
                "COLD2013":"[WORKSHOP]/cold/2013",
                "WOP2013":"[WORKSHOP]/wop/2013",
                "SSN2013":"[WORKSHOP]/ssn/2013",
                "OM-2013":"[WORKSHOP]/om/2013",
                "SSWS2013":"[WORKSHOP]/ssws/2013",
                "URSW2013":"[WORKSHOP]/ursw/2013",
                "CrowdSem":"[WORKSHOP]/crowdsem/2013",
                "DBpedia&NLP2013":"[WORKSHOP]/dbpedia-nlp/2013",
                "LD4IE":"[WORKSHOP]/ld4ie/2013",
                "SML2OD2013":"[WORKSHOP]/sml2od/2013",
                "PRIVON2013":"[WORKSHOP]/provon/2013",
                "WaSABi":"[WORKSHOP]/wasabi/2013",
                "Hands-onGuidetoLinkedDataApplications":"[ME]/tutorial-2",
                "BigDataManagement":"[ME]/tutorial-1",
                "LinkedDataforWebScaleInformationExtraction":"[ME]/tutorial-3",
                "MicrotaskCrowdsourcingtoSolveSemanticWebProblems":"[ME]/tutorial-4",
                "ModellingOntologiesVisually":'[ME]/tutorial-5',
                "RelationalDatabasetoRDF":"[ME]/tutorial-6",
                "StreamReasoningforLinkedData":'[ME]/tutorial-7',
                "TheMobileSemanticWeb":"[ME]/tutorial-8",
                "TheWebofThings":'[ME]/tutorial-9',
            }
            for key,value in entry.items():
                for k,v in map_data.items():
                    if value==k:
                        temp = v
                    else:
                        temp = value.replace(k,v+'/')

                    if temp != value:
                        temp = temp.replace("Session","session")
                        entry[key] = temp

        filename = "%s/data/work/iswc-2013/raw/iswc-paper.json" % (global_config["home"])
        with open(filename) as f:
            json_data_paper = json.load(f)

        filename = "%s/data/work/iswc-2013/raw/iswc-session.json" % (global_config["home"])
        with open(filename) as f:
            json_data_session = json.load(f)

        filename = "%s/data/work/iswc-2013/raw/iswc-schedule.json" % (global_config["home"])
        with open(filename) as f:
            json_data_schedule = json.load(f)

        for day in json_data_schedule:
            for slot in day["slots"]:
                temp_time = slot['time'].split("-")
                if len(temp_time)!=2:
                    print '----'
                    print temp_time
                    continue

                x_datetime = "{} {}".format(day['date'], temp_time[0].strip())
                dt_begin = datetime.datetime.strptime(x_datetime, "%d/%m/%Y %H:%M")
                x_datetime = "{} {}".format(day['date'], temp_time[1].strip())
                dt_end = datetime.datetime.strptime(x_datetime, "%d/%m/%Y %H:%M")

                for session in slot['sessions']:
                    print "======="
                    session['session'] = "".join(session['session'].split(" "))
                    if session['session'] not in json_data_session:
                        print '----'
                        print session['session']
                        continue

                    session_data = json_data_session[session['session']]

                    row = {}
                    fields = ['event_id','super_event', 'order', 'type', 'label', 'dt_begin','dt_end','tzid','room']
                    row['event_id'] = session['session']
                    temp_list_word = session_data['s_title'].split(' ')
                    if len(temp_list_word)>2 and "Session" == temp_list_word[-2]:
                        row['super_event'] = ''.join(temp_list_word[:-2])
                    else:
                        row['super_event'] = '[TODO]'
                    row['label'] = session_data['s_title']
                    row['dt_begin'] = dt_begin.isoformat()
                    row['dt_end'] = dt_end.isoformat()
                    row['type'] = 'SessionEvent'
                    row['tzid'] = 'Australia/Sydney'
                    row['room'] = session['room']
                    row['order'] = ''

                    update_row(row)


                    row_x =[]
                    for key in fields:
                        row_x.append(row[key])
                    print u'\t'.join(row_x)

                    order_in_session= 0
                    for submission in session_data["submissions"]:
                        order_in_session += 1
                        paper_data = json_data_paper[submission]
                        row = {}
                        fields = ['event_id','super_event', 'order', 'type', 'label']
                        row['event_id'] = ''
                        row['super_event'] = session['session']
                        row['order'] = '{}'.format(order_in_session)
                        row['type'] = 'TalkEvent'
                        row['label'] = paper_data['title']

                        update_row(row)

                        row_x =[]
                        for key in fields:
                            row_x.append(row[key])
                        print u'\t'.join(row_x)

def main():
    # load config file
    with open("config.json") as f:
        global_config = json.load(f)

    local_config = IswcDirect.create_local_config(2013)

    #    IswcDirect.gen_conf_organizer(global_config, local_config)
    #IswcDirect.gen_conf_paper(global_config, local_config)
    #IswcDirect.gen_open_access_index(global_config, local_config)

    IswcDirect.gen_schedule(global_config)

if __name__ == "__main__":
    main()
