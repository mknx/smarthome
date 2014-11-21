#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab

import serial
import os
import sys
import logging
import struct
import time
import threading

#CO_RD_VERSION 3

FCSTAB = [
    0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15,
    0x38, 0x3f, 0x36, 0x31, 0x24, 0x23, 0x2a, 0x2d,
    0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65,
    0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d,
    0xe0, 0xe7, 0xee, 0xe9, 0xfc, 0xfb, 0xf2, 0xf5,
    0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd,
    0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85,
    0xa8, 0xaf, 0xa6, 0xa1, 0xb4, 0xb3, 0xba, 0xbd,
    0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2,
    0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea,
    0xb7, 0xb0, 0xb9, 0xbe, 0xab, 0xac, 0xa5, 0xa2,
    0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a,
    0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32,
    0x1f, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0d, 0x0a,
    0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42,
    0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a,
    0x89, 0x8e, 0x87, 0x80, 0x95, 0x92, 0x9b, 0x9c,
    0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4,
    0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec,
    0xc1, 0xc6, 0xcf, 0xc8, 0xdd, 0xda, 0xd3, 0xd4,
    0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c,
    0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44,
    0x19, 0x1e, 0x17, 0x10, 0x05, 0x02, 0x0b, 0x0c,
    0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34,
    0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b,
    0x76, 0x71, 0x78, 0x7f, 0x6A, 0x6d, 0x64, 0x63,
    0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b,
    0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13,
    0xae, 0xa9, 0xa0, 0xa7, 0xb2, 0xb5, 0xbc, 0xbb,
    0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8D, 0x84, 0x83,
    0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb,
    0xe6, 0xe1, 0xe8, 0xef, 0xfa, 0xfd, 0xf4, 0xf3
    ]

PACKET_SYNC_BYTE = 0x55

PACKET_TYPE_RADIO = 0x01
PACKET_TYPE_RESPONSE = 0x02
PACKET_TYPE_COMMON_COMMAND = 0x05
PACKET_TYPE_RADIO_MESSAGE = 0x09

CO_WR_RESET = 0x02
CO_RD_VERSION = 0x03
CO_RD_IDBASE = 0x08

logger = logging.getLogger('EnOcean')

class EnOcean():
    
    def __init__(self, smarthome, serialport):
        self._sh = smarthome
        self.port = serialport
        self._tcm = serial.Serial(serialport, 57600, timeout=0.5)
        self._cmd_lock = threading.Lock()
        self._response_lock = threading.Condition()
        self._rx_items = {}

    def _parse_eep_A5_3F_7F(self, payload):
        #logger.debug("enocean: processing A5_3F_7F")
        results = {'DI_3': (payload[3] & 1<<3) == 1<<3, 'DI_2': (payload[3] & 1<<2) == 1<<2, 'DI_1': (payload[3] & 1<<1) == 1<<1, 'DI_0': (payload[3] & 1<<0) == 1<<0}
        results['AD_0'] = (((payload[1] & 0x03) << 8) + payload[2]) * 1.8 / pow(2,10) 
        results['AD_1'] = (payload[1] >> 2) * 1.8 / pow(2,6) 
        results['AD_2'] = payload[0] * 1.8 / pow(2,8) 
        return results
        
    # fuer MarcoLanghans
    def _parse_eep_A5_38_08(self, payload):
        results = {}
        if (payload[1] == 2): # Dimming
            results['EDIM'] = payload[2]
            results['RMP'] = payload[3]
            results['LRNB'] = ((payload[4] & 1<<3) == 1<<3)
            results['EDIM_R'] = ((payload[4] & 1<<2) == 1<<2)
            results['STR'] = ((payload[4] & 1<<1) == 1<<1)
            results['SW'] = ((payload[4] & 1<<0) == 1<<0)
        return results
    
    def _parse_eep_F6_02_02(self, payload):
        #logger.debug("enocean: processing A5_3F_7F")
        results = {'A1': (payload[0] == 16), 'A0': (payload[0] == 48), 'B1': (payload[0] == 80), 'B0': (payload[0] == 112), 'A1B1': (payload[0] == 21), 'A0B0': (payload[0] == 21)}
        return results
    
    def _parse_eep_F6_10_00(self, payload):
        #logger.debug("enocean: processing A5_3F_7F")
        results = {'VAL': (payload[0] & 0xf0)}
        return results
    
    def eval_telegram(self, sender_id, data, opt):
        for item in self._items:
            # validate id for item id:
            if item.conf['enocean_id'] == sender_id:
                #print ("validated {0} for {1}".format(sender_id,item))
                #print ("try to get value for: {0} and {1}".format(item.conf['enocean_rorg'][0],item.conf['enocean_rorg'][1]))
                rorg = item.conf['enocean_rorg']
                eval_value = item.conf['enocean_value']
                if rorg in RADIO_PAYLOAD_VALUE: #check if RORG exists
                    pl = eval(RADIO_PAYLOAD_VALUE[rorg]['payload_idx'])
                    #could be nicer
                    for entity in RADIO_PAYLOAD_VALUE: 
                        if (rorg == entity) and (eval_value in RADIO_PAYLOAD_VALUE[rorg]['entities']):
                            value_dict = RADIO_PAYLOAD_VALUE[rorg]['entities']
                            value = eval(RADIO_PAYLOAD_VALUE[rorg]['entities'][eval_value])
                            #print ("Resulting value: {0} for {1}".format(value,item))
                            if value: # not shure about this
                                item(value, 'EnOcean', 'RADIO')
                        
                                
    def _process_packet_type_radio(self, data, optional):                      
        #logger.warning("enocean: processing radio message with data = [{}] / optional = [{}]".format(', '.join(['0x%02x' % b for b in data]), ', '.join(['0x%02x' % b for b in optional])))
        
        choice = data[0]
        payload = data[1:-5]
        sender_id = int.from_bytes(data[-5:-1], byteorder='big', signed=False)
        status = data[-1]
        logger.info("enocean: radio message: choice = {:02x} / payload = [{}] / sender_id = {:08X} / status = {}".format(choice, ', '.join(['0x%02x' % b for b in payload]), sender_id, status))
        
        if (len(optional) == 7):
            subtelnum = optional[0]
            dest_id = int.from_bytes(optional[1:5], byteorder='big', signed=False)
            dBm = -optional[5]
            SecurityLevel = optional[6]
            logger.info("enocean: radio message with additional info: subtelnum = {} / dest_id = {:08X} / signal = {}dBm / SecurityLevel = {}".format(subtelnum, dest_id, dBm, SecurityLevel))

        # check for teach-in bit - this is kind of ugly and should be encapsulated someway
        if (choice == 0xA5) and ((payload[3] & 1<<3) == 0):
            teach_in_eep = "{:02X}_{:02X}_{:02X}".format(choice, payload[0] >> 2, ((payload[0] & 0x03) << 5) + (payload[1] >> 3))
            manufacturer = ((payload[1] & 0x07) << 8) + payload[2]
            #logger.info("enocean: received teach-in telegram for sender {:08X} from manufacturer {:03X} with eep {}".format(sender_id, manufacturer, teach_in_eep))
            # check if we know the sender
            if sender_id in self._rx_items:
                # check if we know exactly this eep - all good!
                if teach_in_eep in self._rx_items[sender_id].keys():
                    logger.info("enocean: received teach-in telegram for known sender {:08X} from manufacturer {:03X} with known eep {} - associated items: {}".format(sender_id, manufacturer, teach_in_eep, self._rx_items[sender_id][teach_in_eep]))
                # check if the rorg/choice matches a known eep - this means we can't distinguish them! WARN!
                elif teach_in_eep[:2] in [x[:2] for x in self._rx_items[sender_id].keys()]:
                    for eep,items in self._rx_items[sender_id].items():
                        # check if choice matches first byte in eep (this seems to be the only way to find right eep for this particular packet)
                        if eep.startswith("{:02X}".format(choice)):
                            logger.warning("enocean: received teach-in telegram for known sender {:08X} from manufacturer {:03X} with eep {} which CONFLICTS known eep {} - associated items: {}".format(sender_id, manufacturer, teach_in_eep, eep, self._rx_items[sender_id][eep]))
                else:
                    logger.info("enocean: received teach-in telegram for known sender {:08X} from manufacturer {:03X} with unknown eep {}".format(sender_id, manufacturer, teach_in_eep))
            else:
                logger.info("enocean: received teach-in telegram for unknown sender {:08X} from manufacturer {:03X} with eep {}".format(sender_id, manufacturer, teach_in_eep))
            return

        if sender_id in self._rx_items.keys():
            # iterate over all eep known for this id and get list of associated items
            for eep,items in self._rx_items[sender_id].items():
                # check if choice matches first byte in eep (this seems to be the only way to find right eep for this particular packet)
                if eep.startswith("{:02X}".format(choice)):
                    # call parsing method for particular eep - returns dict with key-value pairs
                    results = getattr(self, "_parse_eep_" + eep)(payload)
                    logger.info("enocean: radio message results = {}".format(results))
                    for item in items:
                        rx_key = item.conf['enocean_rx_key'].upper()
                        if rx_key in results:
                            item(results[rx_key], 'EnOcean', "{:08X}".format(sender_id))
        else:
            logger.info("unknown ID = {:08X}".format(sender_id))

    def _process_packet_type_response(self, data, optional):                      
        RETURN_CODES = ['OK', 'ERROR', 'NOT SUPPORTED', 'WRONG PARAM', 'OPERATION DENIED']
        if (self._last_cmd_code == CO_WR_RESET) and (len(data) == 1):
            logger.info("enocean: Reset returned code = {}".format(RETURN_CODES[data[0]]))
        elif (self._last_cmd_code == CO_RD_VERSION):
            if (data[0] == 0) and (len(data) == 33):
                logger.info("enocean: Chip ID = 0x{} / Chip Version = 0x{}".format(''.join(['%02x' % b for b in data[9:13]]), ''.join(['%02x' % b for b in data[13:17]])))
                logger.info("enocean: APP version = {} / API version = {} / App description = {}".format('.'.join(['%d' % b for b in data[1:5]]), '.'.join(['%d' % b for b in data[5:9]]), ''.join(['%c' % b for b in data[17:33]])))
            else:
                logger.error("enocean: Reading version returned code = {}".format(RETURN_CODES[data[0]]))
        elif (self._last_cmd_code == CO_RD_IDBASE):
            if (data[0] == 0) and (len(data) == 5):
                logger.info("enocean: Base ID = 0x{}".format(''.join(['%02x' % b for b in data[1:5]])))
                if (len(optional) == 1):
                    logger.info("enocean: Remaining write cycles for Base ID = {}".format(optional[0]))
            else:
                logger.error("enocean: Reading Base ID returned code = {}".format(RETURN_CODES[data[0]]))
        else:
            logger.error("enocean: processing unexpected response with return code = {} / data = [{}] / optional = [{}]".format(RETURN_CODES[data[0]], ', '.join(['0x%02x' % b for b in data]), ', '.join(['0x%02x' % b for b in optional])))      
        self._response_lock.acquire()
        self._response_lock.notify()        
        self._response_lock.release()
        
    def _startup(self):
        # request one time information
        logger.info("enocean: resetting device")
        self._send_common_command(CO_WR_RESET)
        logger.info("enocean: requesting version information")
        self._send_common_command(CO_RD_VERSION)
        logger.info("enocean: requesting id-base")
        self._send_common_command(CO_RD_IDBASE)
        #logger.debug("enocean: ending connect-thread")
               
    def run(self):
        self.alive = True
        t = threading.Thread(target=self._startup, name="enocean-startup")
        t.daemon = True
        t.start()
        msg = []
        while self.alive:
            readin = self._tcm.read(1000)
            if readin:
                msg += readin
                        
                # check if header is complete (6bytes including sync)
                # 0x55 (SYNC) + 4bytes (HEADER) + 1byte(HEADER-CRC)
                while (len(msg) >= 6):
                    #check header for CRC
                    if (msg[0] == PACKET_SYNC_BYTE) and (self._calc_crc8(msg[1:5]) == msg[5]):
                        # header bytes: sync; length of data (2); optional length; packet type; crc
                        data_length = (msg[1] << 8) + msg[2]
                        opt_length = msg[3]
                        packet_type = msg[4]
                        msg_length = data_length + opt_length + 7                     
                        #logger.debug("enocean: received header with data_length = {} / opt_length = 0x{:02x} / type = {}".format(data_length, opt_length, packet_type))
                        
                        # break if msg is not yet complete:
                        if (len(msg) < msg_length):
                            break
                            
                        # msg complete    
                        if (self._calc_crc8(msg[6:msg_length-1]) == msg[msg_length-1]):
                            data = msg[6:msg_length-(opt_length+1)]
                            optional = msg[(6+data_length):msg_length-1]
                            if (packet_type == PACKET_TYPE_RADIO):
                                self._process_packet_type_radio(data, optional)
                            elif (packet_type == PACKET_TYPE_RESPONSE):
                                self._process_packet_type_response(data, optional)
                            else:
                                logger.error("enocean: received packet with unknown type = 0x{:02x} - len = {} / data = [{}]".format(packet_type, msg_length, ', '.join(['0x%02x' % b for b in msg])))
                        else:
                            logger.error("enocean: crc error - dumping packet with type = 0x{:02x} / len = {} / data = [{}]!".format(packet_type, msg_length, ', '.join(['0x%02x' % b for b in msg])))                               
                        msg = msg[msg_length:]
                    else:
                        #logger.warning("enocean: consuming [0x{:02x}] from input buffer!".format(msg[0]))                               
                        msg.pop(0)

    def stop(self):
        self.alive = False

    def parse_item(self, item):
        if 'enocean_rx_key' in item.conf:
            # look for info from the most specific info to the broadest (key->eep->id) - one id might use multiple eep might define multiple keys
            eep_item = item
            while (not 'enocean_rx_eep' in eep_item.conf):
                eep_item = eep_item.return_parent()
                if (eep_item is self._sh):
                    logger.error("enocean: could not find enocean_eep for item {}".format(item))
                    return None
            id_item = eep_item
            while (not 'enocean_rx_id' in id_item.conf):
                id_item = id_item.return_parent()
                if (id_item is self._sh):
                    logger.error("enocean: could not find enocean_id for item {}".format(item))
                    return None

            rx_key = item.conf['enocean_rx_key'].upper()
            rx_eep = eep_item.conf['enocean_rx_eep'].upper()
            rx_id = int(id_item.conf['enocean_rx_id'],16)
            
            # check if there is a function to parse payload
            if not callable(getattr(self, "_parse_eep_" + rx_eep, None)):
                logger.error("enocean: item {} misses parser for eep {}".format(item, rx_eep))
                return None
            
            if (not rx_id in self._rx_items):
                self._rx_items[rx_id] = {rx_eep: [item]}
            elif (not rx_eep in self._rx_items[rx_id]):
                self._rx_items[rx_id][rx_eep] = [item]
            elif (not item in self._rx_items[rx_id][rx_eep]):
                self._rx_items[rx_id][rx_eep].append(item)

            logger.info("enocean: item {} listens to id {:08X} with eep {} key {}".format(item, rx_id, rx_eep, rx_key))
            #logger.info("enocean: self._rx_items = {}".format(self._rx_items))
                 
    def update_item(self, item, caller=None, source=None, dest=None):
        if caller != 'EnOcean':
            if item():
                pass

    def _send_packet(self, packet_type, data=[], optional=[]):
        length_optional = len(optional)
        if length_optional > 255:
            logger.error("enocean: optional to long ({} bytes, 255 allowed)".format(length_optional))
            return
        length_data = len(data)
        if length_data > 65535:
            logger.error("enocean: data to long ({} bytes, 65535 allowed)".format(length_data))
            return

        packet = bytearray([PACKET_SYNC_BYTE])
        packet += length_data.to_bytes(2, byteorder='big') + bytes([length_optional, packet_type])
        packet += bytes([self._calc_crc8(packet[1:5])])
        packet += bytes(data + optional)
        packet += bytes([self._calc_crc8(packet[6:])])
        #logger.warning("enocean: sending packet with len = {} / data = [{}]!".format(len(packet), ', '.join(['0x%02x' % b for b in packet])))  
        self._tcm.write(packet)

    def _send_common_command(self, _code, data=[], optional=[]):
        self._cmd_lock.acquire()
        self._last_cmd_code = _code
        self._send_packet(PACKET_TYPE_COMMON_COMMAND, [_code] + data, optional)
        self._response_lock.acquire()
        # wait 5sec for response
        self._response_lock.wait(5)
        self._response_lock.release()
        self._cmd_lock.release()

    def _calc_crc8(self, msg, crc=0):
        for i in msg:
            crc = FCSTAB[crc ^ i]
        return crc

