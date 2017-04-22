#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
#########################################################################
#  This file is part of SmartHome.py.    http://mknx.github.io/smarthome/
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
#  along with SmartHome.py. If not, see <http://www.gnu.org/licenses/>.
#########################################################################

import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu, modbus_tcp
from time import sleep, time

# following not used here but needed for eval of config
import ctypes
import struct
import datetime

import logging

logger = logging.getLogger('modbus')


class Modbus():
    MODBUS_TYPES = {
        'Coil': {'read': cst.READ_COILS,
                 'write': cst.WRITE_MULTIPLE_COILS},
        'DiscreteInput': {'read': cst.READ_DISCRETE_INPUTS,
                          'write': None},
        'InputRegister': {'read': cst.READ_INPUT_REGISTERS,
                          'write': None},
        'HoldingRegister': {'read': cst.READ_HOLDING_REGISTERS,
                            'write': cst.WRITE_MULTIPLE_REGISTERS}
    }

    TIMER_TICK_INTERVAL = 1

    def __init__(self, smarthome, master_id, com_type, 
                 timeout=None, downTime=None,
                 tcp_ip='', tcp_port='502',
                 rtu_port='', rtu_baud=9600, rtu_bytesize=8, rtu_parity='N',
                 rtu_stopbits=1, rtu_xonxoff=0):
        """smarthome.py modbus plugin
        
        Args:
            smarthome (TYPE): sh object
            master_id (str): uniqu id to differentiate between different master
            com_type (TYPE): Modbus RTU or TCP {RTU, TCP}
            timeout (int, optional): timeout for request
            downTime (None, optional): timeout between reads
            tcp_ip (str, optional): slave ip
            tcp_port (str, optional): slave port
            rtu_port (str, optional): serial interface e.g.:/dev/ttyUSB0
            rtu_baud (int, optional): Baud
            rtu_bytesize (int, optional): bytesize
            rtu_parity (str, optional): parity
            rtu_stopbits (int, optional): stopbid
            rtu_xonxoff (int, optional): xonxoff
        """
        self._sh = smarthome

        self._connected = False
        self._dataPoints = []

        self._readErrorCount = 0
        self._writeErrorCount = 0

        # unique master id in case there are more eg. RTU and TCP
        self._master_id = str(master_id)
        self._com_type = str(com_type)
        self._timeout = None
        if timeout is None:
            if self._com_type == 'RTU':
                self._timeout = .05
            elif self._com_type == 'TCP':
                self._timeout = 1
        else:
            self._timeout = float(timeout)

        self._downTime = None
        if downTime is None:
            if self._com_type == 'RTU':
                self._downTime = .05
            elif self._com_type == 'TCP':
                self._downTime = .01
        else:
            self._downTime = float(downTime)

        self._tcp_ip = str(tcp_ip)
        self._tcp_port = int(tcp_port)

        self._rtu_port = str(rtu_port)
        self._rtu_baud = int(rtu_baud)
        self._rtu_bytesize = int(rtu_bytesize)
        self._rtu_parity = str(rtu_parity)
        self._rtu_stopbits = int(rtu_stopbits)
        self._rtu_xonxoff = str(rtu_xonxoff)

        self._master = None  # Modbus Master RTU or TCP
        if self._com_type == 'RTU':
            self._master = self._create_ModbusRTU_Master()
        elif self._com_type == 'TCP':
            self._master = self._create_ModbusTCP_Master()
        else:
            logger.error("Modbus com_type ({}) not implemented"
                         .format(self._com_type))
        self._master.set_verbose(True)

    def _create_ModbusTCP_Master(self):
        master = None
        try:
            master = modbus_tcp.TcpMaster(host=self._tcp_ip,
                                          port=self._tcp_port)
            master.set_timeout(self._timeout)
            # master.open()
            self._connected = True
            logger.info("Modbus TCP Master successfully created.")
        except modbus_tk.modbus.ModbusError as exc:
            logger.error("ModbusRTU Master creation faild: {}"
                         .format(exc))
        return master

    def _create_ModbusRTU_Master(self):
        import serial  # require pyserial only if used
        master = None
        try:
            serialPort = serial.Serial(port=self._rtu_port,
                                       baudrate=self._rtu_baud,
                                       bytesize=self._rtu_bytesize,
                                       parity=self._rtu_parity,
                                       stopbits=self._rtu_stopbits,
                                       xonxoff=self._rtu_xonxoff)
            master = modbus_rtu.RtuMaster(serialPort)
            master.set_timeout(self._timeout)
            # master.open()
            self._connected = True
            logger.info("Modbus RTU Master successfully created.")

        except serial.SerialException as exc:
            logger.error("Opening serial port for ModbusRTU faild: {}"
                         .format(exc))
        except modbus_tk.modbus.ModbusError as exc:
            serialPort.close()
            logger.error("ModbusRTU Master creation faild: {}"
                         .format(exc))
        return master

    def run(self):
        self.alive = True
        tickTimerName = 'TT_' + self._master_id
        self._sh.scheduler.add(tickTimerName, self.__timer_tick, prio=3,
                               cron=None, cycle=self.TIMER_TICK_INTERVAL,
                               value=None, offset=None, next=None)
        readLoopName = 'RL_' + self._master_id
        self._sh.scheduler.add(readLoopName, self.__read_loop, prio=3,
                               cron='init', cycle=None,
                               value=None, offset=None, next=None)

        for dp in self._dataPoints:
            logger.debug('Modbus Data Point: {}'
                         .format(self.__data_point_to_string(dp)))

    def stop(self):
        self._master.close()
        self._connected = False
        self.alive = False

    def __read_loop(self):
        logger.debug("Modbus read loop started. {}"
                     .format(self._master_id))
        while self.alive:
            readStartTime = time()
            self._read_datapoints()
            readTime = time() - readStartTime
            sleepTime = self.TIMER_TICK_INTERVAL - readTime
            if readTime > self.TIMER_TICK_INTERVAL:
                logger.warning("Modbus readloop needed: {:.2f} s for the "
                               "read. This should be less then {:.2f} s."
                               .format(readTime,
                                       self.TIMER_TICK_INTERVAL))
            if sleepTime > 0:
                sleep(sleepTime)

    def __timer_tick(self):
        for dataPoint in self._dataPoints:
            if dataPoint['read_interval'] is not None:
                dataPoint['current_time'] -= 1

    def _read_datapoints(self):
        # reads all datapoints with timer <=0
        for dataPoint in self._dataPoints:
            if (dataPoint['init'] and  # to read every dp at least once
                    (dataPoint['read_interval'] is None or
                     dataPoint['read_interval'] < 0)):
                continue
            if (not dataPoint['init'] or  # if not initalise yet
                    dataPoint['current_time'] <= 0):
                # if not dataPoint['init']:
                #     
                dataPoint['init'] = True
                val = self._read_datapoint(dataPoint)
                dataPoint['item'](val,
                                  dataPoint['master_id'],
                                  self.__data_point_to_string(dataPoint),
                                  None)
                dataPoint['current_time'] = dataPoint['read_interval']

    def __data_point_to_string(self, dataPoint):
        return ("{}, {}, slave#{}, addr {}, len {}"
                .format(str(dataPoint['item']),
                        dataPoint['master_id'],
                        dataPoint['slave_nr'],
                        dataPoint['addr'],
                        dataPoint['length']))

    def __manage_lost_connection(self, dataPoint):
        logger.debug("Modbus handle lost connection.")
        if hasattr(self._master, '_serial'):
            logger.debug("Modbus flush serial buffer.")
            try:
                if self._master._serial.isOpen():
                    self._master._serial.flushInput()
                    self._master._serial.flushOutput()
            except Exception as exc:
                logger.error("Faild flushing serial buffers {}"
                             .format(exc))
        self._master.close()
        for dp in self._dataPoints:
            if (dp['slave_nr'] == dataPoint['slave_nr']):
                logger.debug("Modbus reset datapoint for init Read: {}"
                             .format(self.__data_point_to_string(dp)))
                dp['init'] = False

    def _read_datapoint(self, dataPoint):
        val = None
        try:
            val = self._master.execute(
                dataPoint['slave_nr'],
                self.MODBUS_TYPES[dataPoint['type']]['read'],
                dataPoint['addr'],
                dataPoint['length'])
            val = dataPoint['unpack'](val)
            logger.debug("Modbus item read: {}. val: {}"
                         .format(str(dataPoint['item']),
                                 str(val)))
            sleep(self._downTime)
        # exceptins for telegram problems
        except (modbus_tk.modbus.ModbusInvalidResponseError,
                modbus_tk.modbus.ModbusError) as exc:
            self._readErrorCount += 1
            self.__manage_lost_connection(dataPoint)
            logger.error("Fail reading modbus value. Bad telegram: {}. {}"
                         .format(self.__data_point_to_string(dataPoint),
                                 exc))
            logger.warning("Accumulated modbus read error count: {}"
                           .format(self._readErrorCount))
        # exceptions for connection problems
        # if this happens connection is considerd lost
        except (ConnectionResetError,
                ConnectionRefusedError,
                Exception) as exc:  # For undefind pyserial exceptions
            self.__manage_lost_connection(dataPoint)
            logger.error("Modbus connection faild while reading: {}. {}"
                         .format(self.__data_point_to_string(dataPoint),
                                 exc))
        return val

    def _write_datapoint(self, dataPoint, val):
        try:
            _val = dataPoint['pack'](val)
            self._master.execute(
                dataPoint['slave_nr'],
                self.MODBUS_TYPES[dataPoint['type']]['write'],
                dataPoint['addr'],
                output_value=_val)

            logger.debug("Modbus item write: {}. val: {}"
                         .format(str(dataPoint['item']),
                                 str(_val)))
            sleep(self._downTime)
        # exceptins for telegram problems
        except (modbus_tk.modbus.ModbusInvalidResponseError,
                modbus_tk.modbus.ModbusError) as exc:
            self._writeErrorCount += 1
            logger.error("Fail writing modbus value. Bad telegram: {}. {}"
                         .format(self.__data_point_to_string(dataPoint),
                                 exc))
            logger.warning("Accumulated modbus write error count: {}"
                           .format(self._writeErrorCount))
            self.__manage_lost_connection(dataPoint)
        # exceptions for connection problems 
        # if this happens connection is considerd lost
        except (ConnectionResetError,
                ConnectionRefusedError,
                Exception) as exc:  # For undefind pyserial exceptions
            logger.error("Modbus connection faild while writing: {}. {}"
                         .format(self.__data_point_to_string(dataPoint),
                                 exc))
            self.__manage_lost_connection(dataPoint)

    def parse_item(self, item):
        dataPoint = {
            'item': None,
            'master_id': None,
            'slave_nr': None,
            'addr': None,
            'length': None,
            'type': None,
            'unpack': lambda x: x,  # lambda function
            'pack': lambda x: x,  # lambda function
            'read_interval': None,
            'current_time': -1,  # counts down and if <0 reading is done
            'init': False  # is set to True if read once. 
        }

        param = 'modbus_addr'
        if param in item.conf:
            modbus_addr = item.conf[param]
            dataPoint['master_id'] = str(modbus_addr[0])
            dataPoint['slave_nr'] = int(modbus_addr[1])
            dataPoint['addr'] = int(modbus_addr[2])
            dataPoint['length'] = int(modbus_addr[3])

        param = 'modbus_type'
        if param in item.conf:
            dataPoint['type'] = str(item.conf[param])

        param = 'modbus_readInterval'
        if param in item.conf:
            dataPoint['read_interval'] = int(item.conf[param])

        def __reverseListOp(param):
            # reversing list building of smarthome.py config parser for the
            # binary or opperator |
            if isinstance(param, list):
                return (' | '.join(param))
            else:
                return param

        param = 'modbus_pack'
        if param in item.conf:
            dataPoint['pack'] = eval(__reverseListOp(item.conf[param]))

        param = 'modbus_unpack'
        if param in item.conf:
            dataPoint['unpack'] = eval(__reverseListOp(item.conf[param]))


        if self._master_id == dataPoint['master_id']:
            dataPoint['item'] = item
            self._dataPoints.append(dataPoint)
            return self.update_item
        else:
            return None

    def update_item(self, item, caller=None, source=None, dest=None):
        if caller != self._master_id:
            logger.info("update item: {0}".format(item.id()))
            datapoint = next(datapoint for datapoint in 
                             self._dataPoints if datapoint['item'] == item)
            self._write_datapoint( datapoint, item())


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    myplugin = Modbus('smarthome-dummy')
    myplugin.run()
