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

import pystache

from iswc2014 import lib_data


template_event =u"""
<meta charset="utf-8">
ISWC 2014 Event (v3)

{{#events}}
    <div> {{day}}: {{start}}-{{end}}  {{name}} ( {{location}} ) ---- {{type}}  </div>
{{/events}}

ISWC 2014 Talks

{{#talks}}
    <div> {{day}}: {{start}}-{{end}}  {{name}} ( {{session_name}} )  </div>
{{/talks}}

"""

template_paper =u"""
<meta charset="utf-8">
ISWC 2014 Paper (v3)

<ol>
{{#articles}}
    <li>{{paper_id_x}} {{track}}  {{authors}}   {{author}}    {{title}}   {{link_open_access}}  </li>
{{/articles}}
</ol>


"""

template_person =u"""
<meta charset="utf-8">
ISWC 2014 Person (v3)

{{#contacts}}
    <div>{{id}}    {{name}}   {{affiliation}} {{holdsRole}} {{link_open_access}} </div>
{{/contacts}}


"""

template_paper_markdown =u"""
# {{title}}

{{#tracks}}
*  [{{title}}](#{{title}})
{{/tracks}}


{{#tracks}}

## <a name="{{title}}">{{title}}</a>
   {{#papers}}
1. <b>{{title}}</b>, {{author}}, [PDF]({{link_open_access}})
   {{/papers}}
{{/tracks}}

"""

def load_csv(filename, non_empty_field):
    ret = []
    with open(filename) as f:
        csvreader = UnicodeReader(f)
        headers = csvreader.next()
        for row in csvreader:
            if len(row) < len(headers):
                #print "skipping row %s" % row
                continue

            entry = dict(zip(headers, row))

            if not entry[non_empty_field]:
                continue

            ret.append(entry)
            print entry

    return ret


def csv2markdown(year):
    global_config = mu.mutil.config_load(file_home=__file__)
    print global_config

    local_config = {
        "year": "{}".format(year),
        "id": "iswc-{}".format(year),
    }


    #paper
    filename = "{0}/data/source/{1}-paper.csv".format( global_config["home"], local_config["id"])
    list_paper = load_csv(filename, "author")
    json_output = {"tracks":[],"title": "Open Access Preprint Papers in ISWC {} Proceedings".format(year) }

    map_track = {}

    for paper in list_paper:

        if paper["author"].startswith("#"):
            continue

        if not paper["link_open_access"]:
            continue

        track_title = paper["category"]
        if track_title in map_track:
            track = map_track[track_title]
        else:
            track = {"title":track_title, "papers":[]}
            map_track[track_title] = track
            json_output["tracks"].append(track)

        entry = {
            "title": paper["title"].strip(),
            "author": paper["author"].strip(),
            "abstract": paper["abstract"].strip(),
            "track" : paper["category"],
            "pages" : paper["pages"],
            "link_open_access" : paper["link_open_access"],
            "paper_id_x" : paper["paper_id_x"],
        }
        track["papers"].append(entry)


    #print lib_data.json2text(json_output)

    filename = "{0}/temp/{1}-github-proceeding-papers.json".format( global_config["home"], local_config["id"])
    with open(filename, "w") as f:
        f.write(lib_data.json2text(json_output))


    html_output = pystache.render(template_paper_markdown, json_output)
    filename = "{0}/temp/{1}-github-readme.md".format( global_config["home"], local_config["id"])
    with open(filename, "w") as f:
        f.write(html_output)



def csv2json(year):
    global_config = mu.mutil.config_load(file_home=__file__)
    print global_config

    local_config = {
        "year": "{}".format(year),
        "id": "iswc-{}".format(year),
    }


    #paper-author
    map_role_author={}

    filename = "{0}/data/source/{1}-paper.csv".format( global_config["home"], local_config["id"])
    list_paper = load_csv(filename, "author")

    for paper in list_paper:
        if paper["author"] :

            role = "Author of {}".format(paper["category"])
            if role not in map_role_author:
                map_role_author[role]= set()

            for x in paper["author"].replace(" and ", ",").split(","):
                x = x.strip()
                map_role_author[role].add(x)

    for x in map_role_author["Author of Industry Track Paper"]:
        print x

    #person
    filename = "{0}/data/source/{1}-person.csv".format( global_config["home"], local_config["id"])
    list_person = load_csv(filename, "name")
    map_name_person = {}




    for person in list_person:
        entry = {
            "name": person["name"].strip(),
        }

        for field in ["email","homepage"]:
            if person[field]:
                entry[field] =  person[field].strip()

        if person["organization"]:
            entry["affiliation"] = []
            for x in person["organization"].split(";"):
                x =x.strip()
                entry["affiliation"].append(x)


        key = person["name"].strip()
        if key in map_name_person:
            info = map_name_person[key]
            info.update(entry)
            if person["role_label"]:
                lib_data.list_append_unique(info["holdsRole"], person["role_label"])
        else:
            info = {"holdsRole":[]}
            for role in map_role_author:
                if key in map_role_author[role]:
                    lib_data.list_append_unique(info["holdsRole"], role)

            info.update(entry)
            if person["role_label"]:
                lib_data.list_append_unique(info["holdsRole"], person["role_label"])
            info["id"] = len(map_name_person)+1
            map_name_person[key] = info


    json_output = {"contacts": sorted(map_name_person.values(), key=lambda x: x["id"]) }

    filename = "{0}/data/www/{1}-mobile-person.json".format( global_config["home"], local_config["id"])
    with open(filename, "w") as f:
        f.write(lib_data.json2text(json_output))

    html_output = pystache.render(template_person, json_output)
    filename = "{0}/temp/{1}-mobile-person.html".format( global_config["home"], local_config["id"])
    with open(filename, "w") as f:
        f.write(html_output)






    #paper
    filename = "{0}/data/source/{1}-paper.csv".format( global_config["home"], local_config["id"])
    list_paper = load_csv(filename, "author")
    json_output = {"articles":[]}
    map_name_paper = {}

    for paper in list_paper:

        if paper["author"].startswith("#"):
            continue

        entry = {
            "title": paper["title"].strip(),
            "author": paper["author"].strip(),
            "authors": [],
            "abstract": paper["abstract"].strip(),
            "track" : paper["category"],
            "pages" : paper["pages"],
            "link_open_access" : paper["link_open_access"],
            "paper_id_x" : paper["paper_id_x"],
        }

        entry["id"] = len(json_output["articles"])+1

        json_output["articles"].append(entry)
        map_name_paper[paper["title"]] = entry

        for x in paper["author"].replace(" and ", ",").split(","):
            x = x.strip()
            entry["authors"].append( map_name_person[x]["id"])

    filename = "{0}/data/www/{1}-mobile-paper.json".format( global_config["home"], local_config["id"])
    with open(filename, "w") as f:
        f.write(lib_data.json2text(json_output))

    html_output = pystache.render(template_paper, json_output)
    filename = "{0}/temp/{1}-mobile-paper.html".format( global_config["home"], local_config["id"])
    with open(filename, "w") as f:
        f.write(html_output)







    #event
    filename = "{0}/data/source/{1}-event.csv".format( global_config["home"], local_config["id"])
    list_event = load_csv(filename, "room")
    json_output = {"events":[], "talks":[]}
    map_event_id = {}


    for event in list_event:
        entry = {
            "day": event["start"][8:10],
            "start": event["start"][11:16],
            "end": event["end"][11:16],
            "name" : event["label"],
            "type" : event["event_type"],
            "location" : event["room"],
        }
        if event["event_type"] in ["TalkEvent"]:
            entry["id"] = len(json_output["talks"])+1
            json_output["talks"].append(entry)

            entry["event"]= map_event_id[event["super_event_uri"]]
            entry["paper"]= map_name_paper[event["label"]]["id"]

        else:
            entry["id"] = len(json_output["events"])+1
            json_output["events"].append(entry)

            p = "event_uri"
            if p in event:
                map_event_id[event[p]] = entry["id"]


    filename = "{0}/data/www/{1}-mobile-event.json".format( global_config["home"], local_config["id"])
    with open(filename, "w") as f:
        f.write(lib_data.json2text(json_output))

    html_output = pystache.render(template_event, json_output)
    filename = "{0}/temp/{1}-mobile-event.html".format( global_config["home"], local_config["id"])
    with open(filename, "w") as f:
        f.write(html_output)




if __name__ == "__main__":
    year = 2014
    csv2markdown(year)
    csv2json(year)