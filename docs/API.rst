.. Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
.. This file is part of hompi <https://github.com/dr-prodigy/hompi>

==========
Web API
==========

hompi exposes a Flask HTTP API (``hompi.api:app``) for reading live status,
querying configuration data, sending control commands, and updating heating
programmes. Clients include a custom web UI, Home Assistant, and (historically)
a mobile app. Master nodes also pull peer status over this API.

All routes are mounted under the fixed prefix ``/hompi`` (constant
``API_PREFIX`` in ``hompi.api``).

Base URL
--------

+----------------------------+--------------------------------------------------+
| Environment                | Example base URL                                 |
+============================+==================================================+
| Flask debug (``hompi-api``)| ``http://127.0.0.1:5000/hompi``                  |
| Reverse proxy (production) | ``http://<host>:5000/hompi`` (lighttpd/nginx)    |
| uWSGI private socket       | ``127.0.0.1:3031`` — **uwsgi protocol**, not HTTP|
+----------------------------+--------------------------------------------------+

Clients always talk HTTP to the reverse proxy (or Flask debug). They do **not**
open the uWSGI socket directly.

When hompi runs behind lighttpd or nginx with a ``/hompi`` mount, the WSGI
middleware ``RestoreMountPrefixMiddleware`` rewrites ``PATH_INFO`` so routing
matches the same URLs as standalone Flask debug mode.

Authentication
--------------

If ``API_KEY`` is set in ``config.yaml``, every endpoint requires a query
parameter::

    ?api_key=<MD5_HEX_UPPERCASE>

The server stores the **MD5 hash** (uppercase hex) of the configured
``API_KEY`` string — not the raw secret. Clients must pass that hash.

If ``API_KEY`` is ``null`` or unset, authentication is disabled and all
requests are accepted.

Example (with ``API_KEY: change-me`` in config, hash
``6969AF205F368E464693AFA423D0BB4C``)::

    curl 'http://localhost:5000/hompi/_get_status?api_key=6969AF205F368E464693AFA423D0BB4C'

Failed authentication returns ``403 Forbidden`` with body ``Forbidden``.

Side effects and daemon refresh
-------------------------------

Most write operations insert or update SQLite tables and then call
``_signal_server()``, which sends **SIGHUP** to the hompi daemon (via its PID
file). The daemon reloads state on the next cycle.

``/_send_command`` queues into ``gm_input``; the daemon's ``process_input()``
consumes those rows. ``/_refresh`` triggers SIGHUP without changing data.

Response conventions
--------------------

+-------------+---------------------------------------------------------------+
| HTTP status | Meaning                                                       |
+=============+===============================================================+
| 200         | Success. Body is usually ``Ok`` (writes) or JSON (reads).     |
| 400         | Bad request / parse error (writes). Body: ``Error``.          |
| 403         | Missing or wrong ``api_key``. Body: ``Forbidden``.            |
| 405         | HTTP method not allowed. Body: ``Method not allowed``.        |
| 415         | PUT with unsupported content type. Body: ``Unsupported Media  |
|             | Type``.                                                       |
| 500         | Database or internal error (reads). Body: ``Error``.          |
+-------------+---------------------------------------------------------------+

Read endpoints (GET)
--------------------

``GET /hompi/_get_system_info``
    Exposes which **hompi services are enabled** for this instance, as derived
    from configuration (``MODULE_*``, ``BUTTONS``, optional ambient command
    hints). Built by ``hompi.io_data.SystemInfo``.

    Typical JSON fields:

    - ``modules`` — list of enabled module names (e.g. ``ambient``, ``meteo``,
      ``temp``, ``lcd``, ``aphorism``, ``db_log``)
    - ``buttons`` — display names from ``BUTTONS`` config
    - ``ambient_commands`` — present when ambient is enabled
    - ``temperatures`` — reserved list (may be empty)

``GET /hompi/_get_status``
    Exposes the **internal runtime status** of all active hompi services.
    Consumed by the custom web UI, Home Assistant, peer/master hompi nodes, and
    formerly the mobile app.

    Body is the JSON stored in ``gm_output.data`` (same shape as
    ``hompi.io_data.Status``). Fields depend on enabled modules; core ones
    include:

    - Identity / sync: ``id``, ``last_update``, ``last_change``,
      ``last_program_change``
    - Climate: ``int_temp_c``, ``mode_id``, ``mode_desc``, ``short_mode_desc``,
      ``timetable_desc``, ``day_type_desc``, ``req_temp_c``, ``req_temp_desc``,
      ``req_start_time``, ``req_end_time``, ``heating_status``
    - TRV (if ``MODULE_TRV``): ``areas``, ``req_area_temps``, ``main_area_id``
    - Relays: ``sw_sig``, ``sw_status`` (parallel to ``BUTTONS``)
    - UI: ``current_image``, ``message``
    - Ambient (if enabled): ``ambient_color``, ``ambient_effect``, ``ambient_on``
    - Meteo (if enabled): ``ext_temp_c``, ``place``, ``weather``, ``humidity``,
      ``pressure``, ``wind``
    - Aphorism (if enabled): ``aphorism_text``, ``aphorism_author``
    - Peers / sensors: ``hompi_slaves``, ``hompi_ext_sensors``

``GET /hompi/_get_list/<data_list>``
``GET /hompi/_get_list/<data_list>/<key>``
    Query configuration tables. Returns a JSON array of row objects.

    Supported ``data_list`` values (no further types at present):

    +--------------+---------------------------+--------------------------------+
    | Value        | Table                     | Notes                          |
    +==============+===========================+================================+
    | ``control``  | ``gm_control``            | Active timetable pointer       |
    | ``timetable``| ``gm_timetable``          | Weekly programmes              |
    | ``daytype``  | ``gm_timetable_day_type`` | Day-type labels                |
    | ``temp``     | ``gm_temp``               | Joined with ``gm_timetable_temp`` |
    | ``typedata`` | ``gm_timetable_type_data``| Schedule slots per day type    |
    +--------------+---------------------------+--------------------------------+

    Optional ``key`` filters by row ``id`` (or ``day_type_id`` for
    ``typedata``, or ``timetable_id`` for ``temp``).

``GET /hompi/_get_temp_chart``
    Temperature log for charting: rows from ``gm_log`` where ``event = '.'``
    and date within the last 7 days. Fields include ``datetime``,
    ``datetime_epoch``, ``int_temp_c``, ``ext_temp_c``, ``req_temp_c``,
    ``description``.

``GET /hompi/_get_server_list``
    JSON list of peer IDs currently present under ``hompi_slaves`` in status
    (nodes this instance knows about via ``HOMPI_SERVERS`` polling).

``GET /hompi/_get_image/<image_name>``
    Returns a JPEG thumbnail from the configured image directory
    (``IMAGE_PATH``). Thumbnails are generated on first request and cached
    under ``thumbs/`` using ``THUMB_SIZE`` from config.

Deprecated / unused read endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``GET /hompi/_get_list2/<server>/<list>[/<key>]``
    Proxied ``/_get_list`` to a remote node. **No longer used**; kept for
    compatibility. Prefer calling the peer's own ``/_get_list`` directly.

Write endpoints
---------------

``PUT /hompi/_send_command``
``GET /hompi/_send_command/<command_json>``
    Queue a command for the daemon by inserting into ``gm_input`` (deduplicated
    by identical ``data``). Returns ``Ok``. The daemon's ``process_input()``
    parses the payload (see `Command payloads`_).

    **PUT:** request body is stored as-is. Expected form is a legacy command
    string, e.g. ``GATE=ON``. A JSON command object
    (``{"command":"…","arg":"…","value":"…"}``) is also accepted if that is
    what you PUT.

    **GET:** path must be URL-encoded JSON with a ``data`` field holding the
    command string::

        {"data": "GATE=ON"}

``PUT /hompi/_set_control``
``GET /hompi/_set_control/<data_json>``
    Set the active timetable in ``gm_control``. JSON body (PUT) or path (GET)
    must include either:

    - ``timetable_id`` (integer), or
    - ``timetable_desc`` (string matching ``gm_timetable.description``)

``PUT /hompi/_set_temp/<id>``
``GET /hompi/_set_temp/<data_json>``
    Update ``gm_temp.temp_c`` for the given temperature preset.

    **PUT:** ``id`` in the path; JSON body ``{"temp_c": <float>}``.

    **GET:** ``data_json`` is ``{"id": <int>, "temp_c": <float>}``.

``GET /hompi/_set_timetable/<data_json>``
    Intended for a UI to assign a day-type to one weekday column of a heating
    timetable. JSON fields:

    - ``id`` — timetable row id
    - ``day`` — one of ``monday``, ``tuesday``, ``wednesday``, ``thursday``,
      ``friday``, ``saturday``, ``sunday``, ``pre_holiday``, ``holiday``
    - ``day_type_id`` — day-type id written into that column

``GET /hompi/_set_timetable_data/<data_json>``
    Intended for a UI to rewrite the schedule slots of a day type.
    ``data_json`` is a JSON **array** of objects::

        [
          {"orderby": 1, "temp_id": 2, "time_hhmm": 630, "day_type_id": 1},
          {"orderby": 2, "temp_id": 1, "time_hhmm": 830, "day_type_id": 1}
        ]

    - ``time_hhmm`` — wall time as an integer, e.g. ``830`` = 08:30,
      ``1830`` = 18:30
    - ``temp_id`` — preset from ``gm_temp``
    - ``orderby`` — slot order
    - ``day_type_id`` — day type being rewritten

    Existing rows for that ``day_type_id`` are deleted, then the array is
    inserted. Signals the daemon afterwards.

``GET /hompi/_refresh``
    Signal the daemon to refresh (SIGHUP) without modifying the database.
    Returns ``Ok``.

Deprecated / unused write endpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``PUT|GET /hompi/_set_temp2/<server>/<data>``
    Local or proxied temperature set. **No longer used**; kept for
    compatibility. Prefer ``/_set_temp`` on the target node.

Command payloads
----------------

Commands queued via ``/_send_command`` are parsed by ``process_input()`` in
``hompi.service``.

Legacy string format (``KEY=VALUE`` or ``KEY=ARG,VALUE``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Examples::

    GATE=ON
    BUTTON=0
    TT=2
    TEMP=1,21.5
    LCD=0
    MESSAGE=Hello
    AMBIENT=COLOR,000000
    AMBIENT=XMAS_DAISY,.1
    AMBIENT=TV_SIM,.05

Recognized ``command`` keys (case-insensitive):

+-------------+----------------------------------------------------------------+
| Command     | Effect                                                         |
+=============+================================================================+
| ``TT``      | Set active timetable: ``TT=<timetable_id>``                    |
| ``TEMP``    | Set preset temp: ``TEMP=<temp_id>,<temp_c>``                   |
| ``LCD``     | Backlight: ``LCD=0`` (off for 4 h) or ``LCD=1`` (on)           |
| ``MESSAGE`` | Show LCD/status message: ``MESSAGE=<text>``                    |
| ``AMBIENT`` | LED strip; see `Ambient commands`_                             |
| ``GATE``    | Pulse the relay whose ``BUTTONS`` name is ``GATE`` (case-      |
|             | insensitive; sample config uses ``Gate``)                      |
| ``BUTTON``  | Pulse relay by zero-based index: ``BUTTON=<index>``            |
| ``PROG_T``  | **Planned / not implemented yet** (see comments in             |
|             | ``process_input``)                                             |
+-------------+----------------------------------------------------------------+

Ambient commands
~~~~~~~~~~~~~~~~

With command ``AMBIENT``:

- Legacy: ``AMBIENT=<arg>,<value>`` (if ``arg`` is omitted, ``COLOR`` is
  assumed when using JSON with empty arg)
- JSON: ``{"command":"AMBIENT","arg":"<ARG>","value":"<VALUE>"}``

``arg`` values:

+---------------+----------------------------------------------------------------+
| ``arg``       | Meaning                                                        |
+===============+================================================================+
| ``COLOR``     | Solid colour; ``value`` is RGB hex without ``#`` (e.g.         |
|               | ``FF8800``). Auto-off after 4 hours.                           |
| ``COLOR_HS``  | HS colour (Home Assistant style). Auto-off after 4 hours.      |
| ``BRIGHTNESS``| Luma / brightness level.                                       |
| ``STATUS``    | ``ON`` or ``OFF``.                                             |
| *effect name* | Run a named LED effect; ``value`` is effect parameters (luma   |
|               | and/or transition delay — see below).                          |
+---------------+----------------------------------------------------------------+

Effects accepted by the ambient controller (``EFFECT_LIST`` in
``hompi.ambient``; names are lowercased at runtime):

- ``xmas_daisy``
- ``tv_sim``
- ``test_loop``
- ``rainbow``
- ``rainbow_cycle``
- ``theater_chase_rainbow``
- ``stop_effect``
- ``reset``

The LED worker ``hompi.led_effects`` also implements lower-level programs used
internally (``clear``, ``set_color``, ``crossfade``, ``go_to_sleep``,
``color_wipe``, ``color_curtain``, ``theater_chase``, ``wipe_in_out``,
``curtain_in_out``, …). CLI help for that module documents positional params as::

    brightness=0..1, rgb1='xxxxxx', rgb2='xxxxxx', wait=.05, reverse=False

When driving effects through ``/_send_command``, the ``value`` string is passed
through as effect parameters: typically a **luma level** (e.g. ``.1``) and/or a
**transition delay** (e.g. ``.05``), matching those semantics.

JSON format
~~~~~~~~~~~

Also accepted as the raw body of PUT (or as the string inside GET's ``data``
field if you embed JSON there)::

    {"command": "TEMP", "arg": "1", "value": "21.5"}
    {"command": "TT", "value": "2"}
    {"command": "MESSAGE", "value": "Hello"}
    {"command": "AMBIENT", "arg": "COLOR", "value": "000000"}
    {"command": "AMBIENT", "arg": "TV_SIM", "value": ".05"}

Fields ``command``, ``arg``, and ``value`` are uppercased before dispatch;
effect names are lowercased again inside ambient.

Multi-hompi
-----------

Configure peer base URLs in ``HOMPI_SERVERS`` (e.g.
``http://192.168.1.10:5000/hompi``). The daemon periodically GETs each peer's
``/_get_status`` and stores summaries under ``hompi_slaves`` in local status
JSON (used by dashboards and ``/_get_server_list``).

HTTP proxy helpers ``/_get_list2`` and ``/_set_temp2`` remain in the code but
are **not used anymore**; call the peer API directly instead.

Running the API
---------------

Development:

.. code-block:: bash

    hompi-api
    # or: python -m hompi.api

Production (uWSGI module ``hompi.api:app``, see packaged ``uwsgi.ini``; put
HTTP in front via lighttpd/nginx):

.. code-block:: bash

    uwsgi --ini uwsgi.ini

Home Assistant examples
-----------------------

Sample REST commands and URL secrets live under ``misc/hass_integrations/``.
Typical patterns:

.. code-block:: yaml

    # secrets.yaml
    hompi_set_control_url: "http://localhost:5000/hompi/_set_control?api_key="
    hompi_set_temp_url: "http://localhost:5000/hompi/_set_temp/{{ id }}?api_key="
    hompi_gate_url: "http://localhost:5000/hompi/_send_command/{\"data\":\"GATE=ON\"}?api_key="

.. code-block:: yaml

    # rest_command.yaml
    hompi_set_control:
      url: !secret hompi_set_control_url
      method: put
      content_type: "application/json"
      payload: '{"timetable_desc": "{{ value }}"}'

    hompi_set_temp:
      url: !secret hompi_set_temp_url
      method: put
      content_type: "application/json"
      payload: '{"temp_c": {{ value }}}'

    hompi_command:
      url: !secret hompi_command_url
      method: put
      content_type: "application/json"
      payload: '{"command": "{{ command }}", "arg": "{{ arg }}", "value": "{{ value }}"}'

Implementation reference
------------------------

Source: ``src/hompi/api.py``

Related modules:

- ``hompi.service`` — ``process_input()``, ``gm_input`` / ``gm_output``
- ``hompi.io_data`` — ``Status`` and ``SystemInfo`` JSON shapes
- ``hompi.ambient`` / ``hompi.led_effects`` — ambient effects and LED params
- ``hompi.config`` — ``API_KEY``, ``IMAGE_PATH``, ``HOMPI_SERVERS``, ``BUTTONS``
- ``tests/test_api_routes.py`` — URL prefix and proxy mount behaviour
- ``misc/hass_integrations/`` — Home Assistant REST examples
