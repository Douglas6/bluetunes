#!/usr/bin/env python3

"""Copyright (c) 2021, Douglas Otwell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import time
import logging
import threading
import queue
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GObject, GLib
import tkinter as tk

DBUS_OM_IFACE =         "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE =       "org.freedesktop.DBus.Properties"
BLUEZ_SERVICE_NAME =    "org.bluez"
MEDIA_PLAYER_IFACE =    BLUEZ_SERVICE_NAME + ".MediaPlayer1"
MEDIA_TRANSPORT_IFACE = BLUEZ_SERVICE_NAME + ".MediaTransport1"
MEDIA_CONTROL_IFACE =   BLUEZ_SERVICE_NAME + ".MediaControl1" # deprecated
MEDIA_DEVICE_IFACE =    BLUEZ_SERVICE_NAME + ".Device1"

PROGRAM_NAME =    "BlueTunes"
TXT_PLAY =        "Play"
TXT_PAUSE =       "Pause"
TXT_SKIP =        "Skip"
TXT_WAITING =     "Waiting for a Bluetooth Media Player"
TXT_VOL_UP =      "Up"
TXT_VOL_DN =      "Dn"

THEME_BKGD =        "#031E42"
THEME_TXT_COLOR =   "#ACA3FF"
THEME_BTN_COLOR =   "#2D32BC"
THEME_BTN_HILITE  = "#FFFFFF"

LOG_FILE =   "/home/pi/log-blueplayer.txt"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
LOG_LEVEL =  logging.DEBUG
#LOG_LEVEL =  logging.INFO

#logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL, filemode="w")
logging.basicConfig(stream=sys.stdout, format=LOG_FORMAT, level=LOG_LEVEL)

DBusGMainLoop(set_as_default=True)

class BlueListener(threading.Thread):
    """ register a signal handler on the BlueZ D-Bus and enter GLib MainLoop """
    pipeline = None

    def __init__(self, pipe):
        self.pipeline = pipe
        threading.Thread.__init__(self, daemon=True)

    def _propsChangedCb(self, iface, changed, invalidated):
        """ Place the interface and changed properties on the pipeline """
        self.pipeline.put({iface: changed})

    def run(self):
        """ Listen to DBUS signals and enter the GLib loop """
        receiver = bus.add_signal_receiver(
                self._propsChangedCb,
                bus_name = BLUEZ_SERVICE_NAME,
                dbus_interface = DBUS_PROP_IFACE,
                signal_name = "PropertiesChanged")
        GLib.MainLoop().run()

class BlueTunesWindow(tk.Tk):
    """ Build the BlueTunes window """
    titleVar =     None
    artistVar =    None
    playPauseVar = None
    waitFrame =    None
    mainFrame =    None

    def __init__(self):
        super().__init__()

        self.title(PROGRAM_NAME)
        self.geometry("500x46")
        self.resizable(True, False)
        self.titleVar = tk.StringVar(self, "")
        self.artistVar = tk.StringVar(self, "")
        self.playPauseVar = tk.StringVar(self, TXT_PLAY)

        # build wait frame
        self.waitFrame = tk.Frame(self, bd=0)
        self.waitFrame.pack(fill=tk.BOTH, expand=True)
        lblWait = FlatLabel(self.waitFrame, text=TXT_WAITING, font="Verdana 10")
        lblWait.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # build main frame
        self.mainFrame = tk.Frame(self, bd=0, bg=THEME_BKGD)
 #       self.mainFrame.pack(fill=tk.BOTH, expand=True)

        # build dashboard frame
        dashboardFrame = tk.Frame(self.mainFrame, bd=0, width=4)
        dashboardFrame.pack(side=tk.RIGHT, fill=tk.BOTH)

        btnPause = FlatButton(dashboardFrame, textvariable=self.playPauseVar, command=pause, width=6, font="Verdana 8").grid(row=0, column=0)
        btnSkip = FlatButton(dashboardFrame, text=TXT_SKIP, command=next, width=6, font="Verdana 8").grid(row=1, column=0)
        btnVolUp = FlatButton(dashboardFrame, text=TXT_VOL_UP, command=volumeUp, font="Verdana 8").grid(row=0, column=1)
        btnVolDn = FlatButton(dashboardFrame, text=TXT_VOL_DN, command=volumeDown, font="Verdana 8").grid(row=1, column=1)

        # build track frame
        trackFrame = tk.Frame(self.mainFrame, bd=0, bg=THEME_BKGD)
        trackFrame.bind("<Button-1>", refresh)
        trackFrame.pack(side=tk.LEFT, fill=tk.X)
        lblTitle = FlatLabel(trackFrame, textvariable=self.titleVar, font="Verdana 12", justify=tk.LEFT, padx=6).pack(anchor=tk.W)
        lblArtist = FlatLabel(trackFrame, textvariable=self.artistVar, font="Verdana 10", justify=tk.LEFT, padx=6).pack(anchor=tk.W)

        self.titleVar.set("")
        self.artistVar.set("")
        self.playPauseVar.set(TXT_PLAY)

    def setWindowTitle(self, title, name):
        if (name is not None and name != ""):
            title = "{} ({})".format(title, name)
        self.title(title)

    def setTrack(self, props):
        title = props["Title"] if "Title" in props else None
        artist = props["Artist"] if "Artist" in props else None
        album = props["Album"] if "Album" in props  else None

        if title is not None:
            self.titleVar.set(title)

        if artist is not None:
            if (album is not None and album != ""):
                artist += (" - " + album)
            self.artistVar.set(artist)

    def setPlayPause(self, str):
        self.playPauseVar.set(str)

    def gotoTrackFrame(self):
        self.waitFrame.forget()
        self.mainFrame.pack(fill=tk.BOTH, expand=True)
        self.update()

    def gotoWaitFrame(self):
        self.mainFrame.forget()
        self.waitFrame.pack(fill=tk.BOTH, expand=True)
        self.update()

class FlatButton(tk.Button):
    def __init__(self, parent, **args):
        tk.Button.__init__(self, parent, **args)
        self.config(fg=THEME_BTN_COLOR, bg=THEME_BKGD,
                activebackground=THEME_BKGD,
                activeforeground=THEME_BTN_HILITE,
                bd=0,
                highlightthickness=0,
                relief=tk.FLAT)

class FlatLabel(tk.Label):
    def __init__(self, parent, **args):
        tk.Label.__init__(self, parent, **args)
        self.config(fg=THEME_TXT_COLOR, bg=THEME_BKGD)

def getInterface(bus, iface):
    """ Return the (single) D-Bus Object found with the given interface """
    objects = []
    om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, "/"), DBUS_OM_IFACE)
    objs = om.GetManagedObjects()
    for obj, props in objs.items():
        if iface in props: objects.append(obj)

    if len(objects) == 0: return None
    if len(objects) == 1: return objects[0]

    logging.error("Multiple objects found for interface: {}".format(iface))

def handlePipeline():
    """ Remove any items from the pipeline and process them """
    global root, mediaTransport, mediaPlayer

    if not mediaPlayer:                                          # check for a media player
        mediaTransport, mediaPlayer = getTransportAndPlayer()
        if mediaPlayer:
            props = mediaPlayer.GetAll(MEDIA_PLAYER_IFACE, dbus_interface=DBUS_PROP_IFACE)
            if "Name" in props:
                root.setWindowTitle(PROGRAM_NAME, props["Name"])
            if "Status" in props:
                if props["Status"] == "playing": root.setPlayPause(TXT_PAUSE)
                else: root.setPlayPause(TXT_PLAY)
            if "Track" in props:
                root.setTrack(props["Track"])

            root.gotoTrackFrame()
    else:                                                        # remove and process items from the pipeline

        while not pipeline.empty():
            item = pipeline.get()
            if MEDIA_PLAYER_IFACE in item:                       # If the item has a media player interface:
                props = item[MEDIA_PLAYER_IFACE]                 #     Get its changed properties
                if "Track" in props:
                    logging.info("Updating track")
                    root.setTrack(props["Track"])
                if "Status" in props:
                    logging.debug("Media player Status: {}".format(props["Status"]))
                    if props["Status"] == "playing":
                        root.setPlayPause(TXT_PAUSE)
                    else:
                        root.setPlayPause(TXT_PLAY)
                if "Name" in props:
                    logging.debug("Media player Name: {}".format(props["Name"]))
                    root.setWindowTitle(PROGRAM_NAME, props["Name"])
                if "Position" in props:
                    #logging.debug("Media player Position: {}".format(props["Position"]))
                    pass
                root.update()                                     # Show updates

            elif MEDIA_TRANSPORT_IFACE in item:                   # if the item has a transport interface:
                props = item[MEDIA_TRANSPORT_IFACE]
                if "State" in props:
                    logging.debug("Media transport State: {}".format(props["State"]))
                    if props["State"] == "idle":
                        root.setPlayPause(TXT_PLAY)
                    if props["State"] == "active":
                        root.setPlayPause(TXT_PAUSE)
                    root.update()                                 # Show updates
                if "Volume" in props:
                    logging.debug("Media transport Volume: {}".format(props["Volume"]))

            elif MEDIA_DEVICE_IFACE in item:                      # if the item has a device interface:
                props = item[MEDIA_DEVICE_IFACE]
                if "Connected" in props:
                    logging.debug("The remote device is {}".format("connected" if props["Connected"] else "disconnected"))
                    if not props["Connected"]:
                        logging.info("The remote device disconnected")
                        #  wipe out the media player and go back to waiting
                        mediaTransport = None
                        mediaPlayer = None
                        root.setWindowTitle(PROGRAM_NAME, None)
                        root.gotoWaitFrame()

            elif MEDIA_CONTROL_IFACE in item:                     # if the item has a MediaControl interface:
                logging.debug("Media control properties changed") # (interface is deprecated)

            else:
                logging.warning("Missing information from pipeline: {}".format(item))


    root.after(1000, handlePipeline) # repeat every second

def getTransportAndPlayer():
    """ Find the BlueZ mediaTransport, mediaPlayer """
    global mediaTransport, mediaPlayer

    if not mediaTransport:
        # find a media transport
        path = getInterface(bus, MEDIA_TRANSPORT_IFACE)
        if not path: return (None, None)
        logging.info("Found a media transport at {}".format(path))
        mediaTransport = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, path), dbus_interface=MEDIA_TRANSPORT_IFACE)

    # find a media player
    path = getInterface(bus, MEDIA_PLAYER_IFACE)
    if not path: return (mediaTransport, None)

    logging.info("Found a media player at {}".format(path))
    mediaPlayer = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, path), dbus_interface=MEDIA_PLAYER_IFACE)

    return (mediaTransport, mediaPlayer)

def refresh(ev):
    logging.info("User refreshed")
    props = mediaPlayer.GetAll(MEDIA_PLAYER_IFACE, dbus_interface=DBUS_PROP_IFACE)
    if "Name" in props:
        root.setWindowTitle(PROGRAM_NAME, props["Name"])
    if "Status" in props:
        if props["Status"] == "playing": root.setPlayPause(TXT_PAUSE)
        else: root.setPlayPause(TXT_PLAY)
    if "Track" in props:
        root.setTrack(props["Track"])
    root.update()

def pause():
    """ Pause the media player """
    status = mediaPlayer.Get(MEDIA_PLAYER_IFACE, "Status", dbus_interface=DBUS_PROP_IFACE)

    if status == "playing":
        logging.info("User paused playing")
        mediaPlayer.Pause()
        root.setPlayPause(TXT_PLAY)
    else:
        logging.info("User started playing")
        mediaPlayer.Play()
        root.setPlayPause(TXT_PAUSE)
    root.update()

def next():
    """ Skip to the next track """
    logging.info("User skipped playing")

    mediaPlayer.Next()

def volumeUp():
    """ Raise the volume """
    logging.info("User raised the volume")
    vol = mediaTransport.Get(MEDIA_TRANSPORT_IFACE, "Volume", dbus_interface=DBUS_PROP_IFACE)
    vol = vol + 4 if vol < 124 else 127

    mediaTransport.Set(MEDIA_TRANSPORT_IFACE, "Volume", dbus.UInt16(vol), dbus_interface=DBUS_PROP_IFACE)

def volumeDown():
    """ Lower the volume """
    logging.info("User lowered the volume")
    vol = mediaTransport.Get(MEDIA_TRANSPORT_IFACE, "Volume", dbus_interface=DBUS_PROP_IFACE)
    vol = vol - 4 if vol > 4 else 0

    mediaTransport.Set(MEDIA_TRANSPORT_IFACE, "Volume", dbus.UInt16(vol), dbus_interface=DBUS_PROP_IFACE)


###
#  BlueTunes
###
logging.info("Started the {} media controller".format(PROGRAM_NAME))
mediaTransport = None
mediaPlayer = None
pipeline = queue.SimpleQueue()
root = None
bus = dbus.SystemBus()

# start tbe Bluetooth listener
logging.debug("Starting the Bluetooth listener")
listener = BlueListener(pipeline)
listener.start()

# get the root window
root = BlueTunesWindow()

# run the Tkinter main loop
logging.debug("Entering the Tkinter main loop")
root.after(100, handlePipeline)
root.mainloop()

logging.info("Exiting the {} media controller".format(PROGRAM_NAME))
