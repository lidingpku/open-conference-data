# -*- coding: utf-8 -*-
"""
https://github.com/timuralp/pdflib/blob/master/parse_pdf.py
"""

from pdfminer.pdfparser import PDFParser, PDFDocument, PDFNoOutlines
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTChar

from lib_ext import latex2unicode
import json
import os
import codecs
import glob
import re
from mu.lib_unicode import UnicodeReader, UnicodeWriter
from binascii import b2a_hex

def parse_lt_objs (lt_objs, page_number, images_folder, text=[]):
    """Iterate through the list of LT* objects and capture the text or image data contained in each"""
    text_content = [] 

    for lt_obj in lt_objs:
        if isinstance(lt_obj, LTTextBox) or isinstance(lt_obj, LTTextLine):
            # text
            text_content.append(lt_obj.get_text())

        elif isinstance(lt_obj, LTImage):
            # an image, so save it to the designated folder, and note it's place in the text 
            saved_file = save_image(lt_obj, page_number, images_folder)
            if saved_file:
                # use html style <img /> tag to mark the position of the image within the text
                text_content.append('<img src="'+os.path.join(images_folder, saved_file)+'" />')
            else:
                print >> sys.stderr, "Error saving image on page", page_number, lt_obj.__repr__
        elif isinstance(lt_obj, LTFigure):
            # LTFigure objects are containers for other LT* objects, so recurse through the children
            text_content.append(parse_lt_objs(lt_obj, page_number, images_folder, text_content))

    return '\n'.join(text_content)


###
### Extracting Images
###

def write_file (folder, filename, filedata, flags='w'):
    """Write the file data to the folder and filename combination
    (flags: 'w' for write text, 'wb' for write binary, use 'a' instead of 'w' for append)"""
    result = False
    if os.path.isdir(folder):
        try:
            file_obj = open(os.path.join(folder, filename), flags)
            file_obj.write(filedata)
            file_obj.close()
            result = True
        except IOError:
            pass
    return result

def determine_image_type (stream_first_4_bytes):
    """Find out the image file type based on the magic number comparison of the first 4 (or 2) bytes"""
    file_type = None
    bytes_as_hex = b2a_hex(stream_first_4_bytes)
    if bytes_as_hex.startswith('ffd8'):
        file_type = '.jpeg'
    elif bytes_as_hex == '89504e47':
        file_type = '.png'
    elif bytes_as_hex == '47494638':
        file_type = '.gif'
    elif bytes_as_hex.startswith('424d'):
        file_type = '.bmp'
    return file_type

def save_image (lt_image, page_number, images_folder):
    """Try to save the image data from this LTImage object, and return the file name, if successful"""
    result = None
    if lt_image.stream:
        file_stream = lt_image.stream.get_rawdata()
        if file_stream:
            file_ext = determine_image_type(file_stream[0:4])
            if file_ext:
                file_name = ''.join([str(page_number), '_', lt_image.name, file_ext])
                if write_file(images_folder, file_name, file_stream, flags='wb'):
                    result = file_name
    return result


### 
### Table of Contents
### 

def _parse_toc (doc):
    """With an open PDFDocument object, get the table of contents (toc) data
    [this is a higher-order function to be passed to with_pdf()]"""
    toc = []
    try:
        outlines = doc.get_outlines()
        for (level,title,dest,a,se) in outlines:
            toc.append( (level, title) )
    except PDFNoOutlines:
        pass
    return toc

def get_toc (pdf_doc, pdf_pwd=''):
    """Return the table of contents (toc), if any, for this pdf file"""
    return with_pdf(pdf_doc, _parse_toc, pdf_pwd)


###
### Processing Pages
###

def _parse_pages (doc, images_folder):
    """With an open PDFDocument object, get the pages and parse each one
    [this is a higher-order function to be passed to with_pdf()]"""
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    text_content = []
    for i, page in enumerate(doc.get_pages()):
        interpreter.process_page(page)
        # receive the LTPage object for this page
        layout = device.get_result()
        # layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
        text_content.append(parse_lt_objs(layout, (i+1), images_folder))
        break

    return text_content

def get_pages (pdf_doc, pdf_pwd='', images_folder='/tmp'):
    """Process each of the pages in this pdf file and return a list of strings representing the text found in each page"""
    return with_pdf(pdf_doc, _parse_pages, pdf_pwd, *tuple([images_folder]))


###
### Processing text objects
###

def _get_text_objects (doc, images_folder):
    """With an open PDFDocument object, get the pages and parse each one
    [this is a higher-order function to be passed to with_pdf()]"""
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)

    # Process each page contained in the document.
    first_page = doc.get_pages().next()
    interpreter.process_page(first_page)
    layout = device.get_result()

    text_objs = []
    for lt in layout:
        if isinstance(lt, LTTextBox):
            text_objs.append(lt)
        elif isinstance(lt,    LTTextLine):
            text_objs.append(lt)
    return text_objs

def get_text_objects (pdf_doc, pdf_pwd='', images_folder='/tmp'):
    """Process each of the pages in this pdf file and return a list of strings representing the text found in each page"""
    return with_pdf(pdf_doc, _get_text_objects, pdf_pwd, *tuple([images_folder]))


def with_pdf (pdf_doc, fn, pdf_pwd, *args):
    """Open the pdf document, and apply the function, returning the results"""
    result = None
    try:
        # open the pdf file
        fp = open(pdf_doc, 'rb')
        # create a parser object associated with the file object
        parser = PDFParser(fp)
        # create a PDFDocument object that stores the document structure
        doc = PDFDocument()
        # connect the parser and document objects
        parser.set_document(doc)
        doc.set_parser(parser)
        # supply the password for initialization
        doc.initialize(pdf_pwd)

        if doc.is_extractable:
            # apply the function and return the result
            result = fn(doc, *args)

        # close the pdf file
        fp.close()
    except IOError:
        # the file doesn't exist or similar problem
        pass
    return result

def hack_text(text):
	ret = text
#	ret = latex2unicode(ret)
	ret = ret.replace(u"´e",u"é")
	ret = ret.replace(u"¨o",u"ö")

	return ret

def parse_metadata(lt_text_list):
    # find the title
    title = None
    authors = None
    authors_x = None
    affiliation = None
    abstract = None
    keywords = None
    for lt in lt_text_list:
        if lt.is_empty():
            continue
        text = lt.get_text().strip()
        if len(text) < 5:
            continue

        if abstract:
            if keywords == None:
                if text.lower().startswith('keywords'):
                    keywords = text
                    keywords = text[9:].strip()
                    keywords = re.sub(u"[\n\r]"," ",keywords).strip() 
                    keywords = re.sub(u"\\s+"," ",keywords).strip() 
            break

        if text.lower().startswith('abstract'):
            index_keywords = text.lower().find("keywords:")
            if index_keywords>0:
                abstract = text[9:index_keywords]
                keywords = text[index_keywords+9:].strip()
                keywords = re.sub(u"[\n\r]"," ",keywords).strip() 
                keywords = re.sub(u"\\s+"," ",keywords).strip() 
            else:
                abstract = text[9:]
            abstract = hack_text(abstract)
            #abstract = re.sub("^\.?","",abstract).strip() 
            abstract = re.sub(u"[\n\r]"," ",abstract).strip() 
            abstract = re.sub(u"\\s+"," ",abstract).strip() 

        if title == None:
            title = text.replace('\n', ' ')
            title = hack_text(title)
            title = re.sub("[0-9]","",title)
            title = re.sub("\(cid:\)","",title)
            title = title.strip()
            continue

        if authors == None:
            authors = text.replace('\n', ' ')
            authors_x = authors
            authors_x = hack_text(authors_x)
            authors_x = re.sub("[0-9]","",authors_x)
            authors_x = re.sub(u"[∗]","",authors_x)
            authors_x = re.sub("\(cid:\)","",authors_x)
            authors_x = re.sub("[,\\s]+and\\s+",",",authors_x)
            authors_x = re.sub("\\s+[,\\s+]+\\s+",",",authors_x)
            continue

        if affiliation == None:
            affiliation = text
            affiliation = hack_text(affiliation)
            continue
        
             
    return [title, authors_x, affiliation, abstract, keywords, authors]   

def main():
    ###################################################################        
    # load global config
    # load config file
    with open("config.json") as f:
        global_config = json.load( f)

    # filename_pdf = os.path.join(global_config["home"],"data/open_access/2013-proceedings-1/82180001.pdf")
    # ret = get_text_objects(filename_pdf)
    # for text_obj in ret:
    #     print '-------'
    #     print text_obj.get_text()
    # print parse_metadata(ret)

    # return

    # http://denis.papathanasiou.org/tag/pdfminer/
    # https://github.com/dpapathanasiou/pdfminer-layout-scanner/blob/master/layout_scanner.py

    filepath = os.path.join(global_config["home"],"data/open_access/2013-proceedings-*/*.pdf")
    filenames = glob.glob(filepath)
    print len(filenames)

    filename_output_text = os.path.join(global_config["home"],"data/work/iswc2013/raw/iswc2013paper-text.txt")
    filename_output_csv = os.path.join(global_config["home"],"data/work/iswc2013/raw/iswc2013paper-metadata.csv")
    with codecs.open(filename_output_text, "wb","utf-8") as f:
        with open(filename_output_csv, "wb") as fcsv:
            writer = UnicodeWriter(fcsv)

            for filename in filenames:
                f.write(u"=================================\n\r")
                f.write(filename)
                f.write(u'\n\r')
                f.write(u'\n\r')
                ret = get_pages(filename)
                f.write(ret[0])

                ret = get_text_objects(filename)
                row = parse_metadata(ret)
                writer.writerow(row)



 #   print ret
    #print json.dumps(ret,indent=4)
    # with open(filename_pdf) as f:
    #     parser = PDFParser(f)
    #     # Create a PDF document object that stores the document structure.
    #     doc = PDFDocument()
    #     # Connect the parser and document objects.
    #     parser.set_document(doc)
    #     doc.set_parser(parser)
    #     # Supply the password for initialization.
    #     # (If no password is set, give an empty string.)
    #     doc.initialize("")
    #     # Check if the document allows text extraction. If not, abort.
    #     if not doc.is_extractable:
    #         raise PDFTextExtractionNotAllowed
    #     # Create a PDF resource manager object that stores shared resources.
    #     rsrcmgr = PDFResourceManager()
    #     # Create a PDF device object.
    #     laparams = LAParams()
    #     device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    #     # Create a PDF interpreter object.
    #     interpreter = PDFPageInterpreter(rsrcmgr, device)
    #     # Process each page contained in the document.
    #     images_folder= "/tmp"
    #     for i, page in enumerate(doc.get_pages()):
    #         interpreter.process_page(page)
    #         print page
    #         layout = device.get_result()
    #         print parse_lt_objs(layout, (i+1), images_folder)
    #         break



if __name__ == "__main__":
    main()
