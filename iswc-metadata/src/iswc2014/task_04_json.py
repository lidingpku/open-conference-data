# -*- coding: utf-8 -*-

import json
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


from mu.lib_unicode import UnicodeReader, UnicodeWriter
from mu.lib_format import UtilString
from mu.lib_dbpedia import DbpediaApi
import collections
import re
import glob
import shutil
import codecs
import lib_pdf, lib_text, lib_data


from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTChar

from lib_ext import latex2unicode
import json
import os
import codecs
import glob
import re


def load_gloabl_config():
    filename = "config.json"
    filename = os.path.join(os.path.dirname(__file__), filename)
    with open(filename) as f:
        global_config = json.load(f)
    print global_config
    return global_config

def load_paper_json():
    global_config = load_gloabl_config()



    filename = "paper-excel.json"
    filename  = os.path.join(global_config["home"],"output", filename)
    with open(filename, 'r') as f:
        content = f.read()
        list_paper_excel = lib_data.text2json(content)
    print len(list_paper_excel)
    map_paper_excel = {}
    map_paper_excel_no = {}
    for paper  in list_paper_excel:
        map_paper_excel[str(paper["paper_id"])] = paper

        map_paper_excel_no[str(paper["paper_no"])] = paper


    map_name_session = {}



    filename = "paper-industry.json"
    filename = os.path.join(global_config["home"],"output", filename)
    with open(filename, 'r') as f:
        content = f.read()
        list_paper_industry = lib_data.text2json(content)

    set_session_name = set()
    for paper in list_paper_industry:
        paper_id = str(paper["paper_id"])
        map_paper_excel[paper_id] = paper

        session_name = paper["session_name"]

        set_session_name.add(session_name)

        default_session_id = 100 + len(set_session_name)
        default_entry = {
            "session_time": paper["session_time"],
            "session_name": session_name,
            "session_id" : default_session_id,
            "session_index" : default_session_id,

        }

        entry = map_name_session.get(session_name, default_entry)

        map_name_session[session_name]=entry

        paper_list = entry.get("paper_list",[])
        lib_data.list_append_unique(paper_list, paper_id)
        entry["paper_list"] =paper_list
        entry["paper_count"]= len(entry["paper_list"])


    filename = "paper-pdf.json"
    filename  = os.path.join(global_config["home"],"output", filename)
    with open(filename, 'r') as f:
        content = f.read()
        list_paper_pdf = lib_data.text2json(content)

    print len(list_paper_pdf)
    map_paper_pdf = {}
    for paper in list_paper_pdf:
        map_paper_pdf[str(paper["paper_id"])] = paper





    filename = "session.csv"
    filename  = os.path.join(global_config["home"],"data", filename)
    map_paper_session = {}

    with open(filename,'r') as f:
        csvreader = UnicodeReader(f)
        headers = csvreader.next()
        session_no = None
        session_name = None
        session_index = 1
        for row in csvreader:
            entry = dict(zip(headers, row))

            if entry.get("Paper no."):
                entry["session_no"] = session_no
                entry["session_id"] = int(session_no.split(" ")[-1])
                entry["session_name"] = session_name
                entry["session_index"] = session_index
                session_index+=1
                map_paper_session[entry["Paper no."]]=entry

                map_name_session[session_name]=entry
            else:
                session_no = entry["Session no"]
                session_name = entry["Title"].strip()
                session_index = 1


    print len(map_paper_session)




    filename = "event.csv"
    filename  = os.path.join(global_config["home"],"data", filename)
    map_event_session  = {}

    with open(filename,'r') as f:
        csvreader = UnicodeReader(f)
        headers = csvreader.next()
        for row in csvreader:
            if row[0].startswith("#"):
                continue

            entry = dict(zip(headers, row))

            print entry

            event_start, event_end = entry["Time"].split("-")
            event_day = entry["day"]

            for k,v in entry.items():
                if k in ["Time","day"]:
                    continue
                if v:
                    event_id = (len(map_event_session)+1)

                    event = {
                        "day":event_day,
                        "start":event_start.strip(),
                        "end": event_end.strip(),
                        "name": v.strip(),
                        "location": k,
                        "id": event_id,
                    }

                    if "Session" in v or "Industry Track:" in v:
                        session_name = v.replace("Session:","")
                        session_name = session_name.replace("Industry Track:","")

                        session_name = re.sub("\([^\)]+\)","", session_name)
                        session_name = session_name.strip()

                        if session_name not in map_name_session:
                            print session_name

                        assert session_name in map_name_session

                        event["session_name"] = session_name

                    map_event_session[event_id] = event

    print len(map_paper_session)



    return map_paper_excel, map_paper_excel_no, map_paper_pdf, map_paper_session, map_name_session, map_event_session


def create_json():
    map_paper_excel, map_paper_excel_no, map_paper_pdf, map_paper_session, map_name_session, map_event_session = load_paper_json()


    ret = {}
    #event_index
    list_event = sorted(map_event_session.values(), key=lambda event: event["id"])
    #print lib_data.json2text(list_session)
    ret["events"]= list_event

    map_session_event = {}
    for event in map_event_session.values():
        if "session_name" in event:
            map_session_event[event["session_name"]] = event



    #session_index
    map_session = {}
    for paper in sorted(map_paper_session.values(), key=lambda paper: paper["session_index"]):
        session_id = paper["session_id"]
        session_info = map_session.get(session_id, lib_data.json_update({},paper, ["session_no","session_name","session_id"]))
        map_session[session_id] =session_info

        paper_no = paper["Paper no."]
        paper_id = map_paper_excel_no[paper_no]['paper_id']
        paper_list = session_info.get("paper_list",[])
        lib_data.list_append_unique(paper_list, paper_id)
        session_info["paper_list"] =paper_list
        session_info["paper_count"]= len(session_info["paper_list"])


    list_session = map_session.values()
    for session in map_name_session.values():
        if "paper_list" in session:
            list_session.append(session)

    list_session = sorted(list_session, key=lambda paper: paper["session_id"])

    #print lib_data.json2text(list_session)
    ret["sessions"]= list_session

    #Track_index
    map_track = {}
    TRACK_MAP=[
        {"track_id":"In Use", "track_name":"In Use Track", "category": "Semantic Web In Use Track Paper"},
        {"track_id":"RDBS", "track_name":"Replication, Benchmark, Data and Software  Track","category": "Replication, Benchmark, Data and Software Track Paper"},
        {"track_id":"Research", "track_name":"Research Track","category": "Research Track Paper"},
        {"track_id":"DC", "track_name":"Doctoral Consortium", "category":"Doctoral Consortium Paper"},
        {"track_id":"Industry", "track_name":"Industry Track","category": "Industry Track Paper"},
    ]

    for paper in map_paper_excel.values():
        category = paper["category"]
        track = map_track.get(category, {"category": category})
        map_track[category]=track

        paper_id = paper['paper_id']
        paper_list = track.get("paper_list",[])
        lib_data.list_append_unique(paper_list, paper_id)
        track["paper_list"] = sorted(paper_list)

    print lib_data.json2text(map_track.keys())

    for track in TRACK_MAP:
        if track["category"] in map_track:
            track["paper_list"]= map_track[track["category"]]["paper_list"]
            track["paper_count"]= len(track["paper_list"])

    ret["tracks"] = TRACK_MAP
    #print lib_data.json2text(TRACK_MAP)

    #map_paper_id2info
    for paper_id, paper in map_paper_excel.items():
        if paper_id.startswith("industry"):
            continue

        paper_pdf = map_paper_pdf.get(paper_id)

        lib_data.json_update(paper, paper_pdf, ["keywords", "abstract","number_of_pages"])
        if "pages" in paper:
            end_page = int(paper["start_page"])+ paper_pdf["number_of_pages"] - 1
            paper["pages"]= "{}-{}".format(paper["start_page"], end_page)

    list_paper = sorted(map_paper_excel.values(), key=lambda paper: paper["paper_id"])

    ret["papers"] = list_paper


    list_talk = []
    for session_info in ret["sessions"]:
        session_name = session_info["session_name"]
        start_diff = 0
        for paper_id in session_info["paper_list"]:
            paper_info = map_paper_excel[paper_id]

            event = map_session_event[session_name]
            if "Regular Talks" in session_name:
                diff_len = 15
            elif "Pechakucha" in session_name:
                diff_len = 10
            elif paper_info["paper_no"].endswith("*"):
                diff_len= 10
            else:
                diff_len= 20



            talk = {
                "day": event["day"],
                "start": time_add(event["start"], start_diff),
                "end": time_add(event["start"], start_diff+diff_len),
                "event": event["id"],
                "paper": paper_id,
                "paper_title": paper_info["title"],
                "paper_author": paper_info["author"],
                "id": paper_id,
            }
            print talk

            list_talk.append(talk)

            start_diff +=diff_len

    ret["talks"] = list_talk



    print lib_data.json2text(ret)

    return ret


def time_add(str_time, minute_diff):
    hour, minute = str_time.split(":")
    hour = int(hour)
    minute = int(minute)
    if minute_diff+minute <60:
        return "%d:%02d" % (hour, minute+minute_diff)
    else:
        return "%d:%02d" % (hour+(minute+minute_diff)/60, (minute+minute_diff)%60)



def validate_data():
    map_paper_excel, map_paper_excel_no, map_paper_pdf, map_paper_session, map_name_session, map_event_session = load_paper_json()

    for paper_id, paper in map_paper_excel.items():
        paper_pdf = map_paper_pdf.get(paper_id)
        if paper_pdf is None:
            print json.dumps(paper, indent=4)
            continue

        for p in ["title","author"]:
            v1 = paper[p]
            if p =="author":
                v1 = v1.replace(" and ",",")
            v1 = re.sub("\s*,\s*",",",v1)

            v2 = paper_pdf[p]
            v2 = re.sub("\s*,\s*",",",v2)
            if v1 !=v2:
                print "-------{}--{}---".format(p, paper_id)
                print v1
                print v2, "----pdf"
                #print json.dumps(paper_pdf,indent=4)
                #print json.dumps(paper,indent=4)



def validate_data2():
    map_paper_excel, map_paper_excel_no, map_paper_pdf, map_paper_session, map_name_session, map_event_session = load_paper_json()
    for paper_no, paper in map_paper_excel_no.items():
        paper_session = map_paper_session.get(paper_no)
        if paper_session is None:
            print json.dumps(paper,indent=4)

        #if paper["title"] != paper_pdf["title"]:
          #  print json.dumps(paper_pdf,indent=4)
          #  print json.dumps(paper,indent=4)

import mustache_template
import pystache
def render_json(data):
    global_config = load_gloabl_config()


    filename = "iswc2014-data.json"
    filename = os.path.join(global_config["home"],"output", filename)
    with codecs.open(filename, "w","utf-8") as f:
        f.write(lib_data.json2text(data))



    for xtype in ["events","talks"]:
        filename = "iswc2014-data-{}.json".format(xtype)
        filename = os.path.join(global_config["home"],"output", filename)
        with codecs.open(filename, "w","utf-8") as f:
            temp = {xtype: data[xtype]}
            f.write(lib_data.json2text(temp))





    map_paper = {}
    for paper in data["papers"]:
        map_paper [paper["paper_id"]]=paper

    map_talk = {}
    for talk in data["talks"]:
        map_talk[talk["id"]]=talk

    map_session = {}
    for session in data["sessions"]:
        list_paper_in_session = []
        for paper_id in session["paper_list"]:
            paper = map_paper[paper_id]
            list_paper_in_session.append(paper)
        session["paper_all"]= list_paper_in_session

        map_session[session["session_name"]] = session

    for event in data["events"]:
        list_paper_in_session = []
        if "session_name" in event and event["session_name"] in map_session:
            session = map_session[event["session_name"]]
            event.update(session)
            for paper_id in session["paper_list"]:
                paper = map_paper[paper_id]
                talk = map_talk[paper_id]
                paper.update(talk)
                list_paper_in_session.append(paper)
            event["talk_all"]= list_paper_in_session

    #dc, industry
    for track_index in [3,4]:
        track = data['tracks'][track_index]
        list_paper = []
        map_session = {}

        for paper_id in track["paper_list"]:
            paper = map_paper[paper_id]
            if "session_name" in paper:
                session_name = paper["session_name"]
                map_session[session_name] = map_session.get(session_name, lib_data.json_update({"paper_all":[]}, paper, ["session_name", "session_time"]))
                map_session[session_name]["paper_all"].append(paper)
                map_session[session_name]["paper_count"]= len(map_session[session_name]["paper_all"])
            else:
                list_paper.append(paper)


        section_id = "track_{}".format(track['track_id'])
        if list_paper:
            data[section_id] = list_paper
        else:
            data[section_id] = sorted(map_session.values(), key=lambda session: session["session_time"])




    filename = "iswc2014-data-expand.json"
    filename = os.path.join(global_config["home"],"output", filename)
    with codecs.open(filename, "w","utf-8") as f:
        f.write(lib_data.json2text(data))



    template = mustache_template.program2
    output = pystache.render(template, data)



    filename = "iswc2014-program.htm"
    filename = os.path.join(global_config["home"],"output", filename)
    with codecs.open(filename, "w","utf-8") as f:
        f.write(output)




    template = mustache_template.paper_csv
    output = pystache.render(template, data)

    filename = "iswc2014-paper-abstract.csv"
    filename = os.path.join(global_config["home"],"output", filename)
    with codecs.open(filename, "w","utf-8") as f:
        f.write(output)




    template = mustache_template.event_tsv
    output = pystache.render(template, data)
    output = output.replace("T01","T1")
    output = output.replace("T02","T2")
    output = output.replace("&amp;","&")
    output = output.replace(" (*)","")
    output = output.replace(" (**)","")

    filename = "iswc2014-event.tsv"
    filename = os.path.join(global_config["home"],"output", filename)
    with codecs.open(filename, "w","utf-8") as f:
        f.write(output)

if __name__ == "__main__":
    data = create_json()
    render_json(data)

    validate_data()