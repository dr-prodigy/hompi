# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.

"""Allow ``python -m hompi`` to start the main process."""

from .service import main

if __name__ == '__main__':
    main()
