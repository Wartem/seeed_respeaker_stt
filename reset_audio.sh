#!/bin/bash

# Stop any running audio processes
sudo killall -9 pulseaudio 2>/dev/null
sudo killall -9 python3 2>/dev/null

# Reset ALSA
# sudo alsa force-reload

# Reset sound device permissions
# sudo chmod 666 /dev/snd/*

# Wait for device to settle
sleep 1

# Exit successfully
exit 0