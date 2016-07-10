#! /usr/bin/python 
# -*- coding: utf-8 -*- 

import urllib2, json, sys
import unicodedata
import time


def translate(filename):
    try:
        txtfile = open(filename)
    except:
        print ('faild to load %s' % filename)
        quit()

    if txtfile is None:
        print ('faild to load %s' % argvs[1])
        quit()

    txtdata = txtfile.readlines()
    txtfile.close()

    out_file = open('labels_jp.txt', 'a')
    for phrase in txtdata:
        phrase = phrase.rstrip("\n")
        phrase = phrase.decode('utf-8')

        if is_japanese(phrase):
            from_lang = u"ja"# English   
            dest_lang = u"en"# Japanese 
        else:
            from_lang = u"en"# English   
            dest_lang = u"ja"# Japanese 
        
        url = u"https://glosbe.com/gapi/translate?from=" \
            + from_lang + u"&dest=" + dest_lang \
            + u"&format=json&phrase=" + phrase + u"&pretty=true"
        response = urllib2.urlopen(url.encode("utf-8"))
        json_data = response.read()
        json_dict = json.loads(json_data)
        
        tuc = json_dict["tuc"]# tuc: list   

        print(phrase)
        # print(tuc)

        if tuc:
            if 'phrase' in tuc[0] and 'text' in tuc[0]["phrase"]:
                write_txt = '%s\n' % tuc[0]["phrase"]["text"]
                write_txt = write_txt.encode('utf-8')
            else:
                write_txt = 'None\n'
        else:
            write_txt = 'None\n'

        # if 'phrase' in tuc[0] and 'text' in tuc[0]["phrase"]:
        #     write_txt = '%s\n' % tuc[0]["phrase"]["text"]
        #     write_txt = write_txt.encode('utf-8')
        # else:
        #     write_txt = 'None\n'
        
        print(write_txt)
        out_file.write(write_txt)

        time.sleep(30)

    out_file.close()

def is_japanese(string):
    for ch in string:
        name = unicodedata.name(ch) 
        if "CJK UNIFIED" in name \
        or "HIRAGANA" in name \
        or "KATAKANA" in name:
            return True
    return False

if __name__ == '__main__':
    argvs = sys.argv
    argc = len(argvs)

    if (argc != 2):
        print ("Usage: $python " + argvs[0] + " labels.txt")
        quit()
        # phrase=sys.argv[1]
    filename=sys.argv[1]
        
    translate(filename)
