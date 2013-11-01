
# lib/env/init.py

sh.env.core.version(sh.version)
sh.env.core.start(sh.now())

namefile = "/proc/sys/kernel/hostname"
with open(namefile, 'r') as f:
    hostname = f.read().strip()
sh.env.system.name(hostname)

# system start
with open("/proc/uptime", 'r') as f:
    uptime = f.read()
uptime = int(float(uptime.split()[0]))
start = sh.now() - datetime.timedelta(seconds=uptime)
sh.env.system.start(start)
