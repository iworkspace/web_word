#!/usr/bin/env python

from io import BytesIO
from http.server import *
from urllib.parse import urlparse
import json
import re
import sqlite3 
from metadb import metadb 

'''
    sqlite3
    //add columns
    alter table tablename add column column_name column-type
    //sort
    select column1 from tablename where condition limit xx
'''

#import shutil
class web_cfg(object):
    def __init__(self,db_name="web.db"):
        sql = '''
            create table if not exists "word" (
        		"id"  INTEGER PRIMARY KEY AUTOINCREMENT,  
				"word" VARCHAR(64) NOT NULL,
                "verbose" BLOB
			);
            create table if not exists "cfg" (
                "key" VARCHAR(64) PRIMARY KEY NOT NULL,
                "value" VARCHAR(64) NOT NULL
			);
            --insert into cfg(key,value) values("last",1);
            --insert into cfg(key,value) values("page",8);
            '''
        self.__conn = sqlite3.connect(db_name)
        self.__conn.executescript(sql);
        self['dblen']=str(len(self))
        self.__conn.commit()
 

    def get_backlog_meta(self,dbfile="stardict.db"):
        import stardict
        dict_backlog =  stardict.StarDict(dbfile)
        with self.__conn as c:
            f = c.cursor();
            sql = "select id,word from word order by id ;";
            f.execute(sql)
            r=f.fetchall()
            for item in r:
                word = item[1]
                words_verb = dict_backlog[word]
                sql = "update word set verbose = ? where id = ? ;"
                f.execute(sql,(json.dumps(words_verb).encode(),item[0]))
            c.commit()

    def init_from_file(self,filelist):
       #清空原表 
       c = self.__conn
       sql = "delete from word;update sqlite_sequence set seq =0 where name = 'web'; "
       c.executescript(sql)
       c.commit()
       with open(filelist) as f:
           lines = f.readlines();
           for i in lines:
               sql = "insert INTO word(word) values(?) "
               c.execute(sql,(i.strip(),));
       c.commit()

    def __del__(self):
        if self.__conn:
            self.__conn.commit()
            self.__conn.close()
            self.__conn = None
        
    def __getitem__(self,key):
        with self.__conn as c:
            f = c.cursor();
            sql = "select value from cfg where key=(?);";
            f.execute(sql,(key,))
            r=f.fetchone()
            if r:
                return r[0]

    def __len__(self):
        with self.__conn as c:
            f = c.cursor();
            sql = "select count(*) from word;"
            f.execute(sql)
            return f.fetchone()[0]
    
    def __setitem__(self,key,value):
        with self.__conn as c:
            sql = "insert or replace into cfg(key,value) values(?,?);"
            c.execute(sql,(key,value.strip()))

    def __iter__(self):
        with self.__conn as c:
            f = c.cursor();
            sql = 'select id, word from web order by "id" '
            f.execute(sql)
            return f.__iter__()
    
    def next(self,start,limit=1):
        with self.__conn as c:
            limit = int(limit)
            f = c.cursor();
            if isinstance(start,int):
                sql = 'select id, word, verbose from word  where id >= ? order by "id" '
            elif isinstance(start,str):
                sql = 'select id,word, verbose from word where id >= (select id from web where word = (?) ) order by "id" '
            else:
                sql = 'select id, word, verbose from word order by "id" '
            sql += 'limit ?'
            f.execute(sql,(start,limit))
            return f.__iter__()

wordb = web_cfg()
metadb = metadb()

#class http_request_handler(BaseHTTPRequestHandler):
class http_request_handler(SimpleHTTPRequestHandler):
#    def __init__(self,load):
#        pass

    def __filter(self):
        url_req = urlparse(self.path)
        word = url_req.path.split('/')
        if word[1] == 'api':
            return self.do_api_handler(word[2:])
        #default handle by 
        SimpleHTTPRequestHandler.do_GET(self)

    def do_GET(self):
        self.__filter()

    def do_POST(self):
        self.__filter()

    def args_parser():
        if self.command == 'GET':
            pass
        else: 
            pass

    def do_api_get_cfg(self,ra):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()
        self.wfile.write(json.dumps({ra[0]:wordb[ra[0]]} ).encode()) 

    def do_api_set_cfg(self,ra):
        wordb[ra[0]]=str(ra[1])
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()
        self.wfile.write(b'{"status":"OK"}') 
    
    def do_api_get_list(self,ra):
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()
        last=int(ra[0])
        limit=int(ra[1])
        wlist = [ [x[0],x[1],json.loads(x[2])] for x in wordb.next(last,limit) ] 
        self.wfile.write(json.dumps(wlist).encode()) 
    


    def do_api_handler(self,ra):
        #获取参数至字典
        #args = self.args_parser()
        sub = ra[0]
        word = ra[1]
        if sub == 'mp3' :
            print("query mp3")
            snd=metadb.query_sound(word);
            self.send_response(200)
            self.send_header('Content-type','application/octet-stream')
            self.end_headers()
            self.wfile.write(snd[0]) 
        elif sub == 'pic' :
            print("query pic")
            pic=metadb.query_pic(word);
            self.send_response(200)
            self.send_header('Content-type','image/jpeg')
            self.end_headers()
            self.wfile.write(pic[0]) 
        elif sub == 'get_cfg':
            self.do_api_get_cfg(ra[1:]); 
        elif sub == 'update_cfg':
            self.do_api_set_cfg(ra[1:]); 
        elif sub == 'get_list':
            self.do_api_get_list(ra[1:])
        else:
            pass

if __name__ == '__main__1':
    #wordb.init_from_file('5000.rand')
    wordb.get_backlog_meta("stardict.db")

if __name__ == '__main__':
    http_bind = ("0.0.0.0",8888)
    server = HTTPServer(http_bind,http_request_handler)
    print("Start http server : %s@%s" % http_bind)
    server.serve_forever()

