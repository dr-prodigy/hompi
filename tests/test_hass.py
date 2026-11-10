# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

from unittest.mock import patch, MagicMock
from hompi import hass


def test_publish_status_uses_timeout():
    io_status = MagicMock()
    io_status.id = "Living"
    io_status.mode_desc = "Auto"
    io_status.req_temp_desc = "Off"
    io_status.heating_status = "off"
    io_status.int_temp_c = 21.5
    io_status.areas = {}

    io_system = MagicMock()
    io_system.temperatures = []

    ambient = MagicMock()

    with patch("hompi.hass.post") as mock_post:
        mock_response = MagicMock()
        mock_response.text = '{"message": "ok"}'
        mock_post.return_value = mock_response

        hass.old_entity = {}
        hass.publish_status(io_status, io_system, ambient)

        assert mock_post.called
        for call in mock_post.call_args_list:
            assert "timeout" in call.kwargs
            assert call.kwargs["timeout"] == hass.HASS_TIMEOUT_SECS
