from lib_unicode import *
import simplejson as json

class UtilString(object):
    """ String API"""
    @staticmethod    
    def levenshtein(seq1, seq2):
        """ classical editing distance
         http://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Levenshtein_distance#Python
        """
        oneago = None
        thisrow = range(1, len(seq2) + 1) + [0]
        for x in xrange(len(seq1)):
            twoago, oneago, thisrow = oneago, thisrow, [0] * len(seq2) + [x + 1]
            for y in xrange(len(seq2)):
                delcost = oneago[y] + 1
                addcost = thisrow[y - 1] + 1
                subcost = oneago[y - 1] + (seq1[x] != seq2[y])
                thisrow[y] = min(delcost, addcost, subcost)
        return thisrow[len(seq2) - 1]

    @staticmethod
    def json2list(json_data, list_header):
        row = []
        for header in list_header:
            if header in json_data:
                value = json_data[header]
            else:
                value = ""
            row.append(value)
        return row


class UtilCsv(object):
    """ CSV APIS
    """

    @staticmethod
    def csv2json(filename_csv, has_header=True, filename_json=None):
        """ 
            load csv into json 
        """
        ret = []
        with open(filename_csv) as f:
            csvreader = UnicodeReader(f)

            if has_header:
                headers =  csvreader.next()
                #trim white spaces in headers
                temp = []
                for header in headers:
                    temp.append(header.strip())
                headers =temp
                #print(headers)


            for row in csvreader:
                if has_header:
                    if len(row)!=len(headers):
                        print "skipping row {0}".format( row )
                        continue

                    entry = dict(zip(headers, row))    
                    #print(entry)

                    ret.append(entry)

        if None!=filename_json:
            with open (filename_json) as f:
                json.dump(ret, f, indent=4, sort_keys=True)

        return ret

class UtilJson(object):
    """ JSON APIS
    """

    @staticmethod
    def add_init_dict(json_data, pre_keys, key, value):
        temp = json_data
        for k in pre_keys:
            if not k in temp:
                temp[k] = {}
            temp = temp[k]

        temp[key]=value
        
    @staticmethod
    def add_init_list(json_data, pre_keys, key, value, unique=False):
        temp = json_data
        for k in pre_keys:
            if not k in temp:
                temp[k] = {}
            temp = temp[k]

        if not key in temp:
            temp[key]=[]
            
        if unique and value in temp[key]:
            #skip duplicate insertion
            return 
            
        temp[key].append(value)