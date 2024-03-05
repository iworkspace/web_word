#!/usr/bin/env python

from io import BytesIO
from http.server import *
from urllib.parse import urlparse
import json
import re
import sqlite3 

'''
    sqlite3
    //add columns
    alter table tablename add column column_name column-type
    //sort
    select column1 from tablename where condition limit xx
'''

#import shutil
class web_words(object):
    def __init__(self,db_name="web.db"):
        sql = '''
            create table if not exists "word" (
        		"id"  INTEGER PRIMARY KEY AUTOINCREMENT,  
				"word" VARCHAR(64) NOT NULL,
                "units" INTEGER,
                "phonic" VARCHAR(64),
                "trans_han" VARCHAR(128),
                "verbose" BLOB,
                "pic" BLOB,
                "snd" BLOB
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

    def load_txt(self,ori_txt="eng.txt"):
        c = self.__conn ;
        sql = "delete from word;update sqlite_sequence set seq =0 where name = 'web'; "
        c.execute(sql);
        word_units=1
        word_units_rule=re.compile(r'Word\s+List\s+([0-9]+)')
        word_list_rule=re.compile(r'([A-Za-z\-\ ]+)[\*]?\s+[\/\[\{]([^\/\[\{]+)[\/\]\}]\s+(.+)')
        with open(ori_txt) as txtf:
            lines = txtf.readlines()
            for line in lines:
                m = word_units_rule.match(line) 
                if m and m.group(1):
                    word_units = int(m.group(1))
                    #print("get units:%d"%word_units)
                    continue
                m = word_list_rule.match(line)
                if m and m.group(1):
                    word=m.group(1).strip()
                    #print("%d %s %s %s"%(word_units,m.group(1),m.group(2),m.group(3)));
                    sql="insert or replace into word(units,word,phonic,trans_han,pic,snd)  values(?,?,?,?,?,?)"
                    c.execute(sql,(word_units,word,m.group(2),m.group(3),1,1))
        c.commit()
    
    def test(self):
        for i in self:
            id,word=i;
            word = word.strip()
            sql="update word set word = ? where id = ?"
            c = self.__conn ;
            print("id:%d word:%s->"%(id,word))
            c.execute(sql,(word,id));
        c.commit()

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
                #print(json.dumps(words_verb).encode())
                f.execute(sql,(json.dumps(words_verb).encode(),item[0]))
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
            sql = 'select id, word from word order by "id" '
            f.execute(sql)
            return f.__iter__()
    
    def next(self,start,limit=1):
        with self.__conn as c:
            limit = int(limit)
            f = c.cursor();
            if isinstance(start,int):
                sql = 'select id, word, verbose from word  where id >= ? order by "id" '
            elif isinstance(start,str):
                sql = 'select id,word, verbose from word where id >= (select id from word where word = (?) ) order by "id" '
            else:
                sql = 'select id, word, verbose from word order by "id" '
            sql += 'limit ?'
            f.execute(sql,(start,limit))
            return f.__iter__()

    def wrap(self,inq,deq):
        while not inq.empty():
            try:
                func,id,word,cnt = inq.get(block=False)
                if not func:
                    return
                r = func(word) 
                deq.put(("OK",id,word,r))
            except Exception as e:
                deq.put(("ERR",id,word,cnt+1))

    def query_pic(self,key):
        c = self.__conn.cursor()
        c.execute("select pic from word where word = ?",(key,))
        data = c.fetchone()
        return data
    
    def update_pic(self,key,pic):
        c = self.__conn.cursor()
        c.execute("insert or replace into word(word,pic) values(?,?); ",(key,pic))
        self.__con.commit()
    
    def query_sound(self,key):
        c = self.__conn.cursor()
        c.execute("select snd from word where word = ?",(key,))
        data = c.fetchone()
        return data
    
    def update_sound(self,key,sound):
        c = self.__conn.cursor()
        c.execute("insert or replace into word(word,snd) values(?,?); ",(key,sound))
        self.__conn.commit()		
	
    def netspider(self):
        import  queue
        import netspider as spider
        inq = queue.Queue(len(self))
        deq = queue.Queue(len(self))
        with self.__conn as c:
            f = c.cursor();
            for pre in ['snd','pic']:
                for i in range(1,4):
                    sql = 'select id,word from word where %s_cnt = ? '%(pre)
                    f.execute(sql,(i,))
                    for item in f.fetchall():
                        id,word=item
                        if pre == 'snd':
                            inq.put(( spider.get_sound,id,word,i))
                        else:
                            inq.put(( spider.get_pic,id,word,i))
                    
                    threads = []
                    from threading import Thread
                    for j in range(1,20):
                       t = Thread(target=self.wrap,args=(inq,deq))
                       t.start()
                       threads.append(t)

                    for t in threads:
                        t.join()
                    
                    while not deq.empty():
                        status,id,word,snd = deq.get(block=False)
                        if status == "OK":
                            sql = 'update word set %s = ? , %s_cnt= ? where id = ? '%(pre,pre)
                            f.execute(sql,(snd,0,id))
                            print("success update %s %s "%(pre,word))
                        else:
                            sql = 'update word set  %s_cnt= ? where id = ? '%(pre)
                            f.execute(sql,(snd+1,id))
                            print("fail update %s %s->%d "%(pre,word,snd+1))
                    c.commit()

meta = web_words()

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
        self.wfile.write(json.dumps({ra[0]:meta[ra[0]]} ).encode()) 

    def do_api_set_cfg(self,ra):
        meta[ra[0]]=str(ra[1])
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
        wlist = [ [x[0],x[1],json.loads(x[2])] for x in meta.next(last,limit) ] 
        self.wfile.write(json.dumps(wlist).encode()) 
	

    def do_api_handler(self,ra):
        #获取参数至字典
        #args = self.args_parser()
        sub = ra[0]
        word = ra[1]
        if sub == 'mp3' :
            print("query mp3")
            snd=meta.query_sound(word);
            self.send_response(200)
            self.send_header('Content-type','application/octet-stream')
            self.end_headers()
            self.wfile.write(snd[0]) 
        elif sub == 'pic' :
            print("query pic")
            pic=meta.query_pic(word);
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
    #meta.init_from_file('5000.rand')
    #meta.load_txt("IELTS Word List.txt")
    #meta.get_backlog_meta();
    meta.netspider()

if __name__ == '__main__':
    http_bind = ("0.0.0.0",8888)
    server = HTTPServer(http_bind,http_request_handler)
    print("Start http server : %s@%s" % http_bind)
    server.serve_forever()

