# bestintcp
Home Assistant code for Bestin IoT panel system (wallpad?)

## Status
I'm still hacking on this and will snapshot to github.

Lights and switches currently work. I'll probably get to:

- temperature sensor / thermostat climate
- fan
- elevator
- gas

And maybe other stuff I find along the way. I'd really like to find the real
time energy consumption stats.

## Installation

    cd ~/.homeassistant/custom_components
    git clone ...

You'll need the Python `xmltodict` module also... `pip install`, `apt-get`, etc
to get your own copy

Then edit `configuration.yaml` and add something like:

    bestintcp:
            host: 192.168.50.200
            port: 10000
            rooms: living 1 2 3 4 5
    
