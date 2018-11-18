# -*- coding: utf-8 -*-
import config

DEBUG_LOG = config.VERBOSE_LOG

# stubs
BOARD = 1
OUT = 'OUT'
IN = 'IN'
HIGH = 'HIGH'
LOW = 'LOW'
BCM = 'BCM'


def setmode(a):
    if DEBUG_LOG:
        print('GPIO.setmode {}'.format(a))


def setup(a, b):
    if DEBUG_LOG:
        print('GPIO.setup {},{}'.format(a, b))


def output(a, b):
    if DEBUG_LOG:
        print('GPIO.output {},{}'.format(a, b))


def cleanup():
    if DEBUG_LOG:
        print('GPIO.cleanup')


def setwarnings(flag):
    if DEBUG_LOG:
        print('GPIO.setwarnings {}'.format(flag))


class PWM():
    def __init__(self, a, b):
        if DEBUG_LOG:
            print('__GPIO.PWM__ {}'.format(a, b))

    def start(self, a):
        if DEBUG_LOG:
            print('GPIO.PWM.start {}'.format(a))

    def ChangeFrequency(self, a):
        if DEBUG_LOG:
            print('GPIO.PWM.ChangeFrequency {}'.format(a))

    def ChangeDutyCycle(self, a):
        if DEBUG_LOG:
            print('GPIO.PWM.ChangeDutyCycle {}'.format(a))
