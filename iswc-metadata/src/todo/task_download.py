import json
from subprocess import call

'''mirror website directory

http://www.commandlinefu.com/commands/view/7180/get-gzip-compressed-web-page-using-wget.
'''


def download_all():
	# load config file
	with open("config.json") as f:
		global_config = json.loads( f.read())
		#print json.dumps(global_config, indent=4, sort_keys=True)
		
	url = "http://data.semanticweb.org/dumps/"
	command= "wget -r --no-parent {0} -P {1}".format(url, global_config['home']+"/local/raw/")
	print command
	call(command, shell=True)

	url= "http://dblp.uni-trier.de/xml/dblp.xml.gz"
	command= "wget -O- {0} | gunzip > {1}".format(url, global_config['home']+"/local/raw/dblp.xml")
	print command
	call(command, shell=True)

	url= "http://dblp.uni-trier.de/xml/dblp.dtd"
	command= "wget {0} -P {1}".format(url, global_config['home']+"/local/raw/")
	print command
	call(command, shell=True)


	url= "https://files.ifi.uzh.ch/ddis/iswc_archive/iswc.zip"
	command= "wget {0} -P {1}".format(url, global_config['home']+"/local/raw/")
	print command
	call(command, shell=True)

	command= "unzip {0}".format(global_config['home']+"/local/raw/iswc.zip")
	print command
	call(command, shell=True)

def download_now():	
	# load config file
	with open("config.json") as f:
		global_config = json.loads( f.read())
		#print json.dumps(global_config, indent=4, sort_keys=True)

	urls = ["http://ilrt.org/discovery/2001/06/content/swws2001-07-30.rdf",
			"http://ilrt.org/discovery/2001/06/content/swws2001-07-31.rdf",
			"http://ilrt.org/discovery/2001/06/content/swws2001-08-01.rdf"]
	for url in urls:
		command= "wget {0} -P {1}".format(url, global_config['home']+"/local/raw/swws2001/")
		print command
		call(command, shell=True)
	
	
download_now()
