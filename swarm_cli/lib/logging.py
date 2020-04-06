# Create a logger object.
import logging

import coloredlogs
import verboselogs

logger = verboselogs.VerboseLogger('swarm-cli')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# By default the install() function installs a handler on the root logger,
# this means that log messages from your code and log messages from the
# libraries that you use will all show up on the terminal.
# coloredlogs.install(level='DEBUG')

# If you don't want to see log messages from libraries, you can pass a
# specific logger object to the install() function. In this case only log
# messages originating from that logger will show up on the terminal.
# fmt="%(levelname)s %(message)s"
fmt = "%(message)s"
coloredlogs.install(fmt=fmt, level=verboselogs.SPAM, logger=logger)
