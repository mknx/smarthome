# Modbus

# Features
 - RTU and TCP support
 - Multimaster, RTU and TCP mixed, multiple instances of each are possible. Differentiated by id.
 - Tries to reconnect after connection lost (e.g. peer offline)

# Info
If there are a lot of Modbus datapoints to read in one 'click', then it is not always possible to fulfill the set interval in 'modbus_readInterval'. There are no priorities for reading values but it is ensured that every datapoint is read in one cycle if it is due, so there is no clogging. This 'problem/feature' is per master (master_id), so different ones take no influence on each other.

# How it works
At startup it sets up modbus-tk for all defined Masters differentiated by master_id. Modbus-tk opens the connection with the first read or write.   
On the first run off read loop (__read_loop) all datapoints are read for init values. After that the interval for reading is defined by modbus_readInterval separately for every item.   
If a Slave response is bad (missing, corrupted, ...) it is assumed that this slave is offline and all datapoints of this slave are set up to be read on the next tick (default 1 second). That means all configured Modbus datapoints have to be readable else the master tries to read all datapoints of that slave every tick. This could become a problem if there are a lot of them and the values are required in a certain interval.

# Requirements
- modbus-tk (https://github.com/ljean/modbus-tk)    
- pyserial   
`pip3 install modbus-tk pyserial`

## Supported Hardware

Modbus RTU and TCP

# Configuration

## plugin.conf

* `master_id` -- Uunique id to differentiate between different master, referenced in modbus_addr.
* `com_type` --  Modbus RTU or TCP {RTU, TCP}.
* `timeout` -- Timeout between request and fully received response (modbus-tk).
* `downTime` -- Timeout between reads. Some slaves (especially rtu ones) need some downtime between request to avoid errors.
* `rtu_*` -- Self-explanatory. If it is used is defined by com_type.
* `tcp_*` -- Self-explanatory. If it is used is defined by com_type.


<pre>
[modbus_one]
    class_name = Modbus
    class_path = plugins.modbus
    
    master_id = ModbusOne
    com_type = RTU  # {RTU, TCP}
    # timeout = None  # timeout for request. Default: RTU: 0.5 sec, TCP: 1.0 sec
    # downTime = None  # timeout between reads. Default: RTU: 0.05 sec, TCP: 0.01 sec

    # RTU:
    # rtu_port = /dev/ttyUSB0
    # rtu_baud = 9600
    # rtu_bytesize = 8
    # rtu_parity = N  # {N,E,O,S,M}
    # rtu_stopbits = 1
    # rtu_xonxoff = 0

    # TCP:
    # tcp_ip = 192.168.2.8
    # tcp_port = 50502   # standard modbus TCP port 502 is privileged 
</pre>

### Example
* `modbus_addr` --  ModbusMasterID | SlaveNr | Addr | length
    * `ModbusMasterID` -- master_id from the plugin.conf
    * `SlaveNr` -- Slave Address
    * `Addr` -- Register Address
    * `length` --  Nr of Registers to read
* `modbus_type` -- Options are: Coil, DiscreteInput, InputRegister, HoldingRegister
* `modbus_readInterval` --  Read interval in seconds (optional). If None or <0 it is only read at startup
* `modbus_unpack` --  See below
* `modbus_pack` --  See below


<pre>
[[Temp]]
    type = num
    modbus_addr = ModbusOne | 1 | 0 | 1  # ModbusMasterID, SlaveNr, Addr, length (Nr of registers)
    modbus_type = HoldingRegister  # Coil, DiscreteInput, InputRegister, HoldingRegister
    modbus_readInterval = 1  # read interval in seconds (optional) if -1 or not given it is only read at startup
    modbus_unpack = lambda x: 10.23/(2**10-1)*x[0]  # see below
    modbus_pack = lambda x: [int((x*(2**10-1))/ 10.23)]  # see below
</pre>


#### Pack Unpack

modbus_unpack and modbus_pack require a standard Python lambda function. Pack is called before the value is sent towards the Modbus Slave, unpack for the other way around (Modbus Slave to Smarthome). The modules struct, datetime and ctypes are loaded and can be used.

- x for unpack is always a list
- the return val for pack must always be a list

E.g.:
- `lambda x: datetime.datetime.fromtimestamp(int(x[0]))`
- `lambda x: {1:'Error',2:'Warning'}[x[0]]`

