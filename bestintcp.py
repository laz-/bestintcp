#!/usr/bin/python3

import sys
import time
import socket
import xmltodict
import logging

_LOGGER = logging.getLogger(__name__)

# socket.recv buffer size ... thankfully the connection is closed on exit, and
# I don't have to do something dumb like parse XML to find the end. This is
# more than big enough for all the RPCs I've sent... but you never know
READ_SIZE=4096

class BestinTCP():
    '''Quick class to encapsulate some of the XML over TCP protocol for the
    Bestin home automation system.
    
    It's only as complete as I needed it to be for Home Assistant integration.'''
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def request(self, request):
        _LOGGER.debug('Request --> %s' % request)
        # handle strings as inputs
        try:
            request = request.encode()
        except:
            pass

        mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mysocket.connect((self.host, self.port))

        mysocket.sendall(request)
        # XXX this will break for big responses
        response = mysocket.recv(READ_SIZE)
        if len(response) == READ_SIZE:
            _LOGGER.critical("Possibly incomplete read!")
        mysocket.close()

        # Korean characters in the response ... gotta decode to keep the peace
        try:
            response = response.decode('EUC-KR')
        except:
            pass

        _LOGGER.debug('Response <-- %s' % response)
        return response

    def XMLRequest(self, reqname, action, dev_num='null', unit_num='null', ctrl_action='null'):
        '''Send an XML request

        This is a subset of the true API ... but it's good enough for now'''

        request = ('<?xml version="1.0" encoding="utf-8"?>'
                   f'<imap ver = "1.0" address ="{self.host}" sender = "mobile">'
                   f'	<service type = "request" name = "{reqname}">'
                   '		<target name = "internet" id = "1" msg_no = "11"/>'
                   f'		<action>"{action}"</action>'
                   f'		<params dev_num = "{dev_num}" unit_num = "{unit_num}" ctrl_action = "{ctrl_action}"/>'
                   '	</service>'
                   '</imap>')
        return self.request(request)

    def ParseXMLResponse(self, response):
        '''Parse an XML response, return an array of resuts on success, or False on failure'''
        # Danger Will Robinson: early returns abound
        if not response:
            return False

        try:
            responsedict = xmltodict.parse(response)
            result = responsedict['imap']['service']['@result']
            if result != 'ok':
                _LOGGER.error("Failed RPC result: %s" % responsedict)
                return False
            else:
                return responsedict['imap']['service']['status_info']
        except:
            _LOGGER.critical("exeption in result parsing")

        return False


class BestinRoom():
    def __init__(self, name, tcp):
        self.name = name
        self.tcp = tcp

        self.lights = {}
        self.fetchLightsStatus()
        self.outlets = {}
        self.fetchOutletsStatus()
        self.heat_status = None
        self.heat_target_temp = None
        self.temperature = None
        self.fetchTemperStatus()

    def __repr__(self):
        return (f'BestinRoom(name="{self.name}", '
                f'lights={self.lights}, '
                f'outlets={self.outlets}, '
                f'temperature={self.temperature})')

    def _parseBestinSwitchResponse(self, response, outputdict={}):
        '''parse the response, results in return _AND_ passed argument
        outputdict
        
        The protocol uses the same response format for 'status' and 'control'
        actions, so we leech off the output like it's a status call and update
        all of the switches at once.
        '''
        status_info = self.tcp.ParseXMLResponse(response)
        if status_info == False:
            return {}

        for x in status_info:
            outputdict[x['@unit_num']] = x['@unit_status']

        return outputdict

    def _parseBestinTemperResponse(self, response):
        output = (None, None, None)
        status_info = self.tcp.ParseXMLResponse(response)
        if status_info == False:
            return output

        output = status_info['@unit_status'].split('/')
        return output

    def _livinglightswizzle(self):
        reqname = 'remote_access_light'
        devnum = self.name
        if self.name == 'living':
            reqname = 'remote_access_livinglight'
            devnum = 1
        return (reqname, devnum)

    def isLightOn(self, name):
        return self.lights[name] == 'on'

    def fetchLightsStatus(self):
        reqname, dev_num = self._livinglightswizzle()

        response = self.tcp.XMLRequest(reqname, 'status', dev_num=dev_num)
        self._parseBestinSwitchResponse(response, self.lights)

    def setLightStatus(self, unit_num, ctrl_action):
        assert(ctrl_action in ('on', 'off'))
        assert(unit_num in self.lights)

        reqname, dev_num = self._livinglightswizzle()
        response = self.tcp.XMLRequest(reqname, 'control', dev_num=dev_num, unit_num=unit_num, ctrl_action=ctrl_action)
        self._parseBestinSwitchResponse(response, self.lights)

    def fetchOutletsStatus(self):
        response = self.tcp.XMLRequest('remote_access_electric', 'status', dev_num=self.name)
        self._parseBestinSwitchResponse(response, self.outlets)

    def setOutletStatus(self, unit_num, ctrl_action):
        assert(ctrl_action in ('on', 'off'))
        assert(unit_num in self.outlets)

        response = self.tcp.XMLRequest('remote_access_electric', 'control', dev_num=self.name, unit_num=unit_num, ctrl_action=ctrl_action)
        self._parseBestinSwitchResponse(response, self.outlets)

    def isOutletOn(self, name):
        # TODO: state is usually unset/on or unset/off. What's unset? eco mode?
        if name not in self.outlets.keys():
            _LOGGER.error("outlet %s not in room %s" % (name, self))
            return False
        state = self.outlets[name].split('/')
        return state[1] == 'on'

    def fetchTemperStatus(self):
        response = self.tcp.XMLRequest('remote_access_temper', 'status', dev_num='1', unit_num=f"room{self.name}", ctrl_action='')
        temps = self._parseBestinTemperResponse(response)
        self.heat_status = temps[0]
        self.heat_target_temp = temps[1]
        self.temperature = temps[2]

    def setTemperStatus(self, onoff, temperature=None):
        assert(onoff in ('on', 'off'))
        if not temperature:
            temperature = self.heat_target_temp
        response = self.tcp.XMLRequest('remote_access_temper', 'control', dev_num='1', unit_num=f"room{self.name}", ctrl_action=f"{onoff}/{temperature}")
        temps = self._parseBestinTemperResponse(response)
        self.heat_status = temps[0]
        self.heat_target_temp = temps[1]
        self.temperature = temps[2]

    def isTemperOn(self):
        return self.heat_status == "on"


if __name__ == '__main__':
    import ipdb
    _LOGGER.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)

    h = BestinTCP('192.168.50.200', 10000)

    rooms = [
        BestinRoom('living', h),
        BestinRoom(1, h),
        #BestinRoom(2, h),
        #BestinRoom(3, h),
        #BestinRoom(4, h),
        #BestinRoom(5, h)
    ]

    for room in rooms:
        print(room)

    ipdb.set_trace()
