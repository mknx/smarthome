---
title: yrno Plugin
layout: default
summary: reads wheather data from yr.no api
---

# Requirements

None

## Supported Hardware

None

# Configuration

## plugin.conf

<pre>
[yrno]
   class_name = yrno
   class_path = plugins.yrno
   weatherStation = Tyskland/Hamburg/Hamburg
</pre>

The plugin needs the "weatherStation" attribute. You can get it from yr.no, if you search for the weather station of your choice
and get the relevant data from the URL. E.g for "Hamburg" the URL is "http://www.yr.no/sted/Tyskland/Hamburg/Hamburg/". You need
"Tyskland/Hamburg/Hamburg" for the configuration. Please note that the string has no leading and trailing slashes!

## items.conf

### yrno_attr

The value of the attribute defines, which weather data has to save to this item. Possible values of "yrno_attr" are:

    rainfallMax             # max rainfall in millimeter
    rainfallMin             # min rainfall in millimeter
    rainfallValue           # actual rainfall in millimeter
    pressureUnit            # air-pressure unit
    pressureValue           # air-pressure value
    windDirCode             # wind direction code ( N = north, E = east, S = south, W = west ... )
    windDirDeg              # wind direction degree ( 0 - 360°)
    windDirName             # wind direction full name ( North, East, South, West, Northeast ... )
    windSpeedName           # wind speed full name ( Fresh breeze, Light breeze, Storm )
    windSpeedValue          # wind speed value in Miles per Hour
    symbolName              # text for weather symbol to show ( act. not implemented)
    symbolNumber            # number of weather symbol to show ( act. not implemented)
    symbolVar               # variance for the weather symbol to show (act. not implemented)
    tempUnit                # temperature unit
    tempValue               # temperature value

Actually, only the next available data is supported to save to an item

### Example

<pre>
# items/my.conf

    [[wetter]]
        [[[doUpdate]]]
            type = foo
            enforce_updates = true
            eval = sh.yrno.getActualData()
            crontab = 1 * * * = true
        [[[temperatur]]]
            type = num
            yrno_attr = tempValue
            visu = yes
            history = true
            crontab = init
            enforce_updates = true
        [[[niederschlagsmenge]]]
            type = num
            yrno_attr = rainfallValue
            visu = yes
            history = true
            crontab = init
            enforce_updates = true
        [[[niederschlagMin]]]
            type = num
            yrno_attr = rainfallMin
            visu = yes
            history = true
            crontab = init
            enforce_updates = true
        [[[niederschlagMax]]]
            type = num
            yrno_attr = rainfallMax
            visu = yes
            history = true
            crontab = init
            enforce_updates = true
        [[[luftdruck]]]
            type = num
            yrno_attr = pressureValue
            visu = yes
            history = true
            crontab = init
            enforce_updates = true
        [[[windgeschwindigkeit]]]
            type = num
            yrno_attr = windSpeedValue
            visu = yes
            history = true
            crontab = init
            enforce_updates = true
</pre>

## logic.conf

None

# Methodes

## getActualData()
This method refreshes the weather data and items. The method reads only the next available forcast.
You could call it with `sh.yrno.getActualData()`

## getAllData()
This method refreshes the weather data but actually not items. The method reads _all_ available forecasts and saves them
to the self.weatherData Object.
You could call it with `sh.yrno.getAllData()`