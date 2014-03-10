Indigo Netatmo
==============

Netatmo custom device plugin for Indigo v6

History
=======
Originally by Richard Perlman.
The plugin was built on top of philippelt’s Python Netatmo code: https://github.com/philippelt/netatmo-api-python

Features
========
* Netatmo indoor, outdoor and additional module support
* Multiple stations, single user
* Provides data for temperature, humidity, pressure, co2 and noise levels, battery, etc.

Release Notes
=============

`v0.4.2 March, 2014`
    Work in progress. Improving UI and interactions.

`v0.4.1 Aug 31, 2013`
    Changed state "when" to "Observation_Time" to remove field name conflict with SQL Logger

`v0.4.0 Aug 23, 2013`
    Added support for additional Indoor Modules
    Improved error reporting when read loop fails
    Expanded debugging reporting
    Improved server connection problem detection and recovery handling

`v0.3.0 Aug 23, 2013`
    (Internal development release)

`v0.2.0 May 17, 2013`
    First public beta
    added error checking for configured devices in readNetatmo()

`v0.0.2 May 15, 2013`
    added support for multiple Netatmo pairs

`v0.0.1 May 10, 2013`
    Initial alpha release
