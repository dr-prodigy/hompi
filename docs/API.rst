.. Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
.. This file is part of hompi <https://github.com/dr-prodigy/hompi>

==========
Web API
==========

hompi exposes a Flask HTTP API (``hompi.api:app``) for reading live status,
querying configuration data, sending control commands, and proxying requests
to other hompi nodes on the network.

All routes are mounted under the fixed prefix ``/hompi`` (constant
``API_PREFIX`` in ``hompi.api``).

Base URL
--------

+---------------------------+--------------------------------------------------+
| Environment               | Example base URL                                 |
+===========================+==================================================+
| Flask debug (``hompi-api``)| ``http://127.0.0.1:5000/hompi``                 |
| uWSGI (production)        | ``http://127.0.0.1:3031/hompi`` (via reverse    |
|                           | proxy)                                           |
| Reverse proxy mount       | ``http://<host>/hompi``                          |
+---------------------------+--------------------------------------------------+

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

The ``/_refresh`` endpoint triggers the same SIGHUP without changing data.

Response conventions
--------------------

+-------------+---------------------------------------------------------------+
| HTTP status | Meaning                                                       |
+=============+===============================================================+
| 200         | Success. Body is usually ``Ok`` (writes) or JSON (reads).    |
| 400         | Bad request / parse error (writes). Body: ``Error``.           |
| 403         | Missing or wrong ``api_key``. Body: ``Forbidden``.             |
| 405         | HTTP method not allowed. Body: ``Method not allowed``.         |
| 415         | PUT with unsupported content type. Body: ``Unsupported Media   |
|             | Type``.                                                       |
| 500         | Database or internal error (reads). Body: ``Error``.           |
+-------------+---------------------------------------------------------------+

Read endpoints (GET)
--------------------

``GET /hompi/_get_system_info``
    Static capability snapshot from config: enabled modules, relay/button
    names, ambient commands. Returns JSON from ``SystemInfo`` (fields such as
    ``modules``, ``buttons``, ``ambient_commands``).

``GET /hompi/_get_status``
    Current runtime status JSON stored in ``gm_output.data``. Same structure
    as ``hompi.io_data.Status`` (temperatures, mode, heating state, optional
    TRV areas, ambient, weather, ``hompi_slaves``, etc.).

``GET /hompi/_get_list/<data_list>``
``GET /hompi/_get_list/<data_list>/<key>``
    Query configuration tables. Returns a JSON array of row objects.

    ``data_list`` selects the table:

    +------------+-------------------------+----------------------------------+
    | Value      | Table                   | Notes                            |
    +============+=========================+==================================+
    | ``control``| ``gm_control``          | Active timetable pointer         |
    | ``timetable`` | ``gm_timetable``     | Weekly programmes                |
    | ``daytype``| ``gm_timetable_day_type`` | Day-type labels               |
    | ``temp``   | ``gm_temp``             | Joined with ``gm_timetable_temp``|
    | ``typedata`` | ``gm_timetable_type_data`` | Schedule slots per day type |
    +------------+-------------------------+----------------------------------+

    Optional ``key`` filters by row ``id`` (or ``day_type_id`` for
    ``typedata``, or ``timetable_id`` for ``temp``).

``GET /hompi/_get_temp_chart``
    Temperature log for charting: rows from ``gm_log`` where ``event = '.'``
    and date within the last 7 days. Fields include ``datetime``,
    ``datetime_epoch``, ``int_temp_c``, ``ext_temp_c``, ``req_temp_c``,
    ``description``.

``GET /hompi/_get_server_list``
    JSON array of keys from ``hompi_slaves`` in the current status (remote
    hompi node IDs known to this server).

``GET /hompi/_get_list2/<server>/<list>``
``GET /hompi/_get_list2/<server>/<list>/<key>``
    Same as ``/_get_list`` but for a remote node. ``server`` is a slave ID
    from ``hompi_slaves`` (use ``local`` for this host). Proxies to the
    slave's ``/_get_list`` URL (2 s timeout).

``GET /hompi/_get_image/<image_name>``
    Returns a JPEG thumbnail from the configured image directory
    (``IMAGE_PATH``). Thumbnails are generated on first request and cached
    under ``thumbs/`` using ``THUMB_SIZE`` from config.

Write endpoints
---------------

``PUT /hompi/_send_command``
``GET /hompi/_send_command/<command_json>``
    Queue a command for the daemon by inserting into ``gm_input`` (deduplicated
    by identical ``data``). Returns ``Ok``.

    **PUT:** raw request body is stored as-is (typically a JSON command string).

    **GET:** ``command_json`` must be URL-encoded JSON with a ``data`` field
    containing the command payload, e.g.::

        {"data": "GATE=ON"}

    See `Command payloads`_ below for supported command strings.

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

``PUT /hompi/_set_temp2/<server>/<data>``
``GET /hompi/_set_temp2/<server>/<data>``
    Set temperature locally (``server=local``) or proxy to a remote hompi
    (same ``data`` format as ``/_set_temp``).

``GET /hompi/_set_timetable/<data_json>``
    Update one weekday column on ``gm_timetable``. JSON fields:

    - ``id`` — timetable row id
    - ``day`` — one of ``monday``, ``tuesday``, ``wednesday``, ``thursday``,
      ``friday``, ``saturday``, ``sunday``, ``pre_holiday``, ``holiday``
    - ``day_type_id`` — new day-type id for that column

``GET /hompi/_set_timetable_data/<data_json>``
    Replace all schedule slots for a day type. ``data_json`` is a JSON array
    of objects with ``orderby``, ``temp_id``, ``time_hhmm``, ``day_type_id``.
    Existing rows for that ``day_type_id`` are deleted before insert.

``GET /hompi/_refresh``
    Signal the daemon to refresh (SIGHUP) without modifying the database.
    Returns ``Ok``.

Command payloads
----------------

Commands queued via ``/_send_command`` are parsed by ``process_input()`` in
``hompi.service``. Two formats are supported.

Legacy string format (``KEY=VALUE`` or ``KEY=ARG,VALUE``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Examples used in Home Assistant integrations (``misc/hass_integrations/``)::

    GATE=ON
    AMBIENT_COLOR=000000
    AMBIENT_XMAS=.1
    AMBIENT_TV_SIM=.05

Recognized ``command`` keys (case-insensitive):

+-----------+----------------------------------------------------------------+
| Command   | Effect                                                         |
+===========+================================================================+
| ``TT``    | Set timetable: ``TT=<timetable_id>``                           |
| ``TEMP``  | Set preset temp: ``TEMP=<temp_id>,<temp_c>``                     |
| ``LCD``   | Backlight: ``LCD=0`` (off 4 h) or ``LCD=1`` (on)                |
| ``MESSAGE`` | Show LCD/status message: ``MESSAGE=<text>``                    |
| ``AMBIENT`` | LED strip; see ambient variants below                          |
| ``GATE``  | Pulse relay named ``Gate`` in ``BUTTONS`` config                 |
| ``BUTTON``| Pulse relay by index: ``BUTTON=<index>``                         |
+-----------+----------------------------------------------------------------+

Ambient sub-commands (``AMBIENT_<sub>=<value>`` or JSON ``arg``/``value``):

- ``COLOR`` / ``COLOR_HS`` — RGB or HS color (hex without ``#``)
- ``BRIGHTNESS``
- ``STATUS`` — ``ON`` / ``OFF``
- Effect names (e.g. ``XMAS``, ``TV_SIM``) with numeric parameter

JSON format (preferred for PUT)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

    {"command": "TEMP", "arg": "1", "value": "21.5"}
    {"command": "TT", "value": "2"}
    {"command": "MESSAGE", "value": "Hello"}

Fields ``command``, ``arg``, and ``value`` are uppercased before dispatch.

Multi-hompi
-----------

Configure peer URLs in ``HOMPI_SERVERS`` (e.g.
``http://192.168.1.10:5000/hompi``). The daemon periodically pulls each
peer's ``/_get_status`` and stores summaries under ``hompi_slaves`` in status
JSON.

Proxy endpoints ``/_get_list2`` and ``/_set_temp2`` resolve the slave's base
URL from ``hompi_slaves[<server>].address`` and forward the request with the
same ``api_key``.

Running the API
---------------

Development:

.. code-block:: bash

    hompi-api
    # or: python -m hompi.api

Production (uWSGI module ``hompi.api:app``, see packaged ``uwsgi.ini``):

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

Implementation reference
------------------------

Source: ``src/hompi/api.py``

Related modules:

- ``hompi.service`` — consumes ``gm_input``, maintains ``gm_output``
- ``hompi.io_data`` — ``Status`` and ``SystemInfo`` JSON shapes
- ``hompi.config`` — ``API_KEY``, ``IMAGE_PATH``, ``HOMPI_SERVERS``
- ``tests/test_api_routes.py`` — URL prefix and proxy mount behaviour
