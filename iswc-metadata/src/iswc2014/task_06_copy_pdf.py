
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




def load_gloabl_config():
    filename = "config.json"
    filename = os.path.join(os.path.dirname(__file__), filename)
    with open(filename) as f:
        global_config = json.load(f)
    print global_config
    return global_config


def main():
    global_config = load_gloabl_config()


    #load json to get paper uri
    filename = "paper-excel.json"
    filename  = os.path.join(global_config["home"],"output", filename)
    with open(filename, 'r') as f:
        content = f.read()
        list_paper_pdf = lib_data.text2json(content)

    print len(list_paper_pdf)

    for paper_info in list_paper_pdf:
        print paper_info["link_open_access"]
        filename_new = paper_info["link_open_access"].split("/")[-1]
        paper_id = filename_new.split("-",1)[0]


        filename_x = os.path.join(global_config["opendata"],"temp/{}.pdf".format(paper_id))
        filename_new = os.path.join(global_config["opendata"],"paper/{}".format(filename_new))

        print filename_x, filename_new
        shutil.copy2(filename_x,filename_new)

if __name__ == "__main__":
    main()