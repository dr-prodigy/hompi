# -*- coding: utf-8 -*-

from utils import log_stdout, log_stderr, LOG_GPIO, LOG_DEBUG, LOG_INFO, LOG_WARN, LOG_ERROR

# stubs
BOARD = 1
OUT = 'OUT'
IN = 'IN'
HIGH = 'HIGH'
LOW = 'LOW'
BCM = 'BCM'

def setmode(a):
    log_stdout('GPIO', 'setmode {}'.format(a), LOG_GPIO)


def setup(a, b):
    log_stdout('GPIO', 'setup {},{}'.format(a, b), LOG_GPIO)


def output(a, b):
    log_stdout('GPIO', 'output {},{}'.format(a, b), LOG_GPIO)


def cleanup():
    log_stdout('GPIO', 'cleanup', LOG_GPIO)


def setwarnings(flag):
    log_stdout('GPIO', 'setwarnings {}'.format(flag), LOG_GPIO)


class PWM():
    def __init__(self, a, b):
        log_stdout('GPIO', '__PWM__ {}'.format(a, b), LOG_GPIO)

    def start(self, a):
        log_stdout('GPIO', 'PWM.start {}'.format(a), LOG_GPIO)

    def ChangeFrequency(self, a):
        log_stdout('GPIO', 'PWM.ChangeFrequency {}'.format(a), LOG_GPIO)

    def ChangeDutyCycle(self, a):
        log_stdout('GPIO', 'PWM.ChangeDutyCycle {}'.format(a), LOG_GPIO)
