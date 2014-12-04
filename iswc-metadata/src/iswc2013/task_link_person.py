from mu.lib_format import UtilCsv, UtilString
from mu.lib_unicode import UnicodeWriter
import os
import json


def main():
    ###################################################################        
    # load config file
    with open("config.json") as f:
        global_config = json.load( f)



    """	load three csv files, 
    	aggregate them to form a join
    """
    json_person = {}
    filename = os.path.join(global_config["home"], "data/work/iswc2013/raw/payments.csv")
    json_payment = UtilCsv.csv2json(filename)
    for entry in json_payment:
        key = entry["name"].lower()
        if key in json_person:
            data = json_person[key]
        else:
            data = {"name":entry["name"], 
                    "paid":False, 
                    "attend":False, 
                    "paper":[]}
            json_person[key]=data
        data["email_payment"]= entry["email"]
        data["id_payment"]= entry["id"]
        data["paid"]= True


    filename = os.path.join(global_config["home"], "data/work/iswc2013/raw/attendees.csv")
    json_attendees = UtilCsv.csv2json(filename)
    for entry in json_attendees:
        key = entry["name"].lower()
        if key in json_person:
            data = json_person[key]
        else:
            data = {"name":entry["name"], 
                    "paid":False, 
                    "attend":False, 
                    "paper":[]}
            json_person[key]=data
        data["email_attendees"]= entry["email"]
        data["id_attendees"]= entry["id"]
        data["attend"]= True

    json_output=[]

    filename = os.path.join(global_config["home"], "data/source/iswc-2013-paper.csv")
    json_paper = UtilCsv.csv2json(filename)

    #split authors
    for entry in json_paper:
        title = entry["title"]
        entry["author_list"]= [x.strip() for x in entry["author"].split(',')]

        #print len(json_paper), entry
        data_paper = { "paid":[], "attend":[]}
        for key in ["title","category","author"]:
            data_paper[key] =entry[key]

        json_output.append(data_paper)

        for name in entry["author_list"]:
            key =name.lower()
            if key in json_person:
                json_person[key]["paper"].append(title)

                if json_person[key]["paid"]:
                    data_paper["paid"].append(name)
                if json_person[key]["attend"]:
                    data_paper["attend"].append(name)

    filename_output = os.path.join(global_config["home"], "data/work/iswc2013/raw/stat_paper.csv")
    with open(filename_output,"w") as f:
        csvwriter = UnicodeWriter(f)

        headers = ["category","author","title","paid","attend"]
        csvwriter.writerow(headers)

        for entry in json_output:
            #print entry
            row = UtilString.json2list(entry, headers)
            csvwriter.writerow(row)

    filename_output = os.path.join(global_config["home"], "data/work/iswc2013/raw/stat_person.csv")
    with open(filename_output,"w") as f:
        csvwriter = UnicodeWriter(f)

        headers = ["name","paid","attend","paper"]
        csvwriter.writerow(headers)

        for entry in sorted(json_person.values(), key=lambda x:x["name"]):
            #print entry
            row = UtilString.json2list(entry, headers)
            csvwriter.writerow(row)

if __name__ == "__main__":
    main()
