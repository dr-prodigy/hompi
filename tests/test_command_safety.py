# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

from unittest.mock import patch, MagicMock

from hompi.utils import os_async_command
from hompi import service
from hompi.config import config


def test_os_async_command_executes_with_shell_false():
    with patch("hompi.utils.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", stderr="")
        os_async_command(["echo", "hello; rm -rf /"])
        mock_run.assert_called_once_with(
            ["echo", "hello; rm -rf /"],
            capture_output=True,
            text=True,
            shell=False,
            timeout=10,
        )


def test_show_message_telegram_passes_argument_list(monkeypatch):
    monkeypatch.setattr(config, "ENABLE_TELEGRAM", True)
    monkeypatch.setattr(config, "TELEGRAM_TOKEN", "token123")
    monkeypatch.setattr(config, "TELEGRAM_CHATID", "chat456")

    with patch("hompi.service.os_async_command") as mock_cmd:
        service.show_message("Test message", 'Message with "quotes" & $(whoami)')
        mock_cmd.assert_called_once()
        args = mock_cmd.call_args[0][0]
        assert isinstance(args, list)
        assert args[0] == "telegram"
        assert args[1] == "-t"
        assert args[2] == "token123"
        assert args[3] == "-c"
        assert args[4] == "chat456"
        assert 'Message with "quotes" & $(whoami)' in args[5]


def test_say_passes_tokenized_args_without_shell(monkeypatch):
    monkeypatch.setattr(config, "MODULE_SPEECH", True)
    monkeypatch.setattr(
        config, "SPEECH_COMMAND", 'espeak -vit+m3 -s150 -k10 "{}"'
    )

    with patch("hompi.service.subprocess.Popen") as mock_popen:
        service.say('Test speech with "quotes"; rm -rf /')
        mock_popen.assert_called_once()
        cmd = mock_popen.call_args[0][0]
        assert isinstance(cmd, list)
        assert cmd[0] == "espeak"
        assert 'Test speech with "quotes"; rm -rf /' in cmd[-1]
