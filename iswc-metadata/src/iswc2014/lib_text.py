# -*- coding: utf-8 -*-
import traceback
import base64
import hashlib
import codecs

import chardet
import mimetypes


def guess_charset(text):
    if not isinstance(text, basestring) or isinstance(text, unicode):
        return None

    test_text = text
    test_text = test_text[:5000]
    try:
        charset_info = chardet.detect(test_text)

        if charset_info and charset_info["confidence"] > 0.8:
            if charset_info["encoding"] in ["ascii", "ISO-8859-8"]:
                charset_info = None
        else:
            charset_info = None
    except:
        traceback.print_exc()
        return None

    return charset_info


# http://pythonhosted.org/webencodings/_modules/webencodings.html
# Some names in Encoding are not valid Python aliases. Remap these.
PYTHON_NAMES = {
    'iso-8859-8-i': 'iso-8859-8',
    'x-mac-cyrillic': 'mac-cyrillic',
    'macintosh': 'mac-roman',
    'windows-874': 'cp874'}


def __remap_charset(charset):
    if charset in PYTHON_NAMES:
        return PYTHON_NAMES[charset]
    else:
        return charset


def str2base64(text):
    pos = text.find('--')
    if pos > 0:
        text = text[:pos]

    return base64.b64decode(text)


def str2unicode(text, encoding=None, flag_auto=False):
    if text is None:
        return None

    #TODO hack, backward compaible
    if isinstance(encoding, dict):
        encoding = encoding["encoding"]

    ret = str2unicode_info(text, encoding, flag_auto)
    if ret:
        return ret["data"]
    else:
        #return None
        if str_is_binary(text):
            return None
        else:
            return codecs.decode(text, "utf-8", "ignore")


# http://stackoverflow.com/questions/898669/how-can-i-detect-if-a-file-is-binary-non-text-in-python
def str_is_binary(text):
    if not text:
        return None

    textchars = ''.join(map(chr, [7,8,9,10,12,13,27] + range(0x20, 0x100)))
    is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))
    return is_binary_string(text[:20])

def str2unicode_info(text, xencoding=None, flag_auto=False):
    if text is None:
        return None

    if isinstance(text, unicode):
        return dict(data=text)

    if str_is_binary(text):
        return None

    try:
        #charset_info = None
        if flag_auto and None == xencoding:
            charset_info = guess_charset(text)
            if charset_info:
                xencoding = charset_info["encoding"]
        else:
            charset_info = {"encoding": xencoding, "confidence":1 }

        #try to use the guessed encoding
        if xencoding:
            xencoding = __remap_charset(xencoding)
            try:
                return dict(encoding=xencoding, data=codecs.decode(text, xencoding))
            except:
                if charset_info and charset_info["confidence"] > 0.95:
                    return dict(encoding=xencoding, data=codecs.decode(text, xencoding, "ignore"))

        #try if any encoding gen unicode without exception
        list_encoding = ('UTF-8', 'GB2312', 'ISO-8859-1', 'ascii')
        for gxencoding in list_encoding:
            try:
                return dict(encoding=gxencoding, data=codecs.decode(text, gxencoding))
            except UnicodeDecodeError:
                pass

        #finally use the given/guessed encoding anyway
        if xencoding:
            return dict(encoding=None, data=codecs.decode(text, xencoding, "ignore"))
    except:
        traceback.print_exc()

    return None


def str2hash(text):
    if isinstance(text, unicode):
        text = text.encode(encoding="utf-8")
    return hashlib.sha256(text).hexdigest()


def str2sha256sum(text):
    if isinstance(text, unicode):
        text = text.encode(encoding="utf-8")
    return hashlib.sha256(text).hexdigest()


def any2utf8(xinput):
    if xinput is None:
        return None
    """
  convert a string or object into utf8 encoding
  source: http://stackoverflow.com/questions/13101653/python-convert-complex-dictionary-of-strings-from-unicode-to-ascii
  usage:
        text = "abc"
        str_replace = any2utf8(text)
    """
    if isinstance(xinput, dict):
        return {any2utf8(key): any2utf8(value) for key, value in xinput.iteritems()}
    elif isinstance(xinput, list):
        return [any2utf8(element) for element in xinput]
    elif isinstance(xinput, set):
        return set(any2utf8(element) for element in xinput)
    elif isinstance(xinput, unicode):
        return xinput.encode("utf-8")
    elif isinstance(xinput, basestring):
        ret = str2unicode(xinput, flag_auto=True)
        if ret is None:
            return ret
        else:
            return ret.encode("utf-8")
    else:
        return xinput



def any2unicode(xinput):
    """
  convert a string or object into utf8 encoding
  source: http://stackoverflow.com/questions/13101653/python-convert-complex-dictionary-of-strings-from-unicode-to-ascii
  usage:
        text = "abc"
        str_replace = any2utf8(text)
    """
    if isinstance(xinput, dict):
        return {any2unicode(key): any2unicode(value) for key, value in xinput.iteritems()}
    elif isinstance(xinput, list):
        return [any2unicode(element) for element in xinput]
    elif isinstance(xinput, set):
        return set(any2unicode(element) for element in xinput)
    elif isinstance(xinput, unicode):
        return xinput
    elif isinstance(xinput, basestring):
        return str2unicode(xinput, flag_auto=True)
    else:
        return xinput


def unicode_ellipsis(text, limit, max_padding=3):
    text = str2unicode(text)
    if len(text) > limit:
        list_word = []
        cnt_char = 0
        for word in text.split(" "):
            cnt_char += (len(word)+1)
            if cnt_char <= limit-max_padding:
                list_word.append(word)
            elif cnt_char <= limit-3:
                list_word.append(word)
                list_word.append(u"...")
                break
            elif cnt_char <= limit -3 + len(word)/2:
                length = (limit+len(word)-3-cnt_char)
                list_word.append(u"{}...".format(word[:length]))
                break
            else:
                list_word.append(u"...")
                break
        return u" ".join(list_word)
#        return u"{} ...".format(text[:limit - 4])
    else:
        return text
