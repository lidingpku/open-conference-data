# -*- coding: utf-8 -*-
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from mu.lib_unicode import UnicodeReader, UnicodeWriter
from mu.lib_format import UtilString

import json
import collections
import re
import lib_data
import codecs
import slugify

def main():
    filename = "config.json"
    filename = os.path.join(os.path.dirname(__file__), filename)
    with open(filename) as f:
        global_config = json.load(f)
    print global_config


    list_input = [
        {"filename": "8796CorrespondingAuthors.csv",
         #TODO
         #"link_publisher":"tba",
         "proceedings_uri": "http://data.semanticweb.org/conference/iswc/2014/proceedings-1",
         },
        {"filename": "8797CorrespondingAuthors.csv",
         #"link_publisher":"tba",
         "proceedings_uri": "http://data.semanticweb.org/conference/iswc/2014/proceedings-2",
         },
    ]

    list_field=[
        "author",
        "title",
        "pages",
        "year",
        "link_open_access",
        "link_publisher",
        "proceedings_uri",
        "paper_uri",
        "source_uri",
        "keywords",
        "abstract",
        "uri_me",
        "category",
        "source",
        "start_page",
        "paper_id",
        "EOL",
    ]
    map_key = {
        "Title":"title",
        "Authors":"author",
        "Start Page":"start_page",
        "Folder Index":"paper_id",
        "Paper no.":"paper_no",
    }

    list_key = {
        "link_publisher",
        "proceedings_uri",
    }

    list_item = []
    counter = collections.Counter()

    for input in list_input:
        filename = os.path.join( global_config["home"],"data", input["filename"])
        print filename
        with open(filename,'r') as f:
            csvreader = UnicodeReader(f)
            headers = csvreader.next()

            prev_item = None
            for row in csvreader:
                entry = dict(zip(headers, row))

                print entry

                item = {
                    "year":2014,
                    "uri_me":"http://data.semanticweb.org/conference/iswc/2014",
                    #"EOL":"EOL",
                }
                for k,v in map_key.items():
                    item[v] = entry[k].strip()

                for k in list_key:
                    if k in input:
                        item[k] = input[k]

                temp = entry["Paper no."]
                if temp.startswith("DC"):
                    counter["DC"] += 1
                    category = "Doctoral Consortium Paper"
                else:
                    counter[temp[0]] += 1
                    map_category = {
                        "R": "Research Track Paper",
                        "D": "Replication, Benchmark, Data and Software Track Paper",
                        "I": "Semantic Web In Use Track Paper",
                    }
                    category = map_category[temp[0]]

                item["category"]= category

                list_item.append(item)

                if prev_item:
                    prev_item["pages"]= "{}-{}".format(prev_item["start_page"], int(item["start_page"]) - 1)

                prev_item = item

            prev_item["pages"]= "{}-".format(prev_item["start_page"])

    #update: paper uri
    for item in list_item:

        #paper_name = re.sub("\W+", "-", item[u"title"]).lower()
        paper_name = slugify.slugify(item[u"title"])
        print item[u"title"]
        print paper_name

        item["link_open_access"] = "https://github.com/lidingpku/iswc2014/raw/master/paper/{}-{}.pdf".format(item['paper_id'],paper_name)
        print item["link_open_access"]


    print counter.most_common()
    print len(list_item)

    #create file
    filename = "paper-excel.csv"
    filename = os.path.join(global_config["home"],"output", filename)
    print filename
    with open(filename, "w") as f:
        csvwriter = UnicodeWriter(f)
        csvwriter.writerow(list_field)

        for item in list_item:
            row = UtilString.json2list(item, list_field)
            csvwriter.writerow(row)

    filename = "paper-excel.json"
    filename = os.path.join(global_config["home"],"output", filename)
    print filename
    with codecs.open(filename, "w","utf-8") as f:
        f.write(lib_data.json2text(list_item))


if __name__ == "__main__":
    main()