BlueTunes
=========

Version 0.0.1 BETA

A Raspberry Pi GUI Bluetooth audio player
Copyright (c) 2021, Douglas Otwell
Distributed under the MIT license http://opensource.org/licenses/MIT

Bluetunes is a GUI application, written in Python and Tkinter.
It is not a media player. It will connect to the BlueZ MediaPlayer,
listen for D-Bus signals, and keep the screen synced to the player.
It also allows you to pause the stream, skip to the next track,
and adjust the volume from your desktop.

Caveats
-------

This is a BETA version of the software.

BlueTunes tries to access a remote service: performance 
depends in part on that service. In my experience, and 
using my Android phone, Amazon Music works perfectly, 
Spotify is (sadly) less capable. Please try your favorite 
media streamer.

Built and tested on a Raspberry Pi. But, I can't think why
it shouldn't run on any flavor of Linux with BlueZ.

Requirements
------------

*    BlueZ 5 (tested with BlueZ 5.50)
*    PulsaAudio (tested with PulseAudio 12.2)
*    The ability to stream audio from a Bluetooth
        source to the Pi (PulseAudio is all
        that's really needed here; configuration
        required on the Pi)

Installation
------------

    git clone https://github.com/douglas6/bluetunes.git
    cd bluetunes

Usage
-----

    python3 bluetunes.py
