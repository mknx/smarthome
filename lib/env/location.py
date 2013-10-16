
# lib/env/location.py

if sh.sun:
    sh.env.location.sunrise(sh.sun.rise())
    sh.env.location.sunset(sh.sun.set())

    sh.env.location.moonrise(sh.moon.rise())
    sh.env.location.moonset(sh.moon.set())
    sh.env.location.moonphase(sh.moon.phase())

    # setting day and night
    night = sh.sun.rise(-6).day == sh.sun.set(-6).day
    sh.env.location.day(not night)
    sh.env.location.night(night)
