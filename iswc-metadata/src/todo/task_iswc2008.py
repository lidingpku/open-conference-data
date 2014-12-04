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
mypath = os.path.join( global_config["home"], "local/raw/iswc-2008/LNCS_5318_Archive")
list_dir_pdf = []
for f in os.listdir(mypath):
	if fnmatch.fnmatch(f, '[0-9]*'):
		list_dir_pdf.append(f)

for dir_pdf in list_dir_pdf:
	filename_pdf = os.path.join( mypath, dir_pdf, dir_pdf+ ".pdf")
	
	#print filename_pdf, os.path.exists(filename_pdf)
	
	pdf = PdfFileReader(file(filename_pdf, "rb"))
	#print pdf.getDocumentInfo()
	text = removeNonDigtalAlpha(pdf.getPage(0).extractText())
	url_base = "https://files.ifi.uzh.ch/ddis/iswc_archive/iswc/open-access/iswc-2008/"
	print "%s%s.pdf\t%s\t%s" % (
		url_base,
		dir_pdf, 
		text[0:20],
		text[0:50])

	#copy file
	filename_target = os.path.join( mypath, "../files", dir_pdf+ ".pdf")
	import shutil
	shutil.copy2(filename_pdf, filename_target)
