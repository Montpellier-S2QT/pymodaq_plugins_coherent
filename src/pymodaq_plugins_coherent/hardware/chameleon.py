# -*- coding: utf-8 -*-

import numpy as np
import pyvisa
from time import sleep

class Chameleon():

    def get_ready_state(self):
        return True

    def open_communication(self, address):
        '''
            Opens VISA communication with Chameleon laser source

            Input:
                str : VISA address

            Output:
                None
        '''
        try:
            rm = pyvisa.ResourceManager()
            print(rm)
            self._device = rm.open_resource(address)
            self._device.baud_rate = 19200
            self._device.read_termination = '\r\n'

            self._device.clear()
            self._device.query('ECHO=0')
            self._device.query('PROMPT=0')
            initialized = True

        except:
            initialized = False

        return initialized

    def close_communication(self):
        '''
            Closes VISA communication with Chameleon laser source

            Input:
                None

            Output:
                None
        '''
        self._device.close()

    def get_SN(self):
        '''
            Returns the state of the laser (ON/OFF)

            Input:
                None

            Output:
                str : serial number
        '''
        return self._device.query('?SN')

    def get_laser_state(self):
        '''
            Returns the state of the laser (ON/OFF)

            Input:
                None

            Output:
                str : laser state ('ON' or 'OFF')
        '''
        laser = self._device.query('?L')
        if laser == '0':
            laser_state = 'OFF'
        elif laser == '1':
            laser_state = 'ON'
        return laser_state

    def set_laser_state(self, laser_state):
        '''
            Returns the state of the laser (ON/OFF)

            Input:
                str : laser state ('ON' or 'OFF')

            Output:
                None
        '''
        if laser_state == 'OFF':
            laser = 0
        elif laser_state == 'ON':
            laser = 1
        self._device.query('L={}'.format(laser))


    def get_laser_power(self):
        '''
            Returns current laser power in mW

            Input:
                None

            Output:
                int : laser power
        '''
        power = self._device.query('?UF')
        return int(power)


    def get_wavelength_range(self):
        '''
            Returns the available wavelength range

            Input:
                None

            Output:
                (int,int) : wavelength range (min,max)
        '''
        wl_min = self._device.query('?TMIN')
        wl_max = self._device.query('?TMAX')
        return int(wl_min), int(wl_max)

    def get_wavelength(self):
        '''
            Returns current wavelength in nm

            Input:
                None

            Output:
                int : wavelength in nm
        '''
        wl = self._device.query('?VW')
        return int(wl)

    def set_wavelength(self, wl):
        '''
            Sets wavelength in nm

            Input:
                int : wavelength in nm

            Output:
                None
        '''
        self._device.query('VW={}'.format(wl))

    def set_wavelength_step(self, step):
        '''
            Changes wavelength by specified step in nm

            Input:
                int : wavelength step in nm

            Output:
                None
        '''
        self._device.query('VWS={}'.format(step))

    def home_stepper(self):
        '''
            Homes tuning motor

            Input:
                None

            Output:
                None
        '''
        self._device.query('HM=1')

    def check_tuning_done(self):
        '''
            Checks that the laser has finished tuning

            Input:
                None

            Output:
                bool : tuning done?
        '''
        return self._device.query('?TS') == 0

    def get_align_mode(self):
        '''
            Gets alignment mode

            Input:
                None

            Output:
                (bool, int, int) : state, available power and wavelength of the alignment mode
        '''
        mode = False
        output = self._device.query('?ALIGN')
        if output == '1': align_mode = True
        else: align_mode = False
        align_power = self._device.query('?ALIGNP')
        align_wl = self._device.query('?ALIGNW')
        return align_mode, align_power, align_wl

    def set_align_mode(self, mode):
        '''
            Sets alignment mode

            Input:
                mode : bool

            Output:
                None
        '''
        if mode: output = '1'
        else: output = '0'
        self._device.query('ALIGN={}'.format(output))

    def get_shutter(self):
        '''
            Returns shutter state (OPEN/CLOSED)

            Input:
                None

            Output:
                str : shutter state ('OPEN' or 'CLOSED')
        '''
        shutter = self._device.query('?S')
        if shutter == '0':
            shutter_state = 'CLOSED'
        elif shutter == '1':
            shutter_state = 'OPEN'
        return shutter_state

    def set_shutter(self, shutter_state):
        '''
            Sets shutter state (OPEN/CLOSED)

            Input:
                str : shutter state ('OPEN' or 'CLOSED')

            Output:
                None
        '''
        if shutter_state == 'CLOSED':
            shutter = 0
        elif shutter_state == 'OPEN':
            shutter = 1
        self._device.query('S={}'.format(shutter))


