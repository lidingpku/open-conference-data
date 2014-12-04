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
mypath = os.path.join( global_config["home"], "local/raw/iswc/pps/web/iswc2011.semanticweb.org/")
list_dir_pdf = []
for path, subdirs, files in os.walk(mypath):
    for name in files:
        if name.endswith(".pdf") and path.find("Workshops")<0:
            f = os.path.join(path, name)
            list_dir_pdf.append(f)

for dir_pdf in list_dir_pdf:
	filename_pdf = dir_pdf
	names = filename_pdf.split("/")
	lenx = len(names)
	filename = os.path.basename(filename_pdf)
	
	#print filename_pdf, filename ,os.path.exists(filename_pdf)
	url = os.path.join("http://liding.org/iswc_archive/iswc-2011/paper/",filename)
	#print ",".join([names[lenx-3],names[lenx-2],url])
	
	
	
	pdf = PdfFileReader(file(filename_pdf, "rb"))
	#print pdf.getDocumentInfo()
	text = removeNonDigtalAlpha(pdf.getPage(0).extractText())
	print ",".join(
	[	filename_pdf,
		url,
		names[lenx-3],
		names[lenx-2],
		text[0:20],
		text[0:50]])

	
	#copy file
	filename_target = os.path.join( global_config["home"], 
	"local/raw/iswc-2011/files", 
	filename)
	import shutil
	shutil.copy2(filename_pdf, filename_target)
	#print filename_target
	
