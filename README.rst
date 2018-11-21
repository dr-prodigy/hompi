=====
hompi
=====

Open-source home automation project for Raspberry Pi


Description
-----------

**hompi** (*'hom-pee'*) is a lightweight Python 2 / 3 software developed
for Raspberry Pi to provide a complete and reliable home automation system
to control heating, gates, ambient lights, etc. (more to come!).

The system is designed to be boxed and headless, interfacing all needed
peripherals (thermometre, relays, LED strips, ...) directly.
All information (temperature, time, heating program, weather, aphorisms..)
are accessible through an LCD display (Hitachi 16x2 or 20x4 both supported).

It is suitable for any RPi version and has a very low CPU consumption
(avg 5-10% on a Pi1/2), so your Pi can still do lots of things :)

Everything is implemented in code and local libs (ie: no cloud services
required to work) and access to peripherals is made via native Pi's GPIO or
LAN/WiFi (= simple, fast, reliable).

All functions are exposed and controlled through a secured open web API
developed with Flask (can be accessed on local subnet and/or internet through
public IP), designed to run through web/WSGI server.

**hompi** server module is freeware and opensource, and can be controlled with
no limitations using your own client (web, mobile app).

**hompi** mobile app, specifically designed for it, will soon be available for
Android and iOS.


Main features
-------------

- Heating management (manual and automatic customizable modes and programmes, data logging, reports)
- Interface to W1 thermometer sensors (DS18B20)
- LCD dashboard with graphic chars controlled via I2C (HD44780 16x2 or 20x4) displaying all running information
- LED strip support (eg: WS2801) for ambient light, Xmas lights, sequences...
- Support for GPIO relays (boiler control, home gate, home illumination, etc.)
- (Optional) integration with various external API (weather, aphorisms, etc.)
- Multiple **hompi** servers can interoperate and share data
- More..


Prerequisites
-------------

.. _: http://espeak.sourceforge.net/

- Raspberry Pi any version (code works also on any bash-powered sys, such as Linux / MacOS / Win10, ... for testing and development with stubbed I/O (stub libs provided)
- Raspbian Wheezy or greater (or compatible)
- GPIO, SPI, I2C modules (required for accessing peripherals)
- LAN / internet connection (note: after setup, it can even possibly work offline, given that no external control is required)
- Python and relevant tools:
    - *virtualenv*
    - *pip*
- (Optional) - espeak_ application is required to enable speech synthesis ..


Wiring
------

.. _: https://github.com/dr-prodigy/hompi/blob/master/misc/gpio.txt

Please refer to `misc/gpio.txt`_ file for wiring details.


Usage
-----

After cloning repository

.. code-block:: bash

    $ git clone https://github.com/dr-prodigy/hompi.git

Run

.. code-block:: bash

    $ ./scripts/install.sh
    
or, for Python3:

.. code-block:: bash

    $ ./scripts/install_py3.sh

Upon completion, copy *config_sample.py* to *config.py*, and modify as needed.

.. code-block:: bash

    $ cp config_sample.sh config.py
    $ vi config.py

(Optional) - To run ambient module ( *MODULE_AMBIENT = True* ) on not GPIO-capable devices
(ie: Linux, MacOS, Win..), you need to stub *spidev.py* library using command

.. code-block:: bash

    $ ln -s ./stubs/spidev.py .

Start server in debug mode with

.. code-block:: bash

    $ ./hompi

or, for automatic daemon operation, schedule

.. code-block:: bash

    $ ./scripts/hompi.sh

at boot time.

When run interactively from command line (debug mode), **hompi** displays
internal status updates and emulates LCD on screen.

When flask debugger is enabled (see code in *hompi.sh*) web API is
available at *http://[Raspberry IP]:5000/hompi/....*

In case of WSGI server adoption (recommended for production), please refer to
specific documentation about setup and usage.


To Do
-----

- Web User Interface
- Web API documentation
- Config files documentation
- Wiring and install documentation
- Pictures, demo vids (homesite?)
- Integration with other devices and protocols (433Mhz modules, ZigBee, ...)


Contributions
-------------

.. _: https://github.com/dr-prodigy/hompi/issues
.. __: https://github.com/dr-prodigy/hompi/pulls

Issues_ and `Pull Requests`__ are always welcome.


License
-------

.. _: https://github.com/dr-prodigy/hompi/blob/master/LICENSE.md

Code and documentation are available according to the GPL v.3.0 License
(see LICENSE_).
