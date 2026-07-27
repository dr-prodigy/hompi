# Copyright (C)2018-26 Maurizio Montel (dr-prodigy) <dr.prodigy.github@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>

"""Console entry for ``hompi``: ``hompi init`` or run the control daemon."""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> None:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == 'init':
        from .init import cmd_init
        raise SystemExit(cmd_init(argv[1:]))
    if argv and argv[0] in ('-h', '--help'):
        print('Usage: hompi [init [options]]')
        print('  (no args)   start the Hompi control daemon')
        print('  init        bootstrap instance dirs, config, uWSGI, systemd')
        print('  init -h     show init options')
        raise SystemExit(0)

    from .service import main as service_main
    service_main()


if __name__ == '__main__':
    main()
