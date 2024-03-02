#!/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import requests
from bs4 import BeautifulSoup

from metadb import metadb

import logging

def get_pic_from_bing(keywords):
    #keywords="prompt"
    host="https://cn.bing.com"
    link=host+"/images/search?q="+ keywords +"&first=1"
    #link=host+"/images/search?q="+ keywords +"&qft=+filterui:imagesize-medium&form=IRFLTR&first=1"
    r = requests.get(link)
    #print(r.text)
    
    #get first pic ref
    soup = BeautifulSoup(r.text,"html.parser")
    first_pic_ref = soup.find("div",class_="img_cont hoff").img.get('src')
    #print(first_pic_ref)
    
    #get pic and restore
    r = requests.get(first_pic_ref)
    #with open(keywords+".jpg","wb") as file:
    #    file.write(r.content);
    return r.content

def get_sound_from_bing(keywords):
    #keywords="prompt"
    host="https://cn.bing.com"
    link=host+"/dict/search?q="+ keywords
    r = requests.get(link)
    #print(r.text)
   
    #get first pic ref
    soup = BeautifulSoup(r.text,"html.parser")
    us_sound_ref = soup.find("a",id="bigaud_us").get('data-mp3link')
    #print(us_sound_ref)
      
    #get mp3 and restore
    r = requests.get(us_sound_ref)
    return r.content;


def get_pic(keywords):
    return get_pic_from_bing(keywords)

def get_sound(keywords):
    return get_sound_from_bing(keywords)

def dump_wordlists(files):
    r = []
    wl=re.compile(r'([a-zA-Z\-0-9]+).+?([ABC][12])')
    with open(files,"rt") as f:
       for l in f.readlines():
           m = wl.match(l)
           if type(m.group(1)) != 'NoneType' and \
                type(m.group(2)) != 'NoneType' :
               print("%s,%s "%(m.group(1),m.group(2)))
               
def dump_xwordlists(files):

    wl=re.compile(r'([a-zA-Z\-0-9]+).+?([ABC][12])')
    r = []
    with open(files,"rt") as f:
       for l in f.readlines():
           m = wl.match(l)
           if type(m.group(1)) != 'NoneType' and \
                type(m.group(2)) != 'NoneType' :
               #print("%s,%s "%(m.group(1),m.group(2)))
               r.append(m.group(1))
    #s = [ x for x in range(len(r)) ]
    random.shuffle(r)
    for x in r :
        print(x)
        
def wordlist_bat():
    db = metadb()
    from web_words import web_cfg as cfgdb
    cfgdb = cfgdb()
    last=cfgdb['netspider_last']
    if last is None:
        last=0
    #iter
    last=int(last)
    for id,word in cfgdb:
        #print(id,"->",word)
        if last > id:
            continue
        try:
            pic = get_pic(word)
            mp3 = get_sound(word)
            db.update_pic(word,pic)
            db.update_sound(word,mp3)
        except Exception as e:
            #print(e)
            logging.exception(e)
            print("id:%d ->%s netspider fail "%(id,word))
            cfgdb['netspider_last']=str(id)
            break

def update(word):
    db = metadb()
    from web_words import web_cfg as cfgdb
    cfgdb = cfgdb()
    last=cfgdb['netspider_last']
    if last is None:
        last=0
    #iter
    last=int(last)
    it = cfgdb.next(word,1);
    #print(next(it))
    #print(next(it))
    id,word = next(it)
    try:
        pic = get_pic(word)
        db.update_pic(word,pic)
        print("update %s pic .... ok"%(word))
    except Exception as e:
        print(e)
        print("update %s pic .... err"%(word))
        pass
    try:
        mp3 = get_sound(word)
        db.update_sound(word,mp3)
        print("update %s mp3 .... ok"%(word))
    except Exception as e:
        print(e)
        print("update %s mp3 ... err"%(word))
        pass
    cfgdb['netspider_last']=str(id+1)

if __name__ == '__main__':
#    get_sound_from_bing('test')
#    dump_wordlists('ox3000.txt');
#mp3 = get_sound('memorial')
#    wordlist_bat()        
#update('memorial')
    if len(sys.argv)>=3 and sys.argv[1] == "update":
        update(sys.argv[2])
    else:
        wordlist_bat()        
