# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.

"""Console entry module — delegates to :mod:`hompi.service`."""

from .service import main

__all__ = ['main']

if __name__ == '__main__':
    main()
