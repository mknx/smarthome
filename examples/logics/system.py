############
# system.py
############


def td2str(td):
    hours, seconds = divmod(td.seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if td.days:
        return "{0}d {1}h {2}m".format(td.days, hours, minutes)
    else:
        return "{0}h {1}m".format(hours, minutes)

# Runtime
runtime = sh.tools.runtime()
sh.technik.smarthome.runtime(td2str(runtime))

# Thread
tn = {}
tc = threading.activeCount()
for t in threading.enumerate():
    tn[t.name] = tn.get(t.name, 0) + 1
logger.info('Threads ({0}): '.format(tc) + ', '.join("{0}: {1}".format(k, v) for (k, v) in list(tn.items())))
sh.technik.smarthome.threads(tc)

# Object Counter
d = {}
sys.modules
# collect all classes
for m in list(sys.modules.values()):
    for sym in dir(m):
        o = getattr(m, sym)
        if isinstance(o, type):
            d[o] = sys.getrefcount(o)
# sort by refcount
pairs = [(x[1], x[0]) for x in list(d.items())]
pairs = sorted(pairs, key=lambda element: element[0])
#sorted(pairs)
#pairs.reverse()
obj = ''
for n, c in pairs[-10:]:
    obj += "{0}: {1}, ".format(c.__name__, n)
obj = obj.strip(', ')
logger.info("Objects (Top 10): {0}".format(obj))

# Garbage
import gc
gc.set_debug(gc.DEBUG_LEAK)
gc.collect()
if gc.garbage == []:
    logger.debug("Garbage: {0}".format(gc.garbage))
else:
    logger.warning("Garbage: {0}".format(gc.garbage))
del gc.garbage[:]

# Load
l1, l5, l15 = os.getloadavg()
logger.debug("Load: {0}, {1}, {2}".format(l1, l5, l15))
sh.technik.smarthome.load(round(l5, 2))

# Memory
statusfile = "/proc/{0}/status".format(os.getpid())
units = {'kB': 1024, 'mB': 1048576}
with open(statusfile, 'r') as f:
    data = f.read()
status = {}
for line in data.splitlines():
    key, sep, value = line.partition(':')
    status[key] = value.strip()
size, unit = status['VmRSS'].split(' ')
mem = round(int(size) * units[unit])
sh.technik.smarthome.memory(mem)

## System Memory
#statusfile = "/proc/meminfo"
#units = {'kB': 1024, 'mB': 1048576}
#with open(statusfile, 'r') as f:
#   data = f.read()
#for line in data.splitlines():
#   key, sep, value = line.partition(':')
#   if key.startswith('Mem'):
#       size, unit = value.strip().split(' ')
#       mem = int(size) * units[unit]
#       if key == 'MemTotal':
#           total = mem
#       elif key == 'MemFree':
#           free = mem
#sh.technik.smarthome.system.memory(100 - int(free / (total / 100)))

# System Uptime
statusfile = "/proc/uptime"
with open(statusfile, 'r') as f:
    data = f.read()
uptime = int(float(data.split()[0]))
uptime = datetime.timedelta(seconds=uptime)
sh.technik.smarthome.uptime(td2str(uptime))
