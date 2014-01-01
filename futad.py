#!/usr/bin/env python
import os
import sys
if not ('--nodaemon' in sys.argv):
	print 'Forking..'
	if os.fork() != 0:
		exit()

from flask import Flask, request, redirect, url_for, render_template
import threading
import time
import gtk
import webkit

#topkek
devnull = open(os.devnull, 'w')
sys.stderr = devnull
sys.stdout = devnull
#######

app = Flask(__name__)

@app.route('/')
def home():
	return render_template('home.html', title="Shinryaku! Ika Musume", ep="07")

def showin():
    view = webkit.WebView() 

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

    win.show_all()
    win.move(screen_width-wsw, screen_height-wsh)
    win.set_keep_above(True)
    win.set_decorated(False)
    win.show_all()

    view.open('http://localhost:8880/')
    try:
        gtk.main()
    except Exception, e:
        print str(e)
        os.kill(os.getpid(), 9)

if __name__ == '__main__':
    app_thread = threading.Thread(target=app.run, args=('0.0.0.0', 8880,))
    app_thread.setDaemon(True)
    app_thread.start()

    time.sleep(1)
    showin()