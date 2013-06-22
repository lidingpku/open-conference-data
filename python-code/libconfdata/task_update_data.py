'''
update [home]/data

'''
import os
import rdflib
from rdflib import *
from io import *

import sys
#print sys.getdefaultencoding()
reload(sys)
sys.setdefaultencoding("utf-8")
#print sys.getdefaultencoding()

SWRC = Namespace('http://swrc.ontoware.org/ontology#')


class TaskUpdateData:
	@staticmethod
	def run(home):
		TaskUpdateData.update_data_iswc_local(home)
		TaskUpdateData.update_data_iswc_download(home)
		TaskUpdateData.update_data_iswc_patch(home)
		
	
	@staticmethod
	def update_data_iswc_local(home):
		dir_target = os.path.join(home,  "data/iswc/" )
		list_source = [
			"~/dl/project/iswc-metadata/data/final/*" ,
			"~/dl/project/iswc-metadata/data/manual/iswc-publication*"]
			
		for source in list_source:
			UtilShell.copy_file(source, dir_target)

	@staticmethod
	def update_data_iswc_download(home):
		list_data = [
			"iswc-2006","iswc-aswc-2007",
			"iswc-2008",
			"iswc-2009","iswc-2010",
			"iswc-2011","iswc-2012"
			]
		for id_data in list_data:
			#"http://data.semanticweb.org/dumps/conferences/iswc-2006-complete.rdf"
			url = "http://data.semanticweb.org/dumps/conferences/%s-complete.rdf" % (id_data)
			filename_output_rdfxml = "%s/data/iswc/%s-complete.rdf" % (home, id_data)
			
			UtilShell.download_file(url, filename_output_rdfxml)

	@staticmethod
	def update_data_iswc_patch(home):
		list_data = [
			#"iswc-2006","iswc-aswc-2007",
			"iswc-2008",
			#"iswc-2009","iswc-2010",
			#"iswc-2011","iswc-2012"
			]
		for id_data in list_data:
			#"http://data.semanticweb.org/dumps/conferences/iswc-2006-complete.rdf"
			filename_output_rdfxml = "%s/data/iswc/%s-complete.rdf" % (home, id_data)
			filename_output_add = "%s/data/iswc/%s-complete.add.ttl" % (home, id_data)
			filename_output_del = "%s/data/iswc/%s-complete.del.rdf" % (home, id_data)
			filename_output_new = "%s/data/iswc/%s-complete.new.ttl" % (home, id_data)
			graph_uri = "http://data.semanticweb.org/conference/%s/complete" % (id_data.replace("-20",'/20'))
			
			graph = rdflib.Graph()
			graph.load(filename_output_rdfxml)
			
			graph_delta_del = Graph()
			graph_delta_add = Graph()
			
			TaskUpdateData.clean_graph(graph, graph_delta_del, graph_delta_add )
			TaskUpdateData.patch_graph_with_paper(graph, graph_delta_del, graph_delta_add, graph_uri)
			
			cnt_triple_old = len(graph)
			for triple in graph_delta_del:
				graph.remove(triple)
			for triple in graph_delta_add:
				if not graph.__contains__(triple):
					graph.add(triple)
#				else:
					#print "-- contains tripe -->", triple
			cnt_triple_new = len(graph)
			 
			print "-- changed tripe -->", cnt_triple_new - cnt_triple_old, ' in  ',graph_uri  
			
			if len(graph_delta_add)>0:
				#print "--add-->", graph_delta_add.serialize(format='turtle')
				graph_delta_add.serialize(destination=filename_output_add, format='turtle', encoding="utf-8") 
				
			if len(graph_delta_del)>0:
				#print "--del-->", graph_delta_del.serialize()
				graph_delta_del.serialize(destination=filename_output_del, encoding="utf-8") 
				
			graph.serialize(destination=filename_output_new, format='turtle', encoding="utf-8") 

	@staticmethod
	def clean_node(term):
		if isinstance(term,rdflib.URIRef):
			# https://github.com/RDFLib/rdflib/blob/master/rdflib/term.py
			
			new_str = term.__str__().strip()
			if new_str!=term.__str__():
				return rdflib.URIRef(new_str)
				
		return None
		
	
	@staticmethod
	def clean_graph(graph, graph_delta_del, graph_delta_add ):
		for subject,predicate,obj in graph:
			#TODO only handle object
			modified = False

			new_subject = TaskUpdateData.clean_node(subject)
			if None != new_subject:
				modified = True
			else:
				new_subject = subject
				
			new_obj = TaskUpdateData.clean_node(obj)
			if None != new_obj:
				modified = True
			else:
				new_obj = obj
			
			new_obj = TaskUpdateData.clean_node(obj)
			if None!=new_obj:
				graph_delta_del.add([subject, predicate, obj])
				graph_delta_add.add([subject, predicate, new_obj])
				print "--cleaned trip--> " , new_obj.__str__()

		
	@staticmethod
	def patch_graph_with_paper(graph, graph_delta_del, graph_delta_add, graph_uri):
		graph_delta_add.bind("swrc", SWRC)
		graph.bind("swrc", SWRC)

		filename_paper_csv = "%s/data/iswc/iswc-publication-paper.csv" % (global_config["home"])
		with open(filename_paper_csv) as f:
			csvreader = UnicodeReader(f)
			headers =  csvreader.next()
			for row in csvreader:
				if len(row)<len(headers):
					#print "skipping row %s" % row 
					continue

				entry = dict(zip(headers, row))
				
				if entry['source_uri'] == graph_uri:
					if len(entry['paper_uri'])>0:
						subject = URIRef(entry['paper_uri'])
						
						#validate if the URI has been described in original data
						list_triples = list(graph[subject::])
						if len(list_triples)==0:
							raise "--uri not described in original data --> ", subject.__str__()
							
							
							#patch new triples
						for link in ['link_open_access', 'link_publisher']:
							if len(entry[link])>0 :
								#print "--add link--> " , entry[link]

								obj =  URIRef(entry[link])
								
								for predicate in [SWRC[link], SWRC.url]:
									triple = [subject, predicate, obj]
									graph_delta_add.add(triple)
													
		
###################################################################		
# load global config
global_config={
"home":"/home/dingli/dl/project/open-conference-data",
"created":"2013-05-24"
}


###################################################################		
# run update data
TaskUpdateData.run(global_config["home"])
