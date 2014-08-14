#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
# ########################################################################
# Copyright 2013 KNX-User-Forum e.V. http://knx-user-forum.de/
#########################################################################
# This file is part of SmartHome.py. http://mknx.github.io/smarthome/
#
# SmartHome.py is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SmartHome.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################
import http
import logging
import lib.connection
import lib.tools
import os
import re
import socket
import threading
import json
import urllib
from urllib.parse import urlparse
import fcntl
import struct

logger = logging.getLogger('')
sonos_speaker = {}


class UDPDispatcher(lib.connection.Server):
    def __init__(self, ip, port):
        lib.connection.Server.__init__(self, ip, port, proto='UDP')
        self.dest = 'udp:' + ip + ':{port}'.format(port=port)
        logger.debug('starting udp listener with {url}'.format(url=self.dest))

        self.connect()

    def handle_connection(self):
        try:
            data, address = self.socket.recvfrom(10000)
            address = "{}:{}".format(address[0], address[1])
            logger.debug("{}: incoming connection from {}".format('sonos', address))
        except Exception as err:
            logger.error("{}: {}".format(self._name, err))
            return

        try:
            sonos = json.loads(data.decode('utf-8').strip())
            uid = sonos['uid']

            if not uid:
                logger.error("No uid found in sonos udp response!\nResponse: {}")
            if uid not in sonos_speaker:
                logger.warning("no sonos speaker configured with uid '{uid}".format(uid=uid))
                return

            for key, value in sonos.items():
                instance_var = getattr(sonos_speaker[uid], key)

                if isinstance(instance_var, list):
                    for item in instance_var:
                        item(value, 'Sonos', '')

        except Exception as err:
            logger.error("Error parsing sonos broker response!\nError: {}".format(err))


class Sonos():
    def __init__(self, smarthome, listen_host='0.0.0.0', listen_port=9999, broker_url=None, refresh=120):

        if broker_url:
            self._broker_url = broker_url
        else:
            self._broker_url = "{ip}:12900".format(ip=get_lan_ip())
            if self._broker_url:
                logger.warning("No broker url given, assuming current ip and default broker port: {url}".
                               format(url=self._broker_url))
            else:
                logger.error("Could not detect broker url !!!")
                return

        self._listen_host = listen_host
        self._listen_port = listen_port
        self._sh = smarthome
        self._command = SonosCommand()
        self._sonoslock = threading.Lock()
        self._sh.scheduler.add('sonos-update', self._subscribe, cycle=refresh)

        logger.debug('refresh sonos speakers every {refresh} seconds'.format(refresh=refresh))

        self._sh.trigger('sonos-update', self._subscribe)
        UDPDispatcher(self._listen_host, self._listen_port)

    def run(self):
        self.alive = True

    def _subscribe(self):
        logger.debug('(re)registering to sonos broker server ...')
        self._send_cmd('client/subscribe/{}'.format(self._listen_port))

        for uid, speaker in sonos_speaker.items():
            self._send_cmd(SonosCommand.current_state(uid))

    def stop(self):
        self.alive = False

    def _resolve_uid(self, item):
        uid = None

        parent_item = item.return_parent()
        if (parent_item is not None) and ('sonos_uid' in parent_item.conf):
            uid = parent_item.conf['sonos_uid'].lower()
        else:
            logger.warning("sonos: could not resolve sonos_uid".format(item))
        return uid

    def parse_item(self, item):

        if 'sonos_recv' in item.conf:
            uid = self._resolve_uid(item)

            if uid is None:
                return None
            attr = item.conf['sonos_recv']

            logger.debug("sonos: {} receives updates by {}".format(item, attr))

            if not uid in sonos_speaker:
                sonos_speaker[uid] = SonosSpeaker()

            attr_list = getattr(sonos_speaker[uid], attr)

            if not item in attr_list:
                attr_list.append(item)

        if 'sonos_send' in item.conf:
            try:
                self._sonoslock.acquire()
                uid = self._resolve_uid(item)
                if uid is None:
                    return None

                attr = item.conf['sonos_send']
                logger.debug("sonos: {} is send to {}".format(item, attr))
                return self._update_item
            finally:
                self._sonoslock.release()

        return None

    #nothing yet
    def parse_logic(self, logic):
        pass

    def _update_item(self, item, caller=None, source=None, dest=None):
        if caller != 'Sonos':
            value = item()

            if 'sonos_send' in item.conf:
                uid = self._resolve_uid(item)

                if not uid:
                    return None
                command = item.conf['sonos_send']

                cmd = ''

                if command == 'mute':
                    if isinstance(value, bool):
                        cmd = self._command.mute(uid, value)
                if command == 'led':
                    if isinstance(value, bool):
                        cmd = self._command.led(uid, value)
                if command == 'play':
                    if isinstance(value, bool):
                        cmd = self._command.play(uid, value)
                if command == 'pause':
                    if isinstance(value, bool):
                        cmd = self._command.pause(uid, value)
                if command == 'stop':
                    if isinstance(value, bool):
                        cmd = self._command.stop(uid, value)
                if command == 'volume':
                    if isinstance(value, int):
                        cmd = self._command.volume(uid, int(value))
                if command == 'max_volume':
                    if isinstance(value, int):
                        cmd = self._command.max_volume(uid, int(value))
                if command == 'bass':
                    if isinstance(value, int):
                        cmd = self._command.bass(uid, int(value))
                if command == 'treble':
                    if isinstance(value, int):
                        cmd = self._command.treble(uid, int(value))
                if command == 'loudness':
                    if isinstance(value, bool):
                        cmd = self._command.loudness(uid, value)
                if command == 'playmode':
                    value = value.lower().strip('\'').strip('\"')
                    if value in ['normal', 'shuffle_norepeat', 'shuffle', 'repeat_all']:
                        cmd = self._command.playmode(uid, value)
                    else:
                        logger.warning(
                            "Ignoring PLAYMODE command. Value {value} not a valid paramter!".format(value=value))
                if command == 'next':
                    cmd = self._command.next(uid)
                if command == 'previous':
                    cmd = self._command.previous(uid)
                if command == 'play_uri':
                    cmd = self._command.play_uri(uid, value)
                if command == 'play_snippet':
                    volume_item_name = '{}.volume'.format(item._name)
                    volume = -1
                    for child in item.return_children():
                        if child._name.lower() == volume_item_name.lower():
                            volume = child()
                            break
                    cmd = self._command.play_snippet(uid, value, volume)

                if command == 'play_tts':
                    volume_item_name = '{}.volume'.format(item._name)
                    language_item_name = '{}.language'.format(item._name)
                    volume = -1
                    language = 'de'
                    for child in item.return_children():
                        if child._name.lower() == volume_item_name.lower():
                            volume = child()
                        if child._name.lower() == language_item_name.lower():
                            language = child()
                    cmd = self._command.play_tts(uid, value, language, volume)

                if command == 'seek':
                    if not re.match(r'^[0-9][0-9]?:[0-9][0-9]:[0-9][0-9]$', value):
                        logger.warning('invalid timestamp for sonos seek command, use HH:MM:SS format')
                        cmd = None
                    else:
                        cmd = self._command.seek(uid, value)
                if command == 'current_state':
                    cmd = self._command.current_state(uid)
                if command == 'join':
                    cmd = self._command.join(uid, value)
                if command == 'unjoin':
                    cmd = self._command.unjoin(uid)
                if command == 'partymode':
                    cmd = self._command.partymode(uid)
                if command == 'volume_up':
                    cmd = self._command.volume_up(uid)
                if command == 'volume_down':
                    cmd = self._command.volume_down(uid)
                if cmd:
                    self._send_cmd(cmd)
        return None

    def _send_cmd(self, cmd):

        try:
            conn = http.client.HTTPConnection(self._broker_url)
            conn.request("GET", cmd)
            response = conn.getresponse()
            if response.status == 200:
                logger.info("Sonos: Message %s %s successfully sent - %s %s" %
                            (self._broker_url, cmd, response.status, response.reason))
            else:
                logger.warning("Sonos: Could not send message %s %s - %s %s" %
                               (self._broker_url, cmd, response.status, response.reason))
            data = response.read()
            conn.close()

        except Exception as e:
            logger.warning(
                "Could not send sonos notification: {0}. Error: {1}".format(cmd, e))

        logger.debug("Sending request: {0}".format(cmd))

    def _send_cmd_response(self, cmd):
        try:
            data = ''
            conn = http.client.HTTPConnection(self._broker_url)

            conn.request("GET", cmd)
            response = conn.getresponse()
            if response.status == 200:
                logger.info("Sonos: Message %s %s successfully sent - %s %s" %
                            (self._broker_url, cmd, response.status, response.reason))
                data = response.read()
            else:
                logger.warning("Sonos: Could not send message %s %s - %s %s" %
                               (self._broker_url, cmd, response.status, response.reason))
            conn.close()
            return data

        except Exception as e:
            logger.warning(
                "Could not send sonos notification: {0}. Error: {1}".format(cmd, e))

        logger.debug("Sending request: {0}".format(cmd))

    def get_favorite_radiostations(self, start_item=0, max_items=50):
        return self._send_cmd_response(SonosCommand.favradio(start_item, max_items))

    def version(self):
        return "v1.0\t2014-07-08"


class SonosSpeaker():
    def __init__(self):
        self.uid = []
        self.ip = []
        self.model = []
        self.zone_name = []
        self.zone_icon = []
        self.serial_number = []
        self.software_version = []
        self.hardware_version = []
        self.mac_address = []
        self.playlist_position = []
        self.volume = []
        self.mute = []
        self.led = []
        self.streamtype = []
        self.stop = []
        self.play = []
        self.pause = []
        self.track_title = []
        self.track_artist = []
        self.track_duration = []
        self.track_position = []
        self.track_album_art = []
        self.track_uri = []
        self.radio_station = []
        self.radio_show = []
        self.status = []
        self.max_volume = []
        self.additional_zone_members = []
        self.bass = []
        self.treble = []
        self.loudness = []
        self.playmode = []


class SonosCommand():
    @staticmethod
    def join(uid, value):
        return "speaker/{}/join/{}".format(uid, value)

    @staticmethod
    def unjoin(uid):
        return "speaker/{}/unjoin".format(uid)

    @staticmethod
    def mute(uid, value):
        return "speaker/{uid}/mute/{value}".format(uid=uid, value=int(value))

    @staticmethod
    def next(uid):
        return "speaker/{}/next".format(uid)

    @staticmethod
    def previous(uid):
        return "speaker/{}/previous".format(uid)

    @staticmethod
    def play(uid, value):
        return "speaker/{uid}/play/{value}".format(uid=uid, value=int(value))

    @staticmethod
    def pause(uid, value):
        return "speaker/{uid}/pause/{value}".format(uid=uid, value=int(value))

    @staticmethod
    def stop(uid, value):
        return "speaker/{uid}/stop/{value}".format(uid=uid, value=int(value))

    @staticmethod
    def led(uid, value):
        return "speaker/{uid}/led/{value}".format(uid=uid, value=int(value))

    @staticmethod
    def volume(uid, value):
        return "speaker/{}/volume/{}".format(uid, value)

    @staticmethod
    def volume_up(uid):
        return "speaker/{}/volume_up".format(uid)

    @staticmethod
    def volume_down(uid):
        return "speaker/{}/volume_down".format(uid)

    @staticmethod
    def max_volume(uid, value):
        return "speaker/{}/maxvolume/{}".format(uid, value)

    @staticmethod
    def seek(uid, value):
        return "speaker/{}/seek/{}".format(uid, value)

    @staticmethod
    def play_uri(uid, uri):
        uri = urllib.parse.quote_plus(uri, '&%=')
        return "speaker/{}/play_uri/{}".format(uid, uri)

    @staticmethod
    def play_snippet(uid, uri, volume):
        uri = urllib.parse.quote_plus(uri, '&%=')
        return "speaker/{}/play_snippet/{}/{}".format(uid, uri, volume)

    @staticmethod
    def play_tts(uid, uri, language, volume):
        uri = urllib.parse.quote_plus(uri, '&%=')
        return "speaker/{}/play_tts/{}/{}/{}".format(uid, uri, language, volume)

    @staticmethod
    def current_state(uid):
        return "speaker/{}/current_state".format(uid)

    @staticmethod
    def partymode(uid):
        return "speaker/{}/partymode".format(uid)

    @staticmethod
    def bass(uid, value):
        return "speaker/{uid}/bass/{value}".format(uid=uid, value=value)

    @staticmethod
    def playmode(uid, value):
        return "speaker/{uid}/playmode/{value}".format(uid=uid, value=value)

    @staticmethod
    def treble(uid, value):
        return "speaker/{uid}/treble/{value}".format(uid=uid, value=value)

    @staticmethod
    def loudness(uid, value):
        return "speaker/{uid}/loudness/{value}".format(uid=uid, value=int(value))

    @staticmethod
    def get_uid_from_response(dom):
        try:
            return dom.attributes["uid"].value.lower()
        except:
            return None

    @staticmethod
    def favradio(start_item, max_items):
        try:
            start_item = int(start_item)
        except ValueError:
            logger.error('favradio: command ignored - start_item value \'{}\' is not an integer'.format(start_item))
            return
        str_start_item = '/{}'.format(start_item)

        try:
            max_items = int(max_items)
        except ValueError:
            logger.error('favradio: command ignored - max_items value \'{}\' is not an integer'.format(max_items))
            return
        str_max_items = '/{}'.format(max_items)
        logger.debug("library/favradio{}{}".format(str_start_item, str_max_items))
        return "library/favradio{}{}".format(str_start_item, str_max_items)


#######################################################################
# UTIL FUNCTIONS
#######################################################################

def get_interface_ip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15].encode('utf-8')))[20:24])


def get_lan_ip():
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip.startswith("127.") and os.name != "nt":
            interfaces = ["eth0", "eth1", "eth2", "wlan0", "wlan1", "wifi0", "ath0", "ath1", "ppp0"]
            for ifname in interfaces:
                try:
                    ip = get_interface_ip(ifname)
                    break
                except IOError:
                    pass
        return ip
    except Exception as err:
        logger.exception(err)
        return None
