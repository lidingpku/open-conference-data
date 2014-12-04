from pyPdf import PdfFileWriter, PdfFileReader
import json
import os
import re
import fnmatch

def removeNonAscii(s): 
	return "".join(i for i in s if ord(i)<128)

def removeNonDigtalAlpha(s): 
	return re.sub(r'[^a-zA-Z0-9:-]', '', s)

# load config file
with open("config.json") as f:
	global_config = json.load( f)

# build path to archive
mypath = os.path.join( global_config["home"], "local/raw/iswc/pps/web/iswc2007.semanticweb.org/papers/")
list_dir_pdf = []
for f in os.listdir(mypath):
	if fnmatch.fnmatch(f, '[0-9]*'):
		list_dir_pdf.append(f)

for dir_pdf in list_dir_pdf:
	filename_pdf = os.path.join( mypath, dir_pdf)
	
	#print filename_pdf, os.path.exists(filename_pdf)
	
	
	pdf = PdfFileReader(file(filename_pdf, "rb"))
	#print pdf.getDocumentInfo()

	text = removeNonDigtalAlpha(pdf.getPage(0).extractText())
	url_base = "http://iswc2007.semanticweb.org/papers/"
	print "%s%s\t%s" % (
		url_base,
		dir_pdf,
		text[0:50])

	#copy file
	#filename_target = os.path.join( global_config["home"], "local/open_access/iswc-aswc-2007", dir_pdf)
	#import shutil
	#shutil.copy2(filename_pdf, filename_target)
