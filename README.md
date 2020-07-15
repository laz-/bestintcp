# bestintcp
Home Assistant code for [Bestin](http://bestin.icontrols.co.kr/) IoT home
automation system (wallpad?). It speaks the (undocumented AFAIK) Bestin XML
over TCP protocol.

I am developing against an IHN-1020GL version tablet using HomeAssistant 0.112.

## Status
I'm still hacking on this and will snapshot to github as I progress.

Working:

- lights
- wall switches
- climate (read-only)

To implement:

- climate (write)
- fan
- elevator
- gas
- auto detection of rooms & devices vs requiring configuration

And maybe other stuff I find along the way. I'd really like to find the real
time energy consumption stats.

## Sotware Installation

    cd ~/.homeassistant/custom_components
    git clone https://github.com/laz-/bestintcp.git
    # code should now be in bestintcp/

You'll need the Python `xmltodict` module... `pip install`, `apt-get`, etc to
get your own copy

Then edit `configuration.yaml` and add something like:

    bestintcp:
            host: 192.168.50.200
            port: 10000
            rooms: living 1 2 3 4 5

I'll probably auto detect rooms, but haven't implemented it yet.

## Hardware Installation

You can get to the developer menu on the Android tablet by pushing the Settings
icon for 10 seconds and unlock with the code *5968*

This menu will conveniently tell you the IP address of your panel.

To connect to the tablet over the network you have to use ethernet (enabling
wifi doesn't seem to work on my tablet). I am pluging into the "LAN L2" port on
the gateway and bridging the network with a Raspberry Pi.

For now, see the pictures in the thread linked below.

## Development

Chat is happening in this forum thread:

- [Korea Home Assistant Naver Cafe - Bestin thread](https://cafe.naver.com/koreassistant/1160)

