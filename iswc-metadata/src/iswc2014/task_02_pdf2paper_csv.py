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



def copy_pdf():
    filename = "config.json"
    filename = os.path.join(os.path.dirname(__file__), filename)
    with open(filename) as f:
        global_config = json.load(f)
    print global_config




    filepath = os.path.join(global_config["home"],"/Users/dingli/Downloads/879*/*/*/*.pdf")
    filenames = glob.glob(filepath)

    print len(filenames)

    for filename in filenames:
        paper_id = filename.split("/")[-2]
        filename_new = os.path.join(global_config["opendata"],"temp", "{}.pdf".format(paper_id))
        print filename_new

        shutil.copy2(filename, filename_new)


def extract_metadata():
    with open("config.json") as f:
        global_config = json.load(f)
    print global_config

    filepath = os.path.join(global_config["opendata"],"temp/*.pdf")
    filenames = glob.glob(filepath)
    print len(filenames)

    list_field = []

    filename_output_text = os.path.join(global_config["home"],"output/paper-pdf.txt")
    filename_output_csv  = os.path.join(global_config["home"],"output/paper-pdf.csv")
    list_paper = []
    with codecs.open(filename_output_text, "wb","utf-8") as f:
        with open(filename_output_csv, "wb") as fcsv:
            writer = UnicodeWriter(fcsv)

            for filename in filenames:
                #if '87970177' not in filename:
                #    continue

                with open(filename,'r') as fpdf:
                    f.write(u"=================================\n\r")
                    f.write(filename)
                    f.write(u'\n\r')
                    f.write(u'\n\r')
                    ret = lib_pdf.pdf2text(fpdf, maxpages=1)
                    for p in ["title","number_of_pages", "text"]:
                        f.write("\n")
                        f.write("\n")
                        f.write(p)
                        f.write("\n")
                        print
                        if p == "number_of_pages":
                            content = str(ret[p])
                        else:
                            content = ret[p]

                        f.write(content.decode("utf-8",errors="ignore"))

                    ret = lib_pdf.pdf2metadata_iswc(fpdf)
                    ret["paper_id"]= int(filename.split("/")[-1][:-4])
                    assert ret["author"]
                    list_paper.append(ret)
                    print json.dumps(ret,indent=4)
                    row = UtilString.json2list(ret, ["title","paper_id","author", "keyword","abstract"])
                    writer.writerow(row)

                #break

    filename_output_json  = os.path.join(global_config["home"],"output/paper-pdf.json")
    content = lib_data.json2text(list_paper)
    with codecs.open(filename_output_json, "w","utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    copy_pdf()
    #extract_metadata()