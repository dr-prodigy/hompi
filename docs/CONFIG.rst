.. Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
.. This file is part of hompi <https://github.com/dr-prodigy/hompi>

==================
Configuration
==================

hompi reads runtime settings from a YAML file named ``config.yaml`` (or
``config.yml``). A annotated sample ships as ``config.sample.yaml`` in the
project root and inside the package (``hompi init`` copies it on first setup).

Access in code::

    from hompi.config import config
    print(config.HOMPI_ID)

All keys use **uppercase** names matching the former ``config.py`` module.

File location
-------------

Discovery order (``hompi._path.find_config_file``):

1. ``HOMPI_CONFIG`` environment variable (absolute path to a YAML file)
2. ``config.yaml`` or ``config.yml`` in the **instance home** directory

The instance home (``HOMPI_HOME``) is resolved as:

1. ``HOMPI_HOME`` environment variable
2. Parent directory of ``HOMPI_CONFIG`` (if set)
3. Current working directory
4. Repository root (editable ``src/`` installs)

On startup, hompi ``chdir``\ s into the instance home so relative paths such
as ``./res/images/*.jpg`` and ``db/`` resolve correctly.

Bootstrap a new instance:

.. code-block:: bash

    cp config.sample.yaml config.yaml
    # or:
    hompi init --home "$PWD" --venv "$VIRTUAL_ENV"

Loading behaviour
-----------------

- Omitted keys receive defaults from ``hompi.config._DEFAULTS``.
- ``THUMB_SIZE`` lists are coerced to a tuple ``(width, height)``.
- Empty ``API_KEY`` (``""``) is treated as unset (``null``).
- ``BUTTONS``, ``LOG_MUTE_MODULES``, ``HOMPI_SERVERS``, and
  ``HOMPI_EXT_SENSORS`` default to empty lists when ``null``.
- Settings are loaded once at import time into the singleton ``config`` object.

Temporary filesystem (SQLite)
-----------------------------

``TMPFS_ENABLE`` (bool, default: ``true``)
    When enabled, the SQLite database is copied to ``TMPFS_PATH`` on open and
    synced back to ``db/hompi.sqlite`` on shutdown (``db.flush()``). Reduces
    SD-card wear on Raspberry Pi.

``TMPFS_PATH`` (string, default: ``/tmp/``)
    Directory for the tmpfs copy of ``hompi.sqlite``. Must end with ``/``.

Identity and multi-hompi
------------------------

``HOMPI_ID`` (string, default: ``Living``)
    Human-readable name for this node. Exposed in status JSON (``id`` field),
    Home Assistant entities, and used to skip self when forwarding commands to
    slaves.

``HOMPI_SERVERS`` (list of strings, default: ``[]``)
    Base URLs of peer hompi API endpoints (include the ``/hompi`` prefix), e.g.::

        - http://192.168.1.20:5000/hompi
        - http://bedroom.local/hompi

    The daemon polls each peer's ``/_get_status`` every ~61 s and stores live
    summaries in ``hompi_slaves``. Peer heating state can contribute to the
    local boiler decision when ``THERMOSTAT_MODE`` includes bit 4.

``HOMPI_EXT_SENSORS`` (list of strings, default: ``[]``)
    URLs returning JSON with a top-level ``sensor`` object. Polled periodically
    and stored in ``hompi_ext_sensors`` in status output.

Feature modules
---------------

Boolean toggles unless noted. Set ``false`` to disable a subsystem entirely.

+-------------------+----------------------------------------------------------+
| Key               | Purpose                                                  |
+===================+==========================================================+
| ``MODULE_METEO``  | Fetch outdoor weather from OpenWeatherMap (``PLACE``).   |
| ``MODULE_APHORISM`` | Fetch inspirational quotes (``APHORISM_KEY``).         |
| ``MODULE_DB_LOG`` | Write periodic rows to ``gm_log`` (temperature history). |
| ``MODULE_SPEECH`` | Text-to-speech via ``SPEECH_COMMAND`` (``espeak``).      |
| ``MODULE_AMBIENT``| WS2801 LED strip control and effects.                    |
| ``MODULE_HASS``   | Push sensor entities to Home Assistant REST API.         |
| ``MODULE_TEMP``   | DS18B20 internal temperature and main thermostat logic.  |
| ``MODULE_HEATING``| GPIO relay for boiler / central heating.                 |
| ``MODULE_TRV``    | MQTT smart TRV (thermostatic valve) integration.         |
+-------------------+----------------------------------------------------------+

Aphorism
--------

``APHORISM_KEY`` (string or ``null``, default: ``null``)
    API key for `api-ninjas.com` random quotes. Sent as ``X-Api-Key`` header.
    Without a key, requests may fail or be rate-limited.

Telegram
--------

``ENABLE_TELEGRAM`` (bool, default: ``false``)
    When ``true``, LCD/status messages are also sent via a shell ``telegram``
    command (must be available on ``PATH``).

Home Assistant
--------------

``HASS_SERVER`` (string, default: ``http://localhost:8123/``)
    Base URL of the Home Assistant instance (trailing slash preserved).

``HASS_TOKEN`` (string, default: ``abc123``)
    Long-lived access token used as ``Authorization: Bearer …`` when posting
    to ``api/states/sensor.<entity_id>``.

``HASS_CHECK_SSL_CERT`` (bool, default: ``false``)
    Verify TLS certificates on HA requests. Set ``true`` for production HTTPS.

Published entities include ``hompi_id``, ``hompi_mode``, ``hompi_temperature``,
``hompi_heating_status``, optional aphorism/ambient/TRV area sensors. See
``misc/hass_integrations/`` for companion YAML snippets.

Climate, MQTT, and TRV
----------------------

``MQTT_BROKER`` (string, default: ``localhost``)
    MQTT broker hostname for TRV telemetry and commands.

``MQTT_PORT`` (integer, default: ``1883``)
    MQTT broker port.

``MQTT_BASE_TOPIC`` (string, default: ``zigbee2mqtt``)
    Topic prefix; TRV topics are ``{MQTT_BASE_TOPIC}/{device}/…``.

``TRV_DATA_EXPIRATION_SECS`` (integer, default: ``3600``)
    Ignore TRV area data older than this many seconds for heating decisions and
    Home Assistant staleness icons.

``TRV_KEEPALIVE`` (bool, default: ``true``)
    Periodically republish MQTT setpoints (~every 20 min) to keep valves in sync.

``THERMOSTAT_MODE`` (integer bitmask, default: ``3``)
    Controls which inputs drive the heating relay. Combine with bitwise OR:

    +-------+-------+----------------------------------------------------------+
    | Value | Name  | Effect                                                   |
    +=======+=======+==========================================================+
    | 0     | NONE  | No automatic heating from these sources.                 |
    | 1     | Main  | Local DS18B20 vs ``req_temp_c`` (``MODULE_TEMP``).       |
    | 2     | TRV   | MQTT TRV zones vs their target temps.                    |
    | 4     | External | Peer ``hompi_slaves`` with active heating.            |
    +-------+-------+----------------------------------------------------------+

    Example: ``3`` = Main + TRV. ``7`` = Main + TRV + External.

``HEATING_THRESHOLD`` (float, default: ``0.1``)
    Hysteresis in °C when deciding to turn heating on from ``off``/``cooling``.

``TEMP_CORRECTION`` (float, default: ``0``)
    Offset added to raw DS18B20 readings (°C).

``THERMO_CHANGE_MINS`` (integer, default: ``5``)
    Minutes to stay in ``warming`` before ``on``, and ``cooling`` before ``off``.

LCD display
-----------

``MODULE_LCD`` (integer, default: ``2``)

    +-------+----------------+-----------------------------------------------+
    | Value | Driver         | Notes                                         |
    +=======+================+===============================================+
    | 0     | Disabled       | No physical LCD; console emulation only.      |
    | 1     | GPIO_CharLCD   | Direct GPIO wiring (see ``dashboard.py``).    |
    | 2     | I2C_CharLCD    | PCF8574 backpack (recommended).               |
    +-------+----------------+-----------------------------------------------+

``I2C_BUS`` (integer, default: ``1``)
    I2C bus number: ``0`` on original Pi, ``1`` on Rev 2 and later.

``I2C_ADDRESS`` (integer, default: ``0x27``)
    I2C address of the LCD module (often ``0x27`` or ``0x3F``).

``LCD_COLUMNS`` / ``LCD_ROWS`` (integers, default: ``16`` / ``2``)
    Display geometry (16×2 or 20×4 supported).

``LCD_SKIP_EXTRA_INFO`` (bool, default: ``true``)
    When ``true``, skip weather and aphorism secondary screens on the LCD
    rotation.

Relays and GPIO
---------------

``RELAY_HILOW_MODE`` (bool, default: ``false``)
    Relay wiring mode:

    - ``false`` — active-high via ``GPIO.setup(pin, OUT)`` when on, ``IN`` when off.
    - ``true`` — active-low: pins preconfigured as ``OUT``; ``LOW`` = on,
      ``HIGH`` = off.

``HEATING_GPIO`` (integer, default: ``17``)
    BCM GPIO pin for the heating/boiler relay. Used when ``MODULE_HEATING`` is
    enabled.

``BUTTONS`` (list of ``[gpio, name]``, see sample)
    Push-button or momentary relay outputs. Names are case-sensitive for API
    commands (e.g. a button named ``Gate`` responds to ``GATE=ON``). Example::

        BUTTONS:
          - [18, Gate]
          - [22, Living]

``BUTTON_DURATION_SECS`` (integer, default: ``1``)
    How long each button relay stays energized when triggered (API or LCD).

Ambient LED
-----------

Requires ``MODULE_AMBIENT: true`` and Pi extras (``pip install hompi[pi]``).

``LED_RIGHT_TO_LEFT`` (bool, default: ``false``)
    Reverse pixel order for WS2801 effects (``hompi.led_effects``).

``AMBIENT_TRANSITION_FRAMES`` (integer, default: ``100``)
    Frame count for smooth colour cross-fades.

Debugging and logging
---------------------

``TEST_MODE`` (integer, default: ``1``)

    +-------+---------------------------------------------------------------+
    | Value | Behaviour                                                     |
    +=======+===============================================================+
    | 0     | Production: real GPIO heating, slower sensor polling (20/80 s).|
    | 1     | Development: no GPIO heating toggles, faster polling (5/20 s), |
    |       | synthetic startup state.                                        |
    | 2     | LCD bignum charset test pattern.                              |
    +-------+---------------------------------------------------------------+

    On non-Pi hosts, keep ``TEST_MODE`` ≥ ``1`` to avoid GPIO errors.

``LOG_LEVEL`` (integer, default: ``1`` = DEBUG)

    +-------+--------+
    | Value | Level  |
    +=======+========+
    | 0     | GPIO   |
    | 1     | DEBUG  |
    | 2     | INFO   |
    | 3     | WARN   |
    | 4     | ERROR  |
    +-------+--------+

    Messages at or above ``LOG_LEVEL`` are printed unless the module is listed
    in ``LOG_MUTE_MODULES``.

``LOG_MUTE_MODULES`` (list of strings, default: ``[]``)
    Module name prefixes to suppress (e.g. ``MQTT``, ``HASS``).

``HW_LOG`` (bool, default: ``false``)
    Verbose logging from hardware stub layers (``spidev`` stub).

Miscellaneous
-------------

``PLACE`` (string, default: ``milan``)
    City name passed to OpenWeatherMap when ``MODULE_METEO`` is enabled.

``IMAGE_PATH`` (string, default: ``./res/images/*.jpg``)
    Glob of slideshow images under the instance ``res/`` directory. Resolved via
    ``hompi.paths.resolve_under_data``.

``THUMB_SIZE`` (two integers, default: ``[800, 800]``)
    Max width/height for API thumbnails (``/_get_image``).

``HOLIDAYS_COUNTRY`` (string, default: ``IT``)
    ISO country code for the ``holidays`` library (automatic vs holiday day types
    in timetables).

Speech
------

``SPEECH_COMMAND`` (string, default: ``espeak -vit+m3 -s150 -k10 "{}"``)
    Shell command template; ``{}`` is replaced with the spoken text. Requires
    ``MODULE_SPEECH: true`` and ``espeak`` installed.

HTTP API key
------------

``API_KEY`` (string or ``null``, default: ``null``)
    Optional pre-shared secret for the web API. When set, clients must pass
    ``?api_key=<MD5_HEX_UPPERCASE>`` where the hash is computed from this
    string (see `docs/API.rst`__). An empty string is treated as unset.

    .. __: API.rst

Quick reference
---------------

All configuration keys with types and defaults:

+-----------------------------+---------------+-------------------------------+
| Key                         | Type          | Default                       |
+=============================+===============+===============================+
| ``TMPFS_ENABLE``            | bool          | ``true``                      |
| ``TMPFS_PATH``              | string        | ``/tmp/``                     |
| ``HOMPI_ID``                | string        | ``Living``                    |
| ``HOMPI_SERVERS``           | list          | ``[]``                        |
| ``HOMPI_EXT_SENSORS``       | list          | ``[]``                        |
| ``MODULE_METEO``            | bool          | ``true``                      |
| ``MODULE_APHORISM``         | bool          | ``true``                      |
| ``APHORISM_KEY``            | string/null   | ``null``                      |
| ``MODULE_DB_LOG``           | bool          | ``false``                     |
| ``MODULE_SPEECH``           | bool          | ``false``                     |
| ``MODULE_AMBIENT``          | bool          | ``false``                     |
| ``ENABLE_TELEGRAM``         | bool          | ``false``                     |
| ``MODULE_HASS``             | bool          | ``true``                      |
| ``HASS_SERVER``             | string        | ``http://localhost:8123/``    |
| ``HASS_CHECK_SSL_CERT``     | bool          | ``false``                     |
| ``HASS_TOKEN``              | string        | ``abc123``                    |
| ``MODULE_TEMP``             | bool          | ``true``                      |
| ``MODULE_HEATING``          | bool          | ``true``                      |
| ``MODULE_TRV``              | bool          | ``true``                      |
| ``MQTT_BROKER``             | string        | ``localhost``                 |
| ``MQTT_PORT``               | int           | ``1883``                      |
| ``MQTT_BASE_TOPIC``         | string        | ``zigbee2mqtt``               |
| ``TRV_DATA_EXPIRATION_SECS``| int           | ``3600``                      |
| ``TRV_KEEPALIVE``           | bool          | ``true``                      |
| ``THERMOSTAT_MODE``         | int           | ``3``                         |
| ``MODULE_LCD``              | int           | ``2``                         |
| ``I2C_BUS``                 | int           | ``1``                         |
| ``I2C_ADDRESS``             | int           | ``0x27``                      |
| ``LCD_COLUMNS``             | int           | ``16``                        |
| ``LCD_ROWS``                | int           | ``2``                         |
| ``LCD_SKIP_EXTRA_INFO``     | bool          | ``true``                      |
| ``RELAY_HILOW_MODE``        | bool          | ``false``                     |
| ``HEATING_GPIO``            | int           | ``17``                        |
| ``BUTTONS``                 | list          | Gate/Living/Bedroom sample    |
| ``BUTTON_DURATION_SECS``    | int           | ``1``                         |
| ``LED_RIGHT_TO_LEFT``       | bool          | ``false``                     |
| ``AMBIENT_TRANSITION_FRAMES``| int          | ``100``                       |
| ``TEST_MODE``               | int           | ``1``                         |
| ``LOG_LEVEL``               | int           | ``1`` (DEBUG)                 |
| ``LOG_MUTE_MODULES``        | list          | ``[]``                        |
| ``HW_LOG``                  | bool          | ``false``                     |
| ``HEATING_THRESHOLD``       | float         | ``0.1``                       |
| ``TEMP_CORRECTION``         | float         | ``0``                         |
| ``THERMO_CHANGE_MINS``      | int           | ``5``                         |
| ``PLACE``                   | string        | ``milan``                     |
| ``IMAGE_PATH``              | string        | ``./res/images/*.jpg``        |
| ``THUMB_SIZE``              | 2-tuple       | ``(800, 800)``                |
| ``HOLIDAYS_COUNTRY``        | string        | ``IT``                        |
| ``SPEECH_COMMAND``          | string        | espeak template               |
| ``API_KEY``                 | string/null   | ``null``                      |
+-----------------------------+---------------+-------------------------------+

Related setup (not in config.yaml)
----------------------------------

- **GPIO / wiring** — ``misc/gpio.txt``
- **Pi boot options** (SPI, 1-Wire) — ``misc/config.txt``
- **Web API** — ``docs/API.rst``
- **Home Assistant snippets** — ``misc/hass_integrations/``

Implementation reference
------------------------

- ``src/hompi/config.py`` — defaults, loader, ``Settings`` object
- ``src/hompi/_path.py`` — ``HOMPI_HOME``, ``HOMPI_CONFIG`` discovery
- ``config.sample.yaml`` — annotated template
- ``tests/test_config.py`` — loader and override tests
