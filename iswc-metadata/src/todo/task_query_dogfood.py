import json
import os
import urllib
from subprocess import call
from libx import UnicodeReader, UnicodeWriter, MyCounterKeyValue, UtilSyntax

  
  

# load config file
with open("config.json") as f:
	global_config = json.loads( f.read())
	#print json.dumps(global_config, indent=4, sort_keys=True)

list_filename_query = [
 "all-person"
 ,"all-organization"
]

for filename_query in list_filename_query:
	params ={}

	params["filename_query"] = "{0}/data/query/{1}.sparql".format(global_config['home'], filename_query)
	params["filename_result"] = "{0}/data/raw/{1}.json".format(global_config['home'], filename_query)
	params["filename_manual_csv"] = "{0}/data/manual/{1}.csv".format(global_config['home'], filename_query)
	params["filename_temp_csv"] = "{0}/local/output/{1}.csv".format(global_config['home'], filename_query)
	with open(params["filename_query"]) as f:
		query = f.read()
	print query
		
	command= "curl -H \"Accept: application/sparql-results+json\" \"http://data.semanticweb.org/sparql?query={0}\" > {1}".format(urllib.quote(query), params["filename_result"])
	print command
	#call(command, shell=True)
	
	#load manual mapping
	#name,uri
	mem_name_uri_mapping ={}
	if os.path.exists(params["filename_manual_csv"]):
		with open(params["filename_manual_csv"]) as f:
			csvreader = UnicodeReader(f)
			csvreader.next()
			for row in csvreader:
				if len(row)<2:
					continue
						
				name = row[0]
				uri = row[1]
				mem_name_uri_mapping[name]= uri
			
	#write temp csv
	with open(params["filename_result"]) as f:
		json_data = json.load(f)
	
		counter_name_uri = MyCounterKeyValue()
		counter_uri_name = MyCounterKeyValue()
		for item in json_data["results"]["bindings"]:
			name = item["name"]["value"]
			uri  = item["uri"]["value"]
			g = item["g"]["value"]
			counter_name_uri.inc(name, uri, g)
			counter_uri_name.inc(uri, name, g)
	
		with open(params["filename_temp_csv"],"w") as f_output:
			csvwriter = UnicodeWriter(f_output)
			head = ["name","uri","cnt_uri","cnt_g","cnt_name","alt_name"]

			#print row
			total_row=0
			csvwriter.writerow(head)
			for name in counter_name_uri.data:
				#skip names that we already know
				if name in mem_name_uri_mapping:
					continue;
				
				for uri in counter_name_uri.data[name]:
					row = []
					row.append(name)
					
					row.append(uri)
					
					row.append(len(counter_name_uri.data[name]))

					row.append(len(counter_name_uri.data[name][uri]))

					row.append(len(counter_uri_name.data[uri]))

					row.append(json.dumps(counter_uri_name.data[uri].keys()))
					#print row
					csvwriter.writerow(row)
					total_row+=1
			print "{0} rows written to {1}".format(total_row, params["filename_temp_csv"])
