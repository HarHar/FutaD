#!/usr/bin/env python
import os
import sys
if not ('--nodaemon' in sys.argv):
    print 'Forking..'
    if os.fork() != 0:
        exit()

hide_output = False if '--help' in sys.argv else True
if hide_output:
	for fd in [0, 1, 2]:
		os.close(fd)
	devnull = open(os.devnull, 'w')
	sys.stderr = devnull
	sys.stdout = devnull
	print 'akatsuki best girl'

from flask import Flask, request, redirect, url_for, render_template
import threading
import time
import gtk
import webkit
import psutil
import fuzzywuzzy.process
import parser

dbfile = sys.argv[-1]
db = parser.Parser(dbfile)

global globalInfo
infoTable = {'title': '', 'ep': '', 'type': '', 'percent': '', 'others': [], 'pcolor': '', 'ecolor': ''}
globalInfo = {'requestHide': False, 'requestShow': False, 'win': None, 'view': None, 'started': False, 'requestStop': False}
gtkstarted = False

def findingThread():
    global globalInfo
    interval = 4
    player = 'any'
    filetypes = ['mkv', 'mp4']
    seen = []
    replaces = {'_': ' ', '-': ' '}

    while True:
        try:
            processes = psutil.Process(1).get_children(recursive=True)
            for process in processes:
                if process.pid in seen:
                    if process.is_running() == False:
                        seen.remove(process.pid)
                    continue
                if player != 'any':
                    if process.name[0].lower() != player.lower():
                        continue
                for arg in process.cmdline:
                    for filetype in filetypes:
                        if arg.endswith(filetype):
                        	db.reload()
                            titles = {}
                            for entry in db.dictionary['items']:
                                titles[entry['name']] = entry
                            for replace in replaces:
                            	arg = arg.replace(replace, replaces[replace]) #such replacing
                            guess = fuzzywuzzy.process.extractBests(arg, titles)
                            infoTable['title'] = guess[0][0]
                            infoTable['percent'] = guess[0][1]
                            infoTable['type'] = titles[guess[0][0]]['type']
                            try:
                                infoTable['ep'] = str(int(titles[guess[0][0]]['lastwatched'])+1)
                            except:
                                infoTable['ep'] = 'unknown'
                            infoTable['pcolor'] = '#29d' if guess[0][1] > 60 else '#d81b21'
                            infoTable['ecolor'] = '#29d' if titles[guess[0][0]]['lastwatched'].isdigit() else '#d81b21'
                            seen.append(process.pid)

                            globalInfo['started'] = True
                            globalInfo['requestShow'] = True
                            continue
                seen.append(process.pid)
            time.sleep(interval)
        except psutil.NoSuchProcess: pass
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html', title=infoTable['title'], ep=infoTable['ep'], type=infoTable['type'],\
    percent=infoTable['percent'], others=infoTable['others'], pcolor=infoTable['pcolor'], ecolor=infoTable['ecolor'])

@app.route('/no')
def no():
    global globalInfo
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

    win = gtk.Window(gtk.WINDOW_TOPLEVEL) 
    screen = win.get_screen()
    screen_width, screen_height = screen.get_width(), screen.get_height()
    wsw, wsh = 575, 130

    win.add(sw) 

    win.set_default_size(wsw, wsh)
    win.connect('delete_event', gtk.main_quit)
    win.connect('destroy', gtk.main_quit)

    win.move(screen_width-wsw, screen_height-wsh)
    win.set_keep_above(True)
    win.set_decorated(False)

    globalInfo['win'] = win
    globalInfo['view'] = view

    while True:
        try:
            if globalInfo['started']:
                while gtk.events_pending():
                    gtk.main_iteration()

                if globalInfo['requestStop']:
                	globalInfo['started'] = False

                if globalInfo['requestHide']:
                    globalInfo['win'].hide()
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
                    globalInfo['view'].open('http://localhost:8880/')
                    globalInfo['win'].show_all()
                    globalInfo['requestShow'] = False
                time.sleep(.005)
            else: time.sleep(1)
        except KeyboardInterrupt, EOFError: os.kill(os.getpid(), 9)