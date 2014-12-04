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
from mu.lib_unicode import UnicodeReader, UnicodeWriter
from binascii import b2a_hex


def hack_text(text):
    ret = text
    try:
        unicode(text)
        ret = ret.replace(u"´e",u"é")
        ret = ret.replace(u"¨o",u"ö")
        ret = ret.replace(u'\\"o',u"ö")
        ret = ret.replace(u'\\^o',u"ö")
        ret = ret.replace(u'\\"u',u"ü")
        ret = ret.replace(u"\\'e",u"é")
        ret = ret.replace(u"\\'a",u"á")

    except:
        pass

    return ret


import mustache_template
import pystache

def print_list_people_role(filename, list_people_role):

    for people in list_people_role:
        #print lib_data.json2text(people)
        print u'"{}",,,,"{}","{}","{}","{} ({})"'.format(people["Name"], people["Email"], people["Affiliation"], people["Country"], people["Role"], people["Track"])

    return

    template = mustache_template.people_csv
    list_people_role = lib_text.any2utf8(list_people_role)
    output = pystache.render(template, {"people":list_people_role})

    global_config = load_gloabl_config()

    print output

    filename = os.path.join(global_config["home"],"output", filename)
    with codecs.open(filename, "w","utf-8") as f:
        f.write(output)



def load_gloabl_config():
    filename = "config.json"
    filename = os.path.join(os.path.dirname(__file__), filename)
    with open(filename) as f:
        global_config = json.load(f)
    print global_config
    return global_config




def load_people_tex():
    global_config = load_gloabl_config()

    list_input = [
        {"filename": "8796Frontmatter_Preface_Organizers_KeynoteAbstracts.tex",
         },

    ]

    map_people = {}
    list_people_role = []
    set_organization = set()

    for input in list_input:
        filename = os.path.join( global_config["home"],"data", input["filename"])
        print filename
        with open(filename,'r') as f:
            section = None
            for line in f.read().split("\n"):
                if line.startswith("\section"):
                    section = line.replace("\\section*","")[1:-1]
                    print "\n"
                    print section

                if line.startswith("\\newpage"):
                    section = None

                if not section:
                    continue

                line = line.replace("\\noindent ", "")
                line = line.replace("\\\\", "")

                if line.startswith("\\"):
                    continue

                if not line:
                    continue


                if ("Committee" in section or "Reviewers" in section) and "Organizing" not in section:
                    line = hack_text(line)



                    role, track = section.split("--")
                    role = role.strip()
                    track = track.strip()
                    entry ={
                        "Role": role,
                        "Track": track,
                    }
                    if "," in line:
                        #print line
                        temp =  line.split(",")
                        entry["Name"] = temp[0]
                        entry["Affiliation"] = ",".join(temp[1:-1])
                        entry["Country"] = temp[-1]

                    else:
                        entry["Name"] = line

                    for k, v in entry.items():
                        entry[k] = v.strip()
                    #print entry
                    if role in ["Additional Reviewers"]:
                        print '"{}",,,"{} ({})"'.format( entry["Name"], role, track)
                    #print lib_data.json2text(entry)
                    list_people_role.append(entry)


def load_people_csv():
    with open("config.json") as f:
        global_config = json.load(f)
    print global_config

    list_input = [
        {"filename": "people.csv",
         },

    ]

    list_field=[
        "Paper",
        "Author",
        "Email",
        "Country",
        "Affiliation",
    ]

    list_item = []
    counter = collections.Counter()

    map_name_author = {}
    set_organization = set()
    list_people_role = []

    for input in list_input:
        filename = os.path.join( global_config["home"],"data", input["filename"])
        print filename
        with open(filename,'r') as f:
            csvreader = UnicodeReader(f)
            headers = csvreader.next()

            track = None
            for row in csvreader:
                if not row:
                    continue

                if row[0].startswith("##"):
                    track = row[0][2:]
                    print track , "---------------------------"
                    continue
                elif row[0].startswith("#"):
                    continue

                entry = dict(zip(headers, row))
                entry["Track"] = track
                entry["Role"] = "author"
                print entry

                #author
                author = entry["Author"]
                entry["Name"] = author


                if author in ["Xi Chen"]:
                    author = "{} {}".format(author,  entry["Email"] )

                if author in map_name_author:
                    author_info = map_name_author[author]
                else:
                    author_info = {}
                    author_info.update(entry)
                    map_name_author[author] = author_info
                    author_info["track_list"]= set(track)


                if entry["Email"] != author_info["Email"]:
                    print  author_info["Email"], author_info["Track"]
                    print  entry["Email"], entry["Track"]

                if entry["Affiliation"] != author_info["Affiliation"]:
                    print author_info["Affiliation"], author_info["Track"]
                    print entry["Affiliation"], entry["Track"]

                author_info.update(entry)
                author_info["track_list"].add(track)





                #affiliation
                organization = entry["Affiliation"]
                set_organization.add(organization)


                list_people_role.append(entry)


    print sorted(list(set_organization))

    filename = "person.json"
    filename = os.path.join(global_config["home"],"data", filename)
    print filename
#    with codecs.open(filename, "w","utf-8") as f:
#        f.write(lib_data.json2text(list_item))


    print_list_people_role("person_author.csv", list_people_role)


def load_people_web_txt():
    with open("config.json") as f:
        global_config = json.load(f)
    print global_config

    list_input = [
        {"filename": "people-web.txt",
         },

    ]


    for input in list_input:
        filename = os.path.join( global_config["home"],"data", input["filename"])
        print filename
        track =""
        role = ""
        with open(filename, 'r') as f:
            for line in f.read().split("\n"):
                line = line.strip()
                if len(line)==0:
                    continue

                if line.startswith("=="):
                    track = line[2:].strip()
                    print "-------------", line
                    continue
                elif line.startswith("#"):
                    role = line[1:].strip()
                    print "-------------", line
                    continue


                if "|" in line:
                    line, country = line.split("|")
                    country = country[1:-1]
                elif "," in line and track in ["Research Track"]:
                    line, country = line.rsplit(",",1)
                else:
                    country = ""

                if "," in line:
                    name, affiliation = line.split(",", 1)
                    print '"{}",,,,,"{}",{},,,{} ({})'.format( name.strip(), affiliation.strip(), country.strip(), role, track)
                else:
                    print line






if __name__ == "__main__":
   # load_people_web_txt()
   # load_people_tex()
    load_people_csv()
