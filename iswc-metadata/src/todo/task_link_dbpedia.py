from dbpedia_api import DbpediaApi
from libx import UnicodeReader, UtilSyntax
import json
import os
#UtilLinkDbpedia.linkDbpedia("DERI galway","organisation")
#UtilLinkDbpedia.linkDbpedia("Linkoping University","organisation")
#UtilLinkDbpedia.linkDbpedia("MIT CSAIL","organisation")
#UtilLinkDbpedia.linkDbpedia("University Maryland","organisation")
#UtilLinkDbpedia.linkDbpedia("CNR","organisation")

with open("config.json") as f:
	global_config = json.load(f)

dir_data= "{0}/data/entity".format(global_config["home"])

dbpedia_api = DbpediaApi(dir_data, DbpediaApi.ENTITY_TYPE_ORGANIZATION)

list_tag=[
"swws-2001",
"iswc-2002",
"iswc-2003",
"iswc-2004",
"iswc-2005",
"iswc-2013",
]

for tag in list_tag:
	# process organization table
	filename = "{0}/data/manual/{1}-organization.csv".format(
		global_config["home"],
		tag)

	with open(filename) as f:
		csvreader = UnicodeReader(f)
		headers =  csvreader.next()
		for row in csvreader:
			if len(row)<len(headers):
				#print "skipping row %s" % row 
				continue

			entry = dict(zip(headers, row))

			org = entry["name"]

			if len(org)>0:
				#print "skipping empty name row %s" % entry
				continue

			print u"processing [{0}] in [{1}] ".format(org, tag)	
			dbpedia_api.process_names( org )

	# process person table
	filename = "{0}/data/manual/{1}-person.csv".format(
		global_config["home"],
		tag)

	with open(filename) as f:
		csvreader = UnicodeReader(f)
		headers =  csvreader.next()
		for row in csvreader:
			if len(row)<len(headers):
				#print "skipping row %s" % row 
				continue

			entry = dict(zip(headers, row))

			if "organization" in entry:
				for org in entry["organization"].split(";"):
					if len(org)==0:
						continue
					
					print u"processing [{0}] in [{1}] ".format(org, tag)	
					dbpedia_api.process_names( org )


# write all new data into file
print "write all data".format(org, tag)	
dbpedia_api.write_new_data()

'''
# load config file
with open("config.json") as f:
	global_config = json.load( f)

map_name ={}
filename_manual= "{0}/data/entity/cleanup-organization.csv".format(global_config["home"])
lsif os.path.exists(filename_manual):
	with open (filename_manual) as f:
		csvreader = UnicodeReader(f)
		headers =  csvreader.next()
		for row in csvreader:
			#print row
			status = row[0]
			altLabel = row[1]
			prefLabel = row[2]
			
			if len(prefLabel)>0:
				map_name[altLabel]=row
else:
	with open (filename_manual,"a") as f_manual:
		csvwriter = UnicodeWriter(f_manual)
		row =UtilLinkDbpedia.LIST_HEADER
		csvwriter.writerow(row)
		
with open (filename_manual,"a") as f_manual:
	csvwriter = UnicodeWriter(f_manual)

	filename_new= "{0}/local/output/candidate-organization.csv".format(global_config["home"])
	with open (filename_new) as f:
		csvreader = UnicodeReader(f)
		cnt_row = 0
		for row in csvreader:
			cnt_row+=1
			
			if len(row)==0:
				continue
				
			names = row[0].strip()
			if len(names)==0:
				continue
	
			if names in map_name:
				row = map_name[names]
			else:
				if len(names)>10:
					names =names.replace(" and ", ";")
					names =names.replace(" & ", ";")

				list_name = names.split(";")
				if len(list_name)>1:
					print cnt_row, " ==> ", list_name

				for name in list_name:
					#cache
					map_name[name]=row
					print cnt_row
					
					row = UtilLinkDbpedia.linkDbpedia(name, "organisation")
					csvwriter.writerow(row)
					print "\t".join(UtilSyntax.convert(row))
'''