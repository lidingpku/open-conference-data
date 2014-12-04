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
from binascii import b2a_hex

def load_paper_json():
    filename = "config.json"
    filename = os.path.join(os.path.dirname(__file__), filename)
    with open(filename) as f:
        global_config = json.load(f)
    print global_config


    filename = "industry.txt"
    filename = os.path.join(global_config["home"],"data", filename)
    with open(filename, "r") as f:
        content = f.read()

    ret =[]
    list_line = []
    line_prev = None
    session_name = "Regular Talks"
    session_time=None
    time_slot = None
    paper_index = 1
    for line in content.split("\n"):
        line=line.strip()

        if len(line)<=0:
            continue

        if line[0] == "1":
            #time was given
            time_slot, session_x = line.split(" ", 1)
            if "session" in session_x.lower():
                session_name = session_x
                session_time = time_slot

            rest_of_line = " ".join(line.split(" ")[1:])
        else:
            rest_of_line = line

        if "." in rest_of_line:
            parts = rest_of_line.rsplit(".",1)
            paper_id = "industry%02d" % paper_index
            paper_index+=1

            item ={
                "title":parts[1].strip(),
                "author":parts[0],
                "category":"Industry Track Paper",
                "session_name": session_name,
                "session_time": session_time,
                "paper_id": paper_id,
            }

            if line[0] == "1":
                item["talk_time"]= time_slot


            print '"{}","{}"'.format(item["author"],item["title"])

            ret.append(item)

        line_prev=line

    print len(list_line)
    print lib_data.json2text(ret)

    filename = "paper-industry.json"
    filename = os.path.join(global_config["home"],"output", filename)
    with codecs.open(filename, "w","utf-8") as f:
        f.write(lib_data.json2text(ret))

    return ret


if __name__ == "__main__":
    load_paper_json()