# -*- coding:utf-8 -*-

import requests
import random
import json
import time
from bs4 import BeautifulSoup
import threading
import os
import sys
import Queue

headers = [
    {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0'},
    {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'},
    {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)'},
    {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:40.0) Gecko/20100101 Firefox/40.0'},
    {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/44.0.2403.89 Chrome/44.0.2403.89 Safari/537.36'}]

class Song_Info():
    def __init__(self, path, group_id, group_name, song_id, name):
        self.path = path
        self.group_id = group_id
        self.group_name = group_name
        self.song_id = song_id
        self.name = name

def Get_Url_Content(url):
    return requests.get(url, headers=random.choice(headers)).content

class Download_Song_Thread(threading.Thread):
    def __init__(self):
        super(Download_Song_Thread, self).__init__()
        self.Song_Infos = Queue.Queue()
        self.terminal = False
        self.mutex = threading.Lock()

    def __del__(self):
        pass

    def addSongId(self, songInfo):
        self.mutex.acquire()
        self.Song_Infos.put(songInfo)
        self.mutex.release()

    def __getSongInfo(self):
        songInfo = None
        self.mutex.acquire()
        if not self.Song_Infos.empty():
            songInfo = self.Song_Infos.get()
        self.mutex.release()
        return songInfo

    def __downLoadSong(self, songInfo):
        # print group_id, group_name, song_id, name
        url = "http://music.163.com/api/song/detail/?id=" + str(songInfo.song_id) + "&ids=%5B" + str(songInfo.song_id) + "%5D"
        content = Get_Url_Content(url)
        r = requests.get(json.loads(content)['songs'][0]['mp3Url'], stream=True)

        try:
            #with open(songInfo.path + "\\%s\\%s.mp3" %(songInfo.group_name, songInfo.name), 'wb') as f:
            print songInfo.path
            with open(songInfo.path + "\\%s.mp3"%(songInfo.name), 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        f.flush()
                f.close()
        except IOError as e:
            print "I/O error 2222".format(e.errno, e.strerror)
        except ValueError:
            print "unknown error"

        return False

    def setTerminal(self):
        self.terminal = True

    def run(self):
        while self.terminal is not True:
            songInfo = self.__getSongInfo()
            if songInfo is not None:
                self.__downLoadSong(songInfo)
            else:
                time.sleep(0.01)

class Get_Mp3_Info():
    def __init__(self, headers):
        self.headers = headers

    def Get_Message(self, dir, content, groupid):
        print json.loads(content)['result']['name']
        #os.makedirs(dir)    # + json.loads(content)['result']['name'])
        path = dir + "\\" + json.loads(content)['result']['name']
        number = len(json.loads(content)['result']['tracks'])
        lists = []
        for i in xrange(number):
            try:
                songInfo = Song_Info(dir, groupid, json.loads(content)['result']['name'], json.loads(content)['result']['tracks'][i]['id'], json.loads(content)['result']['tracks'][i]['name'])
                lists.append(songInfo)
            except IOError as e:
                print "I/O error 111".format(e.errno, e.strerror)
            except ValueError:
                print "unknown error"
        return lists

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding("utf-8")

    keyword = "欧美"
    dir = "D:\\Python\\Spider\\test"

    thread = []
    for x in xrange(8):
        thread.append(Download_Song_Thread())
    for y in thread:
        y.start()

    get_mp3_info = Get_Mp3_Info(headers)
    index = 0
    num = 0
    while True:
        s = requests.Session()
        songUrl = "http://music.163.com/discover/playlist/?order=hot&cat=" + keyword + "&limit=35&offset=" + str(35*index)
        index = index + 1
        songList = BeautifulSoup(s.get(songUrl, headers=random.choice(headers)).content,"lxml").select('.u-cover > a')
        length = len(songList)
        for i in range(length):
            groupids = str(songList[i].attrs['href'].replace('/playlist?', ''))
            songslist = get_mp3_info.Get_Message(dir,
                Get_Url_Content("http://music.163.com/api/playlist/detail?" + str(groupids)), str(groupids))
            for songInfo in songslist:
                thread[num % len(thread)].addSongId(songInfo)
                num = num + 1

        if length < 35:
            break

    for i in thread:
        i.setTerminal()
    for i in thread:
        i.join()