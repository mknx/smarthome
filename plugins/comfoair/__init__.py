#!/usr/bin/env python
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#
# Copyright 2013 KNX-User-Forum e.V.            http://knx-user-forum.de/
#
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
#
import logging
import serial
import threading
import commands
import re
import sys

logger = logging.getLogger('')


class comfoAir():

    def __init__(self, smarthome, serialport, update_time=300):
        self._sh = smarthome
        self._lock = threading.Lock()
        self._port = serialport
        self._update_time = update_time
        self._sh.scheduler.add('comfoAir', self.__iterate,
                               cycle=self._update_time, prio=5, offset=0)
        self._listenItems = []
        self._connection = None

    def run(self):
        self.alive = True

    def stop(self):
        self.alive = False

    def parse_item(self, item):
        if 'comfoAir_listen' in item.conf:
            commandKey = item.conf['comfoAir_listen']
            if commandKey.startswith('KEY_'):
                if commandKey in commands.commands:
                    logger.debug(
                        "ComfoAir parse_item(): {0} send command {1}".format(item, commandKey))
                    self._listenItems.append(item)
                else:
                    logger.debug(
                        "ComfoAir parse_item(): Ignoring {0}: Key was not found in command list".format(commandKey))
            else:
                logger.warning(
                    "ComfoAir parse_item(): Ignoring {0}: String have to begin with KEY_.".format(item))
        elif 'comfoAir_send' in item.conf:
            commandKey = item.conf['comfoAir_send']
            if commandKey.startswith('KEY_'):
                if commandKey in commands.commands:
                    logger.debug(
                        "ComfoAir parse_item(): {0} send command {1}".format(item, commandKey))
                    return self.update_item
                else:
                    logger.debug(
                        "ComfoAir parse_item(): Ignoring {0}: Key was not found in command list".format(commandKey))
            else:
                logger.warning(
                    "ComfoAir parse_item(): Ignoring {0}: String have to begin with KEY_.".format(item))

    def parse_logic(self, logic):
        pass

    def update_item(self, item, caller=None, source=None, dest=None):
        if self.__connectSerial():
            try:
                self.__push(item.conf['comfoAir_send'], item, False)
                # iterate through items to get the current values
                self.__iterate()
            finally:
                self.__disconnectSerial()

    def __connectSerial(self):
        try:
            if self._connection is None:
                self._connection = serial.Serial(
                    self._port, 9600, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=1)
                logger.info(
                    "ComfoAir __connectSerial(): Communication with ComfoAir established")
            return True
        except (serial.SerialException, ValueError), e:
            logger.error("ComfoAir __connectSerial(): " + e.message)
            return False

    def __disconnectSerial(self):
        if self._connection is not None:
            self._connection.close()
            logger.info(
                "ComfoAir __disconnectSerial(): Communication with ComfoAir closed")
            self._connection = None

    def __iterate(self):
        if self.__connectSerial():
            try:
                for listenItem in self._listenItems:
                    key = listenItem.conf['comfoAir_listen']
                    self.__push(key, listenItem, True)
            except:
                e = sys.exc_info()[0]
                logger.error("ComfoAir __iterate():" + e)
            finally:
                self.__disconnectSerial()

    def __push(self, commandKey, item, requiredAnswer):

        logger.info("ComfoAir __push(): CommandKey = " + commandKey)
        answer = None
        if commandKey == "KEY_Komforttemperatur":
            commando = commands.commands[commandKey] + \
                str(self.__getComfoAirTemperature(int(item())))
            logger.debug("ComfoAir __push(): Set comfort temperature to " +
                         str(item()) + "! Command = " + str(commando))
            answer = self.__command_send(commando, requiredAnswer)
        else:
            answer = self.__command_send(
                commands.commands[commandKey], requiredAnswer)

        if requiredAnswer:
            if answer is not None:
                answerArray = answer.split('/')

                if commandKey == "KEY_Komforttemp":
                    item(int(answerArray[0]))
                elif commandKey == "KEY_Aussentemp":
                    item(int(answerArray[1]))
                elif commandKey == "KEY_Zulufttemp":
                    item(int(answerArray[2]))
                elif commandKey == "KEY_Ablufttemp":
                    item(int(answerArray[3]))
                elif commandKey == "KEY_Fortlufttemp":
                    item(int(answerArray[4]))
                elif commandKey == "KEY_EWTtemp":
                    item(int(answerArray[5]))
                elif commandKey == "KEY_Vent_Zuluft_Status":
                    item(int(answerArray[0]))
                elif commandKey == "KEY_Vent_Zuluft_Umdrehungen":
                    item(int(answerArray[1]))
                elif commandKey == "KEY_Vent_Abluft_Status":
                    item(int(answerArray[2]))
                elif commandKey == "KEY_Vent_Abluft_Umdrehungen":
                    item(int(answerArray[3]))
                elif commandKey == "KEY_BypassZustand":
                    item(int(answerArray[0]))
                elif commandKey == "KEY_StundenFilter":
                    item(int(answerArray[0]))
                elif commandKey == "KEY_Badschalter":
                    item(int(answerArray[0]))
                elif commandKey == "KEY_AktuelleStufe":
                    item(int(answerArray[0]))

    def __calculate_checksum(self, data):
        chk_data = data.replace(" ", "")
        checksum = 0
        y = 0
        chk_datasum = chk_data + "AD"
        logger.debug(
            "ComfoAir __calculate_checksum(): String to calculate checksum: " + chk_datasum)
        x07warschon = False
        laenge = len(chk_datasum) / 2

        for i in range(0, laenge):
            wertstring = chk_datasum[y:y + 2]
            wertbetrag = int(wertstring, 16)
            if wertbetrag == 7:
                if x07warschon:
                    y += 2
                    continue
                else:
                    x07warschon = True

            checksum += wertbetrag
            y = y + 2

        return hex(checksum)[-2:]

    def __command_send(self, data, requiredAnswer):
        answer = None
        ackbytes = self.__HexToByte("07F3")

        # calculate checksum
        checksum = self.__calculate_checksum(data)
        logger.debug(
            "ComfoAir __command_send(): Received checksum: " + checksum)

        # build command string (start + command + checksum + end)
        commandstring = "07F0" + data + checksum + "070F"
        logger.debug(
            "ComfoAir __command_send(): Final command string: " + commandstring)

        # convert from HEX to Byte
        commandbytes = self.__HexToByte(commandstring)
        logger.debug("ComfoAir __command_send(): Command-Bytes: " +
                     self.__ByteToHex(commandbytes))

        # number of Bytes
        numberBytes = len(commandbytes)
        logger.debug("ComfoAir __command_send(): Number of Bytes: " +
                     str(numberBytes))

        try:
            self._lock.acquire()

            # send command
            if self._connection.write(commandbytes) == numberBytes:
                logger.debug(
                    "ComfoAir __command_send(): Sending command successfully")

                # If command is a listen command then an answer is required
                if requiredAnswer:
                    reciv = ''
                    exit = 0
                    while exit < 2500:
                        retValue = self._connection.read(45)
                        logger.debug(
                            "ComfoAir __command_send(): Read: " + self.__ByteToHex(retValue))
                        if len(retValue) > 0:
                            sin = self.__ByteToHex(retValue)
                            reciv = reciv + sin
                            exit = 0
                        else:
                            exit += 1

                        if reciv.endswith("07 0F"):
                            if reciv[-8:] != "07 07 0F":
                                logger.debug(
                                    "ComfoAir __command_send(): End of answer")
                                break

                    if self._connection.write(ackbytes) != 2:
                        logger.error(
                            "ComfoAir __command_send(): Number of send bytes are not equal to command string")
                        return None

                    if reciv == "":
                        logger.error(
                            "ComfoAir __command_send(): No data received")
                        return None

                    reciv = reciv.replace(" ", "")
                    # while string end not equal to "070F"
                    while len(reciv) > 3 and reciv[-4:] != "070F":
                        reciv = reciv[-2:]

                    # Remove 070F at end of string
                    reciv = reciv[0:-4]
                    logger.debug(
                        "ComfoAir __command_send(): String without 070F at end: " + reciv)

                    # Remove 07F3 at end of string
                    if reciv[-4:] == "07F3":
                        reciv = reciv[0:-4]
                        logger.debug(
                            "ComfoAir __command_send(): String without 07F3 at end: " + reciv)

                    logger.debug(
                        "ComfoAir __command_send(): First two Bytes = " + reciv[0:4])

                    while len(reciv) > 3 and reciv[0:4] != "07F0":
                        reciv = reciv[2:]

                    reciv = reciv[4:]
                    logger.debug(
                        "ComfoAir __command_send(): Reciv without 07F0 at begin: " + reciv)

                    # hier muss noch eine Überprüfung gemacht werden ob nicht
                    # versehentlich mehrere Datenstrings in einem datenpaket
                    # enthalten sind

                    # Seperate checksum from recieved string
                    checksum = 0
                    checksum = reciv[-2:]
                    logger.debug(
                        "ComfoAir __command_send(): Read checksum: " + checksum)
                    reciv = reciv[0:-2]
                    logger.debug(
                        "ComfoAir __command_send(): Data string without checksum: " + reciv)

                    # calculate checksum for received string
                    rcv_checksum = self.__calculate_checksum(reciv)

                    logger.debug(
                        "ComfoAir __command_send(): Calculate checksum for received string: " + rcv_checksum)

                    if str(rcv_checksum).upper() == str(checksum).upper():
                        logger.debug(
                            "ComfoAir __command_send(): Checksums are equal")

                        # remove doubles 07
                        logger.debug(
                            "ComfoAir __command_send(): String before 07 cleaning: " + reciv)
                        reciv = re.sub("0707", "07", reciv)
                        logger.debug(
                            "ComfoAir __command_send(): String after 07 cleaning: " + reciv)

                        # identify temperature
                        if re.search("00D209", reciv) is not None:
                            t1 = self.__getTemperature(reciv[6:8])
                            t2 = self.__getTemperature(reciv[8:10])
                            t3 = self.__getTemperature(reciv[10:12])
                            t4 = self.__getTemperature(reciv[12:14])
                            t5 = self.__getTemperature(reciv[14:16])
                            t7 = self.__getTemperature(reciv[18:20])
                            logger.debug("ComfoAir __command_send(): Comfort temperature (Soll) = " + str(t1) + "; Outdoor temperature (Aussen) = " + str(t2) + "; Incoming air temperature (Zuluft)= " +
                                         str(t3) + "; Outgoing air temperature(Abluft) = " + str(t4) + "; Exit air temperature(Fortluft) = " + str(t5) + "; EWT temperature = " + str(t7))

                            answer = str(t1) + "/" + str(t2) + "/" + str(t3) + \
                                "/" + str(t4) + "/" + \
                                str(t5) + "/" + str(t7)

                        # Status Ventilator
                        elif re.search("000C06", reciv) is not None:
                            vent_zul = int(reciv[6:8], 16)
                            vent_abl = int(reciv[8:10], 16)
                            vent_zul_um = 1875000 / int(reciv[10:14], 16)
                            vent_abl_um = 1875000 / int(reciv[14:18], 16)
                            logger.debug("ComfoAir __command_send(): Incoming vent(Zuluft) = " + str(vent_zul) + "% " +
                                         str(vent_zul_um) + "U/min; Outgoing vent(Abluft) = " + str(vent_abl) + "% " + str(vent_abl_um) + "U/min")

                            answer = str(vent_zul) + "/" + str(vent_zul_um) + \
                                "/" + str(vent_abl) + \
                                "/" + str(vent_abl_um)

                        # Current state
                        elif re.search("00CE0E", reciv) is not None:
                            #currentState = reciv[22:24]
                            currentState = int(reciv[22:24], 16)
                            logger.debug(
                                "ComfoAir __command_send(): Current State = " + str(currentState))

                            #answer = str(currentState[-1:])
                            answer = str(currentState)

                        # Current state of bypass
                        elif re.search("000E04", reciv) is not None:
                            currentBypass = int(reciv[6:8], 16)
                            logger.debug(
                                "ComfoAir __command_send(): Current bypass state = " + str(currentBypass))

                            answer = str(currentBypass)

                        # Filter operating hours
                        elif re.search("00DE14", reciv) is not None:
                            filterHour = int(reciv[36:41], 16)
                            logger.debug(
                                "ComfoAir __command_send(): Filter operating hours = " + str(filterHour))

                            answer = str(filterHour)

                        # Bathswitch active?
                        elif re.search("000402", reciv) is not None:
                            bathSwitch = int(reciv[8:10], 16)
                            logger.debug(
                                "ComfoAir __command_send(): Bathswitch = " + str(bathSwitch))

                            answer = str(bathSwitch)
                    else:
                        logger.debug(
                            "ComfoAir __command_send(): Checksum are not equal")
                else:
                    retValue = self._connection.read(45)
                    logger.debug("ComfoAir __command_send(): Read: " +
                                 self.__ByteToHex(retValue))
                    if (self.__ByteToHex(retValue)).split(" ") == "07F3":
                            return None
            else:
                logger.error(
                    "ComfoAir __command_send():Number of send bytes are not equal to command string")

            return answer

        except ValueError, exception:
            logger.error("ComfoAir __command_send():" + exception.message)
        finally:
            self._lock.release()

    def __getTemperature(self, hexStr):
        return int(hexStr, 16) / 2 - 20

    def __getComfoAirTemperature(self, temp):
        temp = (temp + 20) * 2
        return hex(temp)[-2:]

    def __HexToByte(self, hexStr):

        bytes = []

        hexStr = ''.join(hexStr.split(" "))

        for i in range(0, len(hexStr), 2):
            bytes.append(chr(int(hexStr[i:i + 2], 16)))

        return ''.join(bytes)

    def __ByteToHex(self, byteStr):
        return ''.join(["%02X " % ord(x) for x in byteStr]).strip()
