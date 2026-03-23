# -*- coding: utf-8 -*-

from enum import Enum
import numpy as np
import pyvisa

class Chameleon():

    def get_ready_state(self):
        return True

    def open_communication(self, port):

        try:
            rm = pyvisa.ResourceManager()
            self._device = rm.open_resource(port)
            self._device.baud_rate = 19200
            self._device.data_bits = 7
            self._device.parity = pyvisa.constants.Parity.even
            self._device.stop_bits = pyvisa.constants.StopBits.one
            self._device.read_termination = '\r\n'

            self._device.query('ECHO=0')
            self._device.query('PROMPT=0')
            initialized = True

        except:
            initialized = False

        return initialized

    def close_communication(self):
        self._device.close()


    def get_laser_state(self):
        laser = self._device.query('?L')
        if laser == 0:
            laser_state = 'OFF'
        elif laser == 1:
            laser_state = 'ON'
        return laser_state

    def set_laser_state(self, laser_state):
        if laser_state == 'OFF':
            laser = 0
        elif laser_state == 'ON':
            laser = 1
        self._device.write('L={}'.format(laser))


    def get_laser_power(self):
        power = self._device.query('?UF')
        return power


    def get_wavelength_range(self):
        wl_min = self._device.query('?TMIN')
        wl_max = self._device.query('?TMAX')
        return wl_min, wl_max

    def get_wavelength(self):
        wl = self._device.query('?VW')
        return wl

    def set_wavelength(self, wl):
        self._device.write('VW={}'.format(wl))


    def get_shutter(self):
        shutter = self._device.query('?S')
        if shutter == 0:
            shutter_state = 'CLOSED'
        elif shutter == 1:
            shutter_state = 'OPEN'
        return shutter_state

    def set_shutter(self, shutter_state):
        if shutter_state == 'CLOSED':
            shutter = 0
        elif shutter_state == 'OPEN':
            shutter == 1
        self._device.write('S={}'.format(shutter))


