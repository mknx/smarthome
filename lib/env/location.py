
# lib/env/location.py

if sh.sun:
    sh.env.location.sunrise(sh.sun.rise())
    sh.env.location.sunset(sh.sun.set())

    sh.env.location.moonrise(sh.moon.rise())
    sh.env.location.moonset(sh.moon.set())
    sh.env.location.moonphase(sh.moon.phase())
