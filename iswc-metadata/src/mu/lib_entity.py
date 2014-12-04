"""
syntax
entity ::= {id(utc millisecond), type, id_from, id_to, status, data, source, note}

data example1: search wikipedia
{   "id":1378327851001, 
    "type":"name-name",
    "id-from":"MIT",
    "id-to":"Massachusetts Institute of Technology",
    "status":"auto",
    "date":"2013-09-04", 
    "source":"wikipedia+dbpedia"
}

data example2: search dbpedia
{   "id":1378327851002,
    "type":"name-uri",
    "id-from":"Massachusetts Institute of Technology",
    "id-to":"http://dbpedia.org/resource/Massachusetts_Institute_of_Technology",
    "status":"auto",
    "date":"2013-09-04", 
    "source":"dbpedia"
}

data example3: manual assert
{   "id":1378327851003,
    "type":"name-name",
    "id-from":"Mit",
    "id-to":"MIT",
    "status":"auto",
    "date":"2013-09-04", 
    "source":"man"
}

data
* map_data   id_from > type > record
* list_new   [record]
* list_fail  [id_from] -- avoid retry
* map_type_lookup   type > lookup-function    input: id_from; output:{type>record}

operation
* load(dir_name, entity_type)
   pass1: remove obsoleted relation r1 where r1.id_from=r2.id_from and r1.created<r2.created
          alternatively, use a hashtable with keys {type, id-from} 
* find(id_from, type, recursive=False)
* add(record)



notes
* persistent storage in csv file 
* records is ordered by created


1. api
2. web test
3. algorithm develop

"""


class DataNamedEntity(object):
    ENTITY_TYPE_ORGANIZATION = "organisation"
    ENTITY_TYPE_PERSON = "person"
    ENTITY_TYPE_PLACE = "place"

#    LIST_HEADER = ["altLabel","title","subtitle", "uri","source","status","redirects","disambiguates","matched_entity_type"]
    LIST_HEADER = ["altLabel", "title", "subtitle", "uri", "source", "status", "redirects", "disambiguates",
                   "matched_entity_type", "row_type"]

    def __log__(self, msg):
        print( "[{}]{}",format(type(self),msg) )

    def __init__(self, dir_data, entity_type):
        # init config
        self.config = {
        "entity_type": entity_type, 
        "fn_data":  "%s/%s.csv" % (dir_data, entity_type) ,
        "fn_new": "%s/%s.new.csv" % (dir_data, entity_type) ,
        }
        
        #load data
        data_json = []
        if os.path.exists(self.config["fn_data"]):
            data_json = UtilCsv.csv2json(self.config["fn_data"])
            self.__log__("load {} entries from [{}]".format(
                len(data_json), 
                self.config["fn_data"]))
        else:
            with open (self.config["fn_data"],'w') as f:
                csvwriter = UnicodeWriter(f)
                headers = EntityPerson.LIST_HEADER
                csvwriter.writerow(headers)

        #init internal_memory
        self.dict_name ={}

        for entry in data_json:
            #default label_type
            if not entry["label_type"]:
                entry["label_type"]="text"

            data_person = {}
            for p in ["name","sense","modified"]
                data_person[p]=entry[p]

            UtilJson.add_init_dict(
                self.dict_name
                [ entry["label_type"] ],
                entry["label_text"],
                data_person
                )

        #init new row
        self.list_new_entity =[]
    
    def add_new_data(self, entry):
        #source_id
        #email
        #homepage
        #name
        #organization
        #country


    def write_new_data(self, filemode="w"):
        headers = DbpediaApi.LIST_HEADER
        
        print "{0} new mapping entries added ".format(len(self.list_new_entity))

        #start the new data file, to be merged to original data
        with open (self.config["fn_new"],filemode) as f:
            csvwriter = UnicodeWriter(f)
            for entry in self.list_new_entity:
                row = UtilString.json2list(entry, headers)
                csvwriter.writerow(row)
