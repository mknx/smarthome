#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2012 KNX-User-Forum e.V.            http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.   http://smarthome.sourceforge.net/
#
#  SmartHome.py is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHome.py is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHome.py.  If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import logging
import threading
import mosquitto

logger = logging.getLogger()

class Plugin():

    def __init__(self, smarthome, host='127.0.0.1', port=1883):
        self._sh = smarthome
        self.broker_ip = host
        self.broker_port = int(port)
        self.clients = []
        self.items = {}
        self.logics = {}
        self.publisher = self.create_client('main')

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False
        for client in self.clients:
            logger.debug('Stopping mqtt client {0}'.format(client._client_id))
            client.loop_stop()

    def parse_item(self, item):
        if 'mqtt_topic' in item.conf:
            item.conf['mqtt_topic_in'] = item.conf['mqtt_topic']
            item.conf['mqtt_topic_out'] = item.conf['mqtt_topic']
            
        if 'mqtt_topic_in' in item.conf:
            client = self.create_client(item.id())
            client.on_message = lambda mosq, obj, msg : self.items[msg.topic](msg.payload, 'MQTT')
            client.subscribe(item.conf['mqtt_topic_in'], 0)
            client.loop_start()
            self.items[item.conf['mqtt_topic_in']] = item
            logger.debug('Item [{0}] is listening for messages on topic [{1}]'.format(item, item.conf['mqtt_topic_in']))
            
        if 'mqtt_topic_out' in item.conf:
            return self.update_item
            
    def parse_logic(self, logic):
        if 'mqtt_topic' in logic.conf:
            client = self.create_client(logic.name)
            client.on_message = lambda mosq, obj, msg : self.logics[msg.topic].trigger('MQTT', msg.topic, msg.payload)
            client.subscribe(logic.conf['mqtt_topic'], 0)
            client.loop_start()
            self.logics[logic.conf['mqtt_topic']] = logic
            logger.debug('Logic [{0}] is listening for messages on topic [{1}]'.format(logic.name, logic.conf['mqtt_topic']))

    def update_item(self, item, caller=None, source=None):
        self.publish(item.conf['mqtt_topic_out'], str(item()))
        
    def create_client(self, name):
        client = mosquitto.Mosquitto('{0}.{1}'.format(self._sh._hostname, name))
        client.connect(self.broker_ip, self.broker_port)            
        self.clients.append(client)
        return client
        
    def publish(self, topic, payload):
        self.publisher.publish(topic, str(payload))