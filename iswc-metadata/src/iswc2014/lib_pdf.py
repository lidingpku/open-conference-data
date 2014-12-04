# -*- coding: utf-8 -*-

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter, LTImage
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
import contextlib
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
import traceback
from pdfminer.pdftypes import resolve1
import re
from pdfminer.layout import LAParams, LTTextBox, LTTextLine, LTFigure, LTImage, LTChar
from pdfminer.converter import PDFPageAggregator

def extract_title(text):
    import re
    title = []
    for line in text.split('\n'):
        if len(line.strip())==0 and len(title)>0:
            break
        title.append(line)
    title = " ".join(title)
    title = re.sub("\s+"," ", title)
    return title.strip()


def __hack_text(text):
    ret = text
#	ret = latex2unicode(ret)
    ret = ret.replace(u"´e",u"é")
    ret = ret.replace(u"¨o",u"ö")
    ret = ret.replace(u"\ufb02", u"fl")
    ret = ret.replace(u"ﬀ",u"ff")
    ret = ret.replace(u"ﬃ",u"ffi")
    ret = ret.replace(u"ﬁ",u"fi")


    return ret



def pdf2metadata_iswc(fp):
    rsrcmgr = PDFResourceManager()
    with contextlib.closing(StringIO()) as retstr:
        codec = 'utf-8'
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos=set()
        list_page = PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True)
        first_page = list_page.next()
        interpreter.process_page(first_page)
        layout = device.get_result()

        page_cnt = 1
        for p in list_page:
            page_cnt+=1

        lt_text_list = []
        for lt in layout:
            if isinstance(lt, LTTextBox):
                lt_text_list.append(lt)
            elif isinstance(lt, LTTextLine):
                lt_text_list.append(lt)

        # find the title
        title = None
        authors = None
        authors_x = None
        affiliation = None
        abstract = None
        keywords = None
        lt_prev= None
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

            if title!=None and text.lower().startswith('abstract'):
                index_keywords = text.lower().find("keywords:")
                if index_keywords>0:
                    abstract = text[9:index_keywords]
                    keywords = text[index_keywords+9:].strip()
                    keywords = re.sub(u"[\n\r]"," ",keywords).strip()
                    keywords = re.sub(u"\\s+"," ",keywords).strip()
                else:
                    abstract = text[9:]
                abstract = __hack_text(abstract)
                #abstract = re.sub("^\.?","",abstract).strip()
                abstract = abstract.replace("-\n","")
                abstract = re.sub(u"[\n\r]"," ",abstract).strip()
                abstract = re.sub(u"\\s+"," ",abstract).strip()

            if title == None:
                title = text.replace('\n', ' ')
                title = __hack_text(title)
                title = re.sub("[0-9]","",title)
                title = re.sub("\(cid:\)","",title)
                title = title.strip()

                lt_prev = lt
                continue

            if authors== None and title and lt_prev:
                if lt_prev.height == lt.height:
                    temp = text.replace('\n', ' ')
                    temp = __hack_text(temp)
                    temp = re.sub("[0-9]","",temp)
                    temp = re.sub("\(cid:\)","",temp)
                    title = u"{} {}".format(title, temp.strip())
                    continue

            if authors == None:
                authors = text.replace('\n', ' ')
                authors_x = authors
                authors_x = __hack_text(authors_x)
                authors_x = re.sub("[0-9]","",authors_x)
                authors_x = re.sub(u"[∗]","",authors_x)
                authors_x = re.sub("\(cid:\)","",authors_x)
                authors_x = re.sub("[,\\s]+and\\s+",",",authors_x)
                authors_x = re.sub("\\s+[,\\s+]+\\s+",",",authors_x)
                lt_prev = lt
                continue

            if affiliation== None and authors and lt_prev:
                if lt_prev.height == lt.height:
                    temp = text.replace('\n', ' ')
                    authors = u"{} {}".format(authors, temp.strip())

                    temp = __hack_text(temp)
                    temp = re.sub("[0-9]","",temp)
                    temp = re.sub(u"[∗]","",temp)
                    temp = re.sub("\(cid:\)","",temp)
                    temp = re.sub("[,\\s]+and\\s+",",",temp)
                    temp = re.sub("\\s+[,\\s+]+\\s+",",",temp)
                    authors_x = u"{} {}".format(authors_x, temp.strip())
                    continue

            if affiliation == None:
                affiliation = text
                affiliation = __hack_text(affiliation)
                continue



        return {"title":title, "author":authors_x, "affiliation_original":affiliation, "abstract":abstract, "number_of_pages": page_cnt } #, "keywords":keywords, "author_original":authors}



LIST_FIELD_MEATDATA = ["title","author", "keywords", "abstract", "number_of_pages"]


def pdf2text(fp, maxpages=0):
    rsrcmgr = PDFResourceManager()
    with contextlib.closing(StringIO()) as retstr:
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        caching = True
        pagenos=set()
        list_page = PDFPage.get_pages(fp, pagenos, maxpages=0, password=password,caching=caching, check_extractable=True)
        page_cnt = 0
        for page in list_page:
            if maxpages==0 or page_cnt<maxpages:
                interpreter.process_page(page)
            page_cnt+=1

        device.close()
        str = retstr.getvalue()

        title = extract_title(str)

        return {"text":str, "title":title, "number_of_pages": page_cnt}


def pdf2metadata(fp):
    parser = PDFParser(fp)
    doc = PDFDocument(parser)
    parser.set_document(doc)
    doc.initialize()

    if 'Metadata' in doc.catalog:
        metadata = resolve1(doc.catalog['Metadata']).get_data()
        #print metadata  # The raw XMP metadata
    return doc.info  # The "Info" metadata


def process_blob(blob, list_fn_option=(pdf2metadata, pdf2text)):
    ret = {}
    with contextlib.closing(StringIO(blob)) as fp:
        for fn_option in list_fn_option:
            try:
                ret[fn_option.__name__] = fn_option(fp)
            except:
                traceback.print_exc()

    return ret
