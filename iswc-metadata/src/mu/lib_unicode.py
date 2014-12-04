import csv
import codecs
import cStringIO
import codecs 


def replace_with_dash(e): 
    """ replace unicode chars with -
        usage: 
            encode("ascii","replace_with_dash")   

            other built-in options "ignore", "replace" (with ?)
            e.g. 
            encode("ascii","replace") will replace non-ascii into "?"
    """
    return (u'-',e.start + 1) 
codecs.register_error('replace_with_dash',replace_with_dash)


def any2utf8(input):
    """
     convert a string or object into utf8 encoding
     source: http://stackoverflow.com/questions/13101653/python-convert-complex-dictionary-of-strings-from-unicode-to-ascii
     usage: 
        str = "abc"
        str_replace = any2utf8(str)
    """
    if isinstance(input, dict):
        return {any2utf8(key): any2utf8(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [any2utf8(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input  


""" unicode csv reader/writer
 source: http://docs.python.org/2/library/csv.html
 usage:
        from lib_unicode import *

        filename ="your file name"
        with open(filename) as f:
            csvreader = UnicodeReader(f)

            headers =  csvreader.next()
            #print(headers)

            for row in csvreader:
                if len(row)!=len(headers):
                    print("skipping row {0}".format(row))
                    continue

                entry = dict(zip(headers, row))

                #print(row)
"""

class UTF8Recoder(object):
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader(object):
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
        
class UnicodeWriter(object):
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
        row = any2utf8(row)
        self.writer.writerow(row)
        #self.writer.writerow([s.encode("utf-8") for s in row])
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




