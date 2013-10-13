
# lib/env/init.py

sh.env.core.version(sh.version)

namefile = "/proc/sys/kernel/hostname"
with open(namefile, 'r') as f:
    hostname = f.read().strip()
sh.env.system.name(hostname)
