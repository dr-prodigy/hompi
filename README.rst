.. Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
.. This file is part of hompi <https://github.com/dr-prodigy/hompi>

=====
hompi
=====
Open-source home automation project for Raspberry Pi


Description
-----------
**hompi** (*'hom-pee'*) is a lightweight Python 2 / 3 software developed
for Raspberry Pi to provide a native reliable home automation engine
to control heating, gates, ambient LED lights, etc...

The system is designed to be headless, interfacing all needed
peripherals (thermometre, relays, LED strips, ...) in hw via GPIO.
All information (temperature, time, heating program, weather, aphorisms..)
are made available through an LCD display (Hitachi 16x2 or 20x4 supported)
or can be retrieved via webservices, or integrated in Home Assistant.

It is suitable for any RPi version and has a very low CPU consumption
(avg 5-10% on a Pi1), so your Pi can still do lots of things :)

Everything is implemented in code and local libs (ie: no cloud services
required to work) and access to peripherals is made via native Pi's GPIO or
LAN/WiFi (= simple, fast, reliable).

All functions are exposed and controlled through a secured open web API
developed with Flask (can be accessed on local subnet and/or internet through
public IP), designed to run through web/WSGI server.

**hompi** server module is freeware and opensource, and can be controlled with
no limitations using your own client (web, mobile app), and includes Home Assistant
integration.

Main features
-------------
- Support for Home Assistant https://www.home-assistant.io/
- Heating system (multi-area temperature control, manual and automatic customizable modes and programmes, data logging
  and reporting)
- MQTT integration with external thermometers and TRV (smart thermostatic valves)
- Interface to W1 thermometer sensors (DS18B20)
  (eg: https://www.amazon.it/SENSORE-TEMPERATURA-DS18B20-IMPERMEABILE-ARDUINO/dp/B072QYW9J4)
- LCD dashboard (HD44780 16x2 or 20x4) with custom / big chars through direct or I2C connection
  (eg: https://www.amazon.it/SunFounder-LCD1602-Display-Arduino-Raspberry/dp/B019K5X53O)
- LED strip support (eg: WS2801) for ambient light, Xmas lights, sequences, configured as Home Assistant light
  (eg: https://www.amazon.it/BTF-LIGHTING-indirizzabili-individualmente-flessibile-impermeabile/dp/B088BRY2SH)
- Native support for GPIO relays (boiler control, home gate, home illumination, etc.)
  (eg: https://www.amazon.it/SunFounder-Channel-Optocoupler-Expansion-Raspberry/dp/B00E0NTPP4)
- Integration with various external API (weather, aphorisms, etc.)
- Multiple **hompi** servers can interoperate and share data
- More..

Prerequisites
-------------
.. __: http://espeak.sourceforge.net/

- Raspberry Pi any version (code works also on any bash-powered sys, such as Linux / MacOS / Win10, ... for testing and development with stubbed I/O (stub libs provided)
- Raspbian Wheezy or greater (or compatible)
- GPIO, SPI, I2C modules (required for accessing peripherals)
- LAN / internet connection (no cloud services required)
- Python and relevant tools:
    - *virtualenv*
    - *pip*
- (Optional) - espeak__ is required to enable internal speech synthesis ..

Wiring
------
.. __: https://github.com/dr-prodigy/hompi/blob/master/misc/gpio.txt

Please refer to `misc/gpio.txt`__ file for wiring details.

Usage
-----
Hompi separates the **Python package** (code + dependencies) from the
**instance** (config, ``db/``, ``logs/``, ``run/``, systemd). Bootstrap the
instance with ``hompi init`` after the package is installed.

Install from a clone (venv + editable package + init)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ git clone https://github.com/dr-prodigy/hompi.git
    $ cd hompi
    $ ./scripts/install.sh          # or: ./scripts/install.sh --pi

``install.sh`` creates ``./venv``, runs ``pip install -e .`` (or ``.[pi]``),
then ``hompi init`` for the current directory (``HOMPI_HOME``).

Install without cloning (venv + pip + init)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ python3 -m venv ~/venvs/hompi
    $ . ~/venvs/hompi/bin/activate
    $ pip install "hompi[pi]"    # or: pip install "git+https://github.com/dr-prodigy/hompi.git#egg=hompi[pi]"
    $ mkdir -p ~/hompi && cd ~/hompi
    $ hompi init --home "$PWD" --venv "$VIRTUAL_ENV"

``hompi init`` creates runtime dirs, writes ``config.yaml`` from the packaged
sample (unless one already exists), installs ``scripts/hompid.sh`` and
``uwsgi.ini``, and installs a systemd **user** unit
(``~/.config/systemd/user/hompi.service``). Use ``--no-systemd`` to skip the
unit, and ``--force`` to overwrite config/uWSGI files.

Manual editable install (same as install.sh steps)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    $ python3 -m venv venv
    $ . venv/bin/activate
    $ pip install -e .
    $ pip install -e ".[pi]"   # Pi hosts only
    $ hompi init --home "$PWD" --venv "$VIRTUAL_ENV"
    $ vi config.yaml

You can also point ``HOMPI_CONFIG`` at any YAML file, and ``HOMPI_HOME`` at the
instance data directory (``db/``, ``res/``, optional override ``migrations/``).
Packaged DB migrations live inside the ``hompi`` package; place a custom
``migrations/`` folder under ``HOMPI_HOME`` only if you need to override them.

On non-Pi hosts, missing GPIO/SPI libraries are stubbed automatically
(no ``spidev.py`` symlink required). Install real drivers with ``.[pi]``.

Start server in debug mode (venv activated, from the project root or with
``HOMPI_HOME`` set):

.. code-block:: bash

    $ . venv/bin/activate
    $ hompi

or:

.. code-block:: bash

    $ python -m hompi

The Flask HTTP API entry point (development) is:

.. code-block:: bash

    $ hompi-api

For production, serve ``hompi.api:app`` with uWSGI (see ``uwsgi.ini``):

.. code-block:: bash

    $ mkdir -p logs
    $ uwsgi --ini uwsgi.ini

API listens on ``127.0.0.1:3031`` (uwsgi protocol) by default.

or, for automatic daemon operation:

.. code-block:: bash

    $ systemctl --user enable --now hompi.service
    # or: ./scripts/hompid.sh start

When run interactively from command line (debug mode), **hompi** displays
internal status updates and emulates LCD on screen.

When flask debugger is enabled (see ``run_flask_debugger`` in *hompid.sh*) web API is
available at *http://[Raspberry IP]:5000/hompi/....*

In case of WSGI server adoption (recommended for production), please refer to
specific documentation about setup and usage. The API module is ``hompi.api``.

Web API documentation is in `docs/API.rst`__ (endpoints, authentication,
command formats, multi-hompi proxying, Home Assistant examples).

Configuration reference is in `docs/CONFIG.rst`__ (``config.yaml`` keys,
defaults, module flags, GPIO, MQTT, logging).

.. __: docs/API.rst
.. __: docs/CONFIG.rst

To Do
-----
- Pictures, demo vids (homesite?)

Development
-----------
Install with test extras and run the suite:

.. code-block:: bash

    $ pip install -e ".[dev]"
    $ hompi init --home "$PWD" --no-systemd
    $ pytest
    $ flake8 src

CI runs on GitHub Actions (``.github/workflows/ci.yml``) for Python 3.10–3.13.

Contributions
-------------
.. _issues: https://github.com/dr-prodigy/hompi/issues
.. __: https://github.com/dr-prodigy/hompi/pulls

Issues_ and `Pull Requests`__ are always welcome.


License
-------
.. _: https://github.com/dr-prodigy/hompi/blob/master/LICENSE.md

Code and documentation are available according to the GPL v.3.0 License
(see LICENSE_).
