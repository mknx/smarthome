
# lib/env/statistic.py

# Garbage
gc.collect()
if gc.garbage != []:
    sh.env.core.garbage(len(gc.garbage))
    logger.warning("Garbage: {} objects".format(len(gc.garbage)))
    logger.info("Garbage: {}".format(gc.garbage))
    del gc.garbage[:]

# Threads
sh.env.core.threads(threading.activeCount())

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
sh.env.core.memory(mem)

# Load
l1, l5, l15 = os.getloadavg()
sh.env.system.load(round(l5, 2))

if sh.moon:
    sh.env.location.moonlight(sh.moon.light())
