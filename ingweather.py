#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui
from PyQt4.QtCore import SLOT
from PyQt4.QtCore import SIGNAL
from PyQt4 import QtCore
from PIL import Image
import ImageOps
import ImageDraw, ImageFont
import time
from urllib2 import urlopen
import lxml.html
from StringIO import StringIO
import os

url = "http://catserver.ing.iac.es/weather/index.php?miniview=1"
tempdir = "/tmp/ingweather"
timeout = 150

if not os.access(tempdir, os.F_OK): #check if folder exists
  os.mkdir(tempdir)

def wrNumb(Hum):
    im = Image.open("/usr/share/ingweather/data/square-mask.png")
    font = ImageFont.truetype("/usr/share/ingweather/data/dsfont.ttf", 96)
    draw = ImageDraw.Draw(im)

    intHum = int(Hum)#FIXME in case of broken data it will crash program
    #choose color
    if intHum < 65:
      color = "rgb(9,249,17)"
    elif intHum < 75:
      color = "rgb(255,255,0)"
    else:
      color = "rgb(255,0,0)"

    #align position
    if intHum < 10:
      pos = (35, 10)
    else:
      pos = (6, 10)

    draw.text(pos, Hum, font=font, fill=color)
    del draw
    im.save('/tmp/ingweather/numb.png')



def creIma(Hum):
    wrNumb(Hum)
    highlight = Image.open('/usr/share/ingweather/data/square.png')
    mask = Image.open('/usr/share/ingweather/data/square-mask.png')
    icon = Image.open('/tmp/ingweather/numb.png').convert('RGBA')
    button = Image.new('RGBA', mask.size)
 
    # Resize Icon
    icon = ImageOps.fit(
        icon, highlight.size, method=Image.ANTIALIAS, centering=(0.5, 0.5)
        )
 
    # Create a helper image that will hold the icon after the reshape
    helper = button.copy()
    # Cut the icon by the shape of the mask
    helper.paste(icon, mask=mask)
 
    # Fill with a solid color by the mask's shape
    button.paste((255, 255, 255), mask=mask)
    # Get rid of the icon's alpha band
    icon = icon.convert('RGB')
    # Paste the icon on the solid background
    # Note we are using the reshaped icon as a mask
    button.paste(icon, mask=helper)
 
    # Get a copy of the highlight image without the alpha band
    overlay = highlight.copy().convert('RGB')
    button.paste(overlay, mask=highlight)
 
    button.save('/tmp/ingweather/button.png')


def parser():
    global url

    f = urlopen(url)
    s = f.read()
    f.close()

    result = []

    pars = lxml.html.etree.HTMLParser()
    tree = lxml.html.etree.parse(StringIO(s),pars)
    for parent in tree.getiterator():
        if parent.tag == "tr" and len(parent)==6:
            try:    # FIXME
                TelName = parent[0][0][0].text
            except IndexError:
                TelName = parent[0][0].text
            Temp  = parent[1].text
            Hum   = parent[2].text
            Wspd  = parent[3].text
            Wdir  = parent[4].text
            Press = parent[5].text
            result.append((TelName,Temp,Hum,Wspd,Wdir,Press))
    return result

def GetHum():
    data = parser()
    Hum = 0
    for s in data:
        if s[0] == "LT":
            Hum = s[2]
            creIma(Hum)
            return Hum

class AlarmWindow(QtGui.QDialog):
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        okButton = QtGui.QPushButton("&OK")
        cancelButton = QtGui.QPushButton("&Cancel")
        self.connect(cancelButton, QtCore.SIGNAL("clicked()"), self, QtCore.SLOT("hhide()"))#"reject()"))
        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(okButton)
        buttonLayout.addWidget(cancelButton)
        
        layout = QtGui.QVBoxLayout()
        #layout.addWidget(self.textEdit)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

    @QtCore.pyqtSlot()
    def hhide(self):
	self.hide()
	return
    @QtCore.pyqtSlot()
    def rise(self):
        self.show()
        return

class TerminalViewer(QtGui.QWidget):
    def __init__(self,app,parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.Label = QtGui.QLabel("Waiting for Something",self)
        self.trayIcon = QtGui.QSystemTrayIcon(QtGui.QIcon("/tmp/ingweather/button.png"), app)
        self.menu = QtGui.QMenu()
        self.alarmAction = self.menu.addAction("Setup alarm")
        self.confAction = self.menu.addAction("Configure")
        self.exitAction = self.menu.addAction("Exit")
        self.trayIcon.setContextMenu(self.menu)

        self.DataCollector = TerminalX(self)
        self.connect(self.DataCollector,QtCore.SIGNAL("Activated ( QString ) "), self.Activated)
        self.DataCollector.start()

        self.trayIcon.show()
        self.exitAction.connect(self.exitAction, SIGNAL("triggered()"), app, SLOT("quit()"))

        self.connect(self.DataCollector,QtCore.SIGNAL("SetNewHum ( QString ) "), self.SetNewHum)
        #self.trayIcon.showMessage( "Warning", "Humidity increases", QtGui.QSystemTrayIcon.Warning, 10000)
        
        self.alarmClockWindow = AlarmWindow()
        self.alarmAction.connect(self.alarmAction, SIGNAL("triggered()"), self.alarmClockWindow, SLOT("rise()"))
    def Activated(self,newtext):
        self.Label.setText(newtext)
    def SetNewHum(self,Hum):
        GetHum()
        self.trayIcon.setIcon(QtGui.QIcon(Hum))
        print Hum
    def closeEvent(self,e):
        e.accept()
        app.exit()


class TerminalX(QtCore.QThread):
    def __init__(self,parent=None):
        QtCore.QThread.__init__(self,parent)

    def run(self):
        global timeout
        while True:
            time.sleep(timeout)
            self.emit(QtCore.SIGNAL("SetNewHum( QString )"),"/tmp/ingweather/button.png")
            print "################################################"


def main():
    GetHum()
    app = QtGui.QApplication(sys.argv)
    qb = TerminalViewer(app)
    sys.exit(app.exec_())



if __name__ == '__main__':
    main()
