#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
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
import re
import threading
import json
import urllib
from urllib.parse import urlparse

logger = logging.getLogger('Sonos')
sonos_speaker = {}

class UDPDispatcher(lib.connection.Server):
    def __init__(self, ip, port):
        lib.connection.Server.__init__(self, ip, port, proto='UDP')
        self.dest = 'udp:' + ip + ':' + port
        self.connect()

    def handle_connection(self):
        try:
            data, addr = self.socket.recvfrom(10000)
            ip = addr[0]
            addr = "{}:{}".format(addr[0], addr[1])
            logger.debug("{}: incoming connection from {}".format('sonos', addr))
        except Exception as e:
            logger.error("{}: {}".format(self._name, e))
            return

        try:
            sonos = json.loads(data.decode('utf-8').strip())
            uid = sonos['uid']

            if not uid:
                logger.error("No uid found in sonos udp response!\nResponse: {}")

            for key, value in sonos.items():
                instance_var = getattr(sonos_speaker[uid], key)

                if isinstance(instance_var, list):
                    for item in instance_var:
                        item(value, 'Sonos', '')

        except Exception as err:
            logger.error("Error parsing sonos broker response!\nError: {}".format(err))

class Sonos():
    def __init__(self, smarthome, host='0.0.0.0', port='9999', broker_url=None):

        if broker_url:
            self._broker_url = broker_url
        self.port = port
        self._sh = smarthome
        self.command = SonosCommand()
        self._sonoslock = threading.Lock()
        self._sh.scheduler.add('sonos-update', self._subscribe, cycle=120)
        self._sh.trigger('sonos-update', self._subscribe)
        UDPDispatcher(host, port)

    def run(self):
        self.alive = True

    def _subscribe(self):
        logger.debug('(re)registering to sonos broker server ...')
        self._send_cmd('client/subscribe/{}'.format(self.port))

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

                if command == 'mute':
                    cmd = self.command.mute(uid)
                if command == 'led':
                    cmd = self.command.led(uid)
                if command == 'play':
                    cmd = self.command.play(uid)
                if command == 'pause':
                    cmd = self.command.pause(uid)
                if command == 'stop':
                    cmd = self.command.stop(uid)
                if command == 'volume':
                    if isinstance(value, int):
                        cmd = self.command.volume(uid, int(value))
                if command == 'max_volume':
                    if isinstance(value, int):
                        cmd = self.command.max_volume(uid, int(value))
                if command == 'next':
                    cmd = self.command.next(uid)
                if command == 'previous':
                    cmd = self.command.previous(uid)
                if command == 'play_uri':
                    cmd = self.command.play_uri(uid, value)

                if command == 'play_snippet':

                    volume_item_name = '{}.volume'.format(item._name)
                    volume = -1
                    for child in item.return_children():
                        if child._name.lower() == volume_item_name.lower():
                            volume = child()
                            break
                    cmd = self.command.play_snippet(uid, value, volume)

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
                    cmd = self.command.play_tts(uid, value, language, volume)

                if command == 'seek':
                    if not re.match(r'^[0-9][0-9]?:[0-9][0-9]:[0-9][0-9]$', value):
                        logger.warning('invalid timestamp for sonos seek command, use HH:MM:SS format')
                        cmd = None
                    else:
                        cmd = self.command.seek(uid, value)
                if command == 'current_state':
                    cmd = self.command.current_state(uid)
                if command == 'join':
                    cmd = self.command.join(uid, value)
                if command == 'unjoin':
                    cmd = self.command.unjoin(uid)
                if command == 'partymode':
                    cmd = self.command.partymode(uid)
                if command == 'volume_up':
                    cmd = self.command.volume_up(uid)
                if command == 'volume_down':
                    cmd = self.command.volume_down(uid)
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
        return "v0.8.1\t2014-06-07"

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
        self.status =[]
        self.max_volume = []
        self.additional_zone_members = []

class SonosCommand():
    @staticmethod
    def join(uid, value):
        return "speaker/{}/join/{}".format(uid, value)

    @staticmethod
    def unjoin(uid):
        return "speaker/{}/unjoin".format(uid)

    @staticmethod
    def mute(uid):
        return "speaker/{}/mute".format(uid)

    @staticmethod
    def next(uid):
        return "speaker/{}/next".format(uid)

    @staticmethod
    def previous(uid):
        return "speaker/{}/previous".format(uid)

    @staticmethod
    def play(uid):
        return "speaker/{}/play".format(uid)

    @staticmethod
    def pause(uid):
        return "speaker/{}/pause".format(uid)

    @staticmethod
    def stop(uid):
        return "speaker/{}/stop".format(uid)

    @staticmethod
    def led(uid):
        return "speaker/{}/led".format(uid)

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