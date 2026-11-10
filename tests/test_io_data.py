# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""Tests for Status and Input data structures in io_data."""

import datetime
import json

from hompi.io_data import Status


def test_send_message_stores_str_and_serializes_to_json():
    status = Status()

    # Pass string
    status.send_message("Test message")
    assert status.message == "Test message"
    assert isinstance(status.message, str)

    # get_output() must serialize to JSON without TypeError
    output_json = status.get_output()
    data = json.loads(output_json)
    assert data["message"] == "Test message"

    # Pass bytes
    status.send_message(b"Byte message")
    assert status.message == "Byte message"
    assert isinstance(status.message, str)

    output_json = status.get_output()
    data = json.loads(output_json)
    assert data["message"] == "Byte message"


def test_status_update_clears_message_and_updates_last_change():
    status = Status()
    now = datetime.datetime.now()
    status.send_message("Expiring message")

    # Time before expiration: message remains
    status.update(now)
    assert status.message == "Expiring message"

    # Time after expiration: message is cleared and last_change is updated
    future_time = now + datetime.timedelta(seconds=50)
    status.update(future_time)
    assert status.message == ""
    assert status.last_change == future_time.isoformat()
