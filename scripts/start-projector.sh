#!/bin/bash

#xset -dpms
#xset s off
xset s noblank

xrandr --output HDMI-1 --rotate right --mode 800x480

matchbox-window-manager &

#vncviewer -FullScreen -ViewOnly -SendPrimary=0 -passwd ~/.vnc/passwd 192.168.0.75:5900
xterm -bg black cmatrix
