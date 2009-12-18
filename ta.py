#!/usr/bin/python
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


url = "http://catserver.ing.iac.es/weather/index.php?miniview=1"
timeout = 150


def wrNumb(Hum):
    im = Image.open("square-mask.png")
    font = ImageFont.truetype("dsfont.ttf", 96)
    draw = ImageDraw.Draw(im)
    # draw.line((0, 0) + im.size, fill=128)
    # draw.line((0, im.size[1], im.size[0], 0), fill=128)
    draw.text((5, 10), Hum, font=font, fill='red')
    del draw
    im.save('numb.png')



def creIma(Hum):
    wrNumb(Hum)
    highlight = Image.open('square.png')
    mask = Image.open('square-mask.png')
    icon = Image.open('numb.png').convert('RGBA')
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
 
    button.save('button.png')


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


class TerminalViewer(QtGui.QWidget):
    def __init__(self,app,parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.Label = QtGui.QLabel("Waiting for Something",self)
        self.trayIcon = QtGui.QSystemTrayIcon(QtGui.QIcon("button.png"), app)
        self.menu = QtGui.QMenu()
        self.exitAction = self.menu.addAction("Exit")
        self.trayIcon.setContextMenu(self.menu)

        self.DataCollector = TerminalX(self)
        self.connect(self.DataCollector,QtCore.SIGNAL("Activated ( QString ) "), self.Activated)
        self.DataCollector.start()

        self.trayIcon.show()
        self.exitAction.connect(self.exitAction, SIGNAL("triggered()"), app, SLOT("quit()"))
        self.connect(self.DataCollector,QtCore.SIGNAL("SetNewHum ( QString ) "), self.SetNewHum)
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
            self.emit(QtCore.SIGNAL("SetNewHum( QString )"),"button.png")
            print "################################################"


def main():
    GetHum()
    app = QtGui.QApplication(sys.argv)
    qb = TerminalViewer(app)
    sys.exit(app.exec_())



if __name__ == '__main__':
    main()
