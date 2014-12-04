# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import json
import os
import re
from mu.lib_unicode import UnicodeWriter
from mu.lib_format import UtilString

class HtmlUtil(object):

	@staticmethod
	def extract_table(soup, attr_pattern):
		"""
		see http://www.crummy.com/software/BeautifulSoup/bs4/doc/
		"""
		list_table = soup.find_all('table', attrs=attr_pattern)

		ret = {}
		ret["rows"] = []
		for table in list_table:
			ret["headers"] = [header.text.encode('utf8').strip() for header in table.find_all('th')]
			for row in table.find_all('tr'):
				values = [val.text.encode('utf8').strip() for val in row.find_all('td')]
				if len(values)== len(ret["headers"]):
					ret["rows"].append(dict(zip(ret["headers"], values)))
				else:
					print "SKIP ROW: {}".format(values)
		
		return ret	    

	@staticmethod
	def extract_links(soup):
		ret = []
		for el in soup.find_all("a"):
			entry = {}
			entry["text"]= el.text.encode('utf8')
			entry["link"]= el['href']
			ret.append(entry)
		return ret


def easychair_paper_author(
	filename_input_paper, filename_input_author,
	filename_output_paper, filename_output_author):
	#process author
	with open(filename_input_author) as f:
		html_doc = f.read()
	soup = BeautifulSoup(html_doc)

	map_author_all ={}

	attr_pattern = { "class" : "ct_table"}
	list_author = HtmlUtil.extract_table(soup, attr_pattern)
	for author in list_author["rows"]:
		#print author
		name = author[u"Author"]
		map_author_all[name] = author
		author["Homepage"] = ""

	print "{} authors found".format(len(map_author_all))

	#process paper
	with open(filename_input_paper) as f:
		html_doc = f.read()
	soup = BeautifulSoup(html_doc)

	list_paper =[]

	list_author = []
	list_div_paper = soup.find_all('div', attrs= { "class" : "paper"})
	for div_paper in list_div_paper:
		paper ={}
		list_paper.append(paper)

		for cls in ["authors", "title"]:
			div_cls = div_paper.find('span', attrs= { "class" : cls})
			#print div_cls.text

			if cls =="authors":
				text = div_cls.text.encode('utf8')
				text = text.replace(" and ", ", ")
				text = re.sub("\.\s*$","", text)
				text = text.strip()
				paper[cls] = text


				for el in HtmlUtil.extract_links(div_cls):
					name = el["text"]
					list_author.append( name)
					if name not in map_author_all:
						print "ERROR: name [{}] not in author, with homepage".format(name)
						map_author_all[name]={"Author": name}

					el["link"] = el["link"].replace("http://http:/","http://")
					map_author_all[name]["Homepage"]=el["link"]

				for x in text.split(","):
					name =  x.strip()
					list_author.append( name )
					if name not in map_author_all:
						print "ERROR: name [{}] not in author, without homepage".format(name)
						map_author_all[name]={"Author": name}

			else:
				paper[cls] = div_cls.text.encode('utf8')

	list_author = sorted(set(list_author))

	list_div_abstract = soup.find_all('div', attrs= { "class" : "abstract"})
	for index, div_abstract in enumerate(list_div_abstract):
		abstract = div_abstract.text.encode('utf8').replace("Abstract:", "")
		abstract = abstract.strip()
		list_paper[index]["abstract"] =abstract
	
	print "{} papers write".format(len(list_paper))
	with open(filename_output_paper, "w") as f:
		csvwriter = UnicodeWriter(f)
		headers = ["authors", "title","abstract"]
		csvwriter.writerow(headers)

		for paper in list_paper:
			row = UtilString.json2list(paper, headers)
			csvwriter.writerow(row)

	print "{} authors write".format(len(list_author))
	with open(filename_output_author, "w") as f:
		csvwriter = UnicodeWriter(f)
		headers = ["Author", "Affiliation","Country","Email","Homepage"]
		csvwriter.writerow(headers)

		for name in list_author:
			author = map_author_all[name]
			row = UtilString.json2list(author, headers)
			csvwriter.writerow(row)



def main():
    ###################################################################        
    # load global config
    # load config file
    with open("config.json") as f:
        global_config = json.load( f)


    ###################################################################        
    # run 
	filename_input_author = os.path.join(
		global_config["home"], 
		"data/work/iswc2013/raw/pd-authors.html")

	filename_input_paper = os.path.join(
		global_config["home"], 
		"data/work/iswc2013/raw/pd-accepted-paper.html")

	filename_output_author = os.path.join(
		global_config["home"], 
		"data/work/iswc2013/raw/pd-authors.csv")

	filename_output_paper = os.path.join(
		global_config["home"], 
		"data/work/iswc2013/raw/pd-accepted-paper.csv")

	easychair_paper_author( 
		filename_input_paper, filename_input_author, 
		filename_output_paper, filename_output_author)


def sample(filename_input_author):
	# see http://www.crummy.com/software/BeautifulSoup/bs4/doc/
	     
	with open(filename_input_author) as f:
		html_doc = f.read()
	soup = BeautifulSoup(html_doc)

	attr_pattern = { "class" : "ct_table"}

	ret = {}

	table = soup.find('table', attrs=attr_pattern)
	ret["headers"] = [header.text.encode('utf8').strip() for header in table.find_all('th')]

	ret["rows"] = []
	for row in table.find_all('tr'):
		values = [val.text.encode('utf8').strip() for val in row.find_all('td')]

		if len(values)== len(ret["headers"]):
			ret["rows"].append(dict(zip(ret["headers"], values)))
		else:
			print "SKIP ROW: {}".format(values)

	print "{} columns found".format(len(ret["headers"]))
	print "{} rows found".format(len(ret["rows"]))



if __name__ == "__main__":
    main()

    with open("config.json") as f:
        global_config = json.load( f)
	filename_input_author = os.path.join(
		global_config["home"], 
		"data/work/iswc2013/raw/pd-authors.html")	
    sample(filename_input_author)
