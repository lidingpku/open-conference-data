import xml.etree.ElementTree as ElementTree
import json
import csv
import os
import htmlentitydefs
from datetime import datetime
from subprocess import call


'''
* http://docs.python.org/2/library/csv.html
* http://stackoverflow.com/questions/956867/how-to-get-string-objects-instead-unicode-ones-from-json-in-python
'''

import csv, codecs, cStringIO

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
            
def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input            
            
# load config file
with open("config.json") as f:
	global_config = json.load( f)



params ={}
params["filename_json"]= os.path.join(global_config['home'], 'data/raw/dblp_semweb.json')
params["filename_csv"]= os.path.join(global_config['home'], 'data/raw/dblp_semweb.csv')
params["filename_csv_sorted"]= os.path.join(global_config['home'], 'data/raw/dblp_semweb_sorted.csv')


def json2csv(global_config, params):
	LIST_COLUMN = ["crossref", "year", "title", "authors", "pages","editors",  "ee",  "publisher", "booktitle", "series","volume"]
	with open(params["filename_csv"],'w') as f_output:
		csvwriter = csv.writer(f_output)
		with open(params["filename_json"],'r') as f_input:
			list_paper = json.load( f_input )
			header = ["atype"]
			header.extend(LIST_COLUMN)
			header.append("key")
			csvwriter.writerow(header)
			for paper in list_paper:
				row = []
				row.append(convert(paper["_meta"]["type"]))
				for column in LIST_COLUMN:
					if column in paper:
						if column in ["authors", "editors"]:
								
							row.append(", ".join(convert(paper[column])))
						else:
							row.append(convert(paper[column]))
					else:
						row.append("")
				
				row.append(convert(paper["_meta"]["key"]))
				
				csvwriter.writerow(row)
			
			print row


json2csv(global_config, params)

command = "sort {0} > {1} ".format(params["filename_csv"], params["filename_csv_sorted"])
print command
call(command, shell=True)
