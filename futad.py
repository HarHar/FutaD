#!/usr/bin/env python3
import os
import sys
if not ('--nodaemon' in sys.argv):
    print('Forking..')
    if os.fork() != 0:
        exit()

hide_output = False if '--verbose' in sys.argv else True
if hide_output:
    for fd in [0, 1, 2]:
        os.close(fd)
    devnull = open(os.devnull, 'w')
    sys.stderr = devnull
    sys.stdout = devnull
    print('akatsuki best girl')

noanims = True if '--noanims' in sys.argv else False

from flask import Flask, request, redirect, url_for, render_template
import threading
import time
from gi.repository import Gtk, GdkPixbuf, Gdk
gtk = Gtk
from gi.repository import WebKit
webkit = WebKit

import psutil
import fuzzywuzzy.process
import parser
import re
import utils
import traceback

dbfile = sys.argv[-1]
db = parser.Parser(dbfile)

global globalInfo
infoTable = {'title': '', 'ep': '', 'type': '', 'percent': '', 'others': [], 'pcolor': '', 'ecolor': '', 'dbEntry': None}
globalInfo = {'requestHide': False, 'requestShow': False, 'win': None, 'view': None, 'started': False, 'requestStop': False, 'db': db, 'requestHeight': 0, 'requestReload': False}
gtkstarted = False

ANN = utils.ANNWrapper()
ANN.init()

def findingThread():
    global globalInfo
    interval = 4
    player = 'any'
    filetypes = ['mkv', 'mp4']
    fileseen = []
    replaces = {'_': ' ', '-': ' '}

    while True:
        try:
            processes = psutil.process_iter()
            for process in processes:
                if player != 'any':
                    if process.name[0].lower() != player.lower():
                        continue
                try:
                    for openfile in process.get_open_files():
                        if openfile[0] in fileseen: continue
                        for filetype in filetypes:
                            if openfile[0].endswith(filetype):
                                fileseen.append(openfile[0])
                                arg = openfile[0]
                                db.reload()
                                titles = {}
                                for entry in db.dictionary['items']:
                                    titles[entry['name']] = entry
                                for replace in replaces:
                                    arg = arg.replace(replace, replaces[replace]) #such replacing
                                arg = os.path.basename(arg)
                                arg = os.path.splitext(arg)[0]
                                arg = re.sub(r'\(.*?\)', '', arg)
                                arg = re.sub(r'\[.*?\]', '', arg)
                                guess = []
                                for title in titles:
                                	if title.lower() in arg.lower():
                                		guess.append((title, 99))
                                guess += fuzzywuzzy.process.extractBests(arg, titles.keys())
                                if int(guess[0][1]) < 86:
                                    break

                                seen = []
                                for g in guess:
                                	if g[0] in seen:
                                		guess.remove(g)
                                	seen.append(g[0])
                                guess = guess[:5]
                                infoTable['title'] = guess[0][0]
                                infoTable['percent'] = guess[0][1]
                                infoTable['type'] = titles[guess[0][0]]['type']
                                try:
                                    infoTable['ep'] = str(int(titles[guess[0][0]]['lastwatched'])+1)
                                except:
                                    infoTable['ep'] = 'unknown'
                                infoTable['pcolor'] = '#29d' if guess[0][1] > 60 else '#d81b21'
                                infoTable['ecolor'] = '#29d' if titles[guess[0][0]]['lastwatched'].isdigit() else '#d81b21'
                                infoTable['dbEntry'] = titles[guess[0][0]]
                                infoTable['others'] = guess

                                globalInfo['started'] = True
                                globalInfo['requestShow'] = True
                                continue
                except psutil.AccessDenied: pass
            time.sleep(interval)
        except psutil.NoSuchProcess: pass
app = Flask(__name__)

@app.route('/')
def loading():
    return render_template('loading.html', noanims=str(noanims))

@app.route('/main')
def home():
    try:
        global globalInfo, infoTable
        globalInfo['requestHeight'] = 130
        others = []
        for guess in infoTable['others']:
            if guess[0] != infoTable['title']:
                others.append(guess)

        entryDetails = ANN.details(infoTable['dbEntry']['aid'], infoTable['dbEntry']['type'])
        epName = ''
        for epn in entryDetails['episode_names']:
            if epn.isdigit() and infoTable['ep'].isdigit():
                if int(epn) == int(infoTable['ep']):
                    epName = entryDetails['episode_names'][epn]

        return render_template('home.html', title=infoTable['title'], ep=infoTable['ep'], type=infoTable['type'],\
        percent=infoTable['percent'], others=others, pcolor=infoTable['pcolor'], ecolor=infoTable['ecolor'],\
        db=globalInfo['db'], noanims=str(noanims), epname=epName)
    except Exception:
        traceback.print_exc()
        return 'Exception :c'

@app.route('/no')
def no():
    global globalInfo
    globalInfo['requestHide'] = True
    return ''

@app.route('/resizeTo_<h>')
def grow(h):
    global globalInfo
    globalInfo['requestHeight'] = int(h)
    return ''

@app.route('/changeEp_<ep>')
def changeEp(ep):
    global globalInfo, infoTable
    infoTable['ep'] = str(ep)
    globalInfo['requestReload'] = True
    return ''

@app.route('/changeSrs_<srs>')
def changeSrs(srs):
    global globalInfo, infoTable
    infoTable['title'] = srs
    infoTable['percent'] = 100
    infoTable['pcolor'] = '#29d'
    globalInfo['requestReload'] = True
    return ''

@app.route('/yes')
def yes():
    global globalInfo, infoTable
    infoTable['dbEntry']['lastwatched'] = str(int(infoTable['dbEntry']['lastwatched']) + 1)
    globalInfo['db'].save()
    globalInfo['requestHide'] = True
    return ''

if __name__ == '__main__':
    app_thread = threading.Thread(target=app.run, args=('0.0.0.0', 8880,))
    app_thread.setDaemon(True)
    app_thread.start()

    finder_thread = threading.Thread(target=findingThread)
    finder_thread.setDaemon(True)
    finder_thread.start()

    view = webkit.WebView()
    settings = view.get_settings()
    settings.set_property('enable-plugins', False)
    settings.set_property('enable-java-applet', False)
    view.set_settings(settings)

    sw = gtk.ScrolledWindow()
    sw.add(view)

    win = gtk.Window()
    screen = win.get_screen()
    screen_width, screen_height = screen.get_width(), screen.get_height()
    wsw, wsh = 575, 130
    globalInfo['requestHeight'] = wsh

    win.add(sw) 

    win.set_default_size(wsw, wsh)
    win.set_property('height-request', wsh)
    win.set_property('width-request', wsw)
    win.connect('delete_event', gtk.main_quit)
    win.connect('destroy', gtk.main_quit)

    win.move(screen_width-wsw, screen_height-wsh)
    win.set_keep_above(True)
    win.set_decorated(False)
    win.set_resizable(False)
    win.set_title('FutaD')
    win.set_wmclass('futad', 'futad')
    win.set_role('futad')
    win.set_focus(None)

    globalInfo['win'] = win
    globalInfo['view'] = view

    while True:
        try:
            if globalInfo['started']:
                while gtk.events_pending():
                    gtk.main_iteration()

                if globalInfo['requestHeight'] != wsh:
                    if noanims:
                        wsh = globalInfo['requestHeight']-1
                    if globalInfo['requestHeight'] > wsh:
                        wsh += 1
                    else:
                        wsh -= 1
                    win.resize(wsw, wsh)
                    win.move(screen_width-wsw, screen_height-wsh)
                    win.set_property('height-request', wsh)
                    win.set_property('width-request', wsw)
                    continue

                if globalInfo['requestStop']:
                    globalInfo['started'] = False
                    globalInfo['requestStop'] = False

                if globalInfo['requestHide']:
                    win.hide()
                    globalInfo['requestHide'] = False

                    #I had to do this because if we simply
                    #do globalInfo['started'] = False as to
                    #reduce uneeded checks and GTK iterating
                    #hogging the CPU, GTK will not have time
                    #to process the .hide() we just issued as
                    #it will not reiterate and do the
                    #events_pending loop and hide it,
                    #so we have to flag that we want to stop
                    #the GTK loop after the next iteration
                    #</walloftext>
                    globalInfo['requestStop'] = True

                if globalInfo['requestShow']:
                    view.open('http://localhost:8880/')
                    win.show_all()
                    win.move(screen_width-wsw, screen_height-wsh)
                    globalInfo['requestShow'] = False

                if globalInfo['requestReload']:
                    view.open('http://localhost:8880/')
                    globalInfo['requestReload'] = False

                time.sleep(.0001)
            else: time.sleep(1)
        except KeyboardInterrupt:
            os.kill(os.getpid(), 9)
        except EOFError:
            os.kill(os.getpid(), 9)
