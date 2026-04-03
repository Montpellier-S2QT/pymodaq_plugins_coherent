
from typing import Union, List, Dict
from time import sleep
from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun,
                                                          main, DataActuatorType, DataActuator)

from pymodaq_utils.utils import ThreadCommand  # object used to send info back to the main thread
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_coherent.hardware.chameleon import Chameleon
from pymodaq_plugins_coherent.hardware.utils import get_resources


class DAQ_Move_Chameleon(DAQ_Move_base):
    """ Instrument plugin class for an actuator that controls the Chameleon series of laser sources using VISA
    communication
        * Tested with a Coherent Chameleon Ultra II
        * Tested with PyMoDAQ ver5.2.0a1
        * Tested on OS: Win11
        * NI-VISA library is required to communicate with the instrument
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.

    """
    is_multiaxes = False
    _axis_names: Union[List[str], Dict[str, int]] = ['Wavelength']
    _controller_units: Union[str, List[str]] = 'nm'
    _epsilon: Union[float, List[float]] = 0.1


    params = [{'title': 'Address:', 'name': 'address', 'type': 'list', 'limits': get_resources()},
                {'title': 'Laser Settings:', 'name': 'laser_settings', 'type': 'group', 'expanded': True,
               'children': [
                    {'title': 'Laser state:', 'name': 'laser_state', 'type': 'list', 'limits': ['ON', 'OFF'],
                        'readonly': False},
                    {'title': 'Shutter:', 'name': 'shutter_state', 'type': 'list', 'limits': ['OPEN', 'CLOSED'],
                        'readonly': False},
                    {'title': 'Wavelength (nm):', 'name': 'laser_wl', 'type': 'int',
                        'readonly': False},
                    {'title': 'Power (mW):', 'name': 'laser_power', 'type': 'int',
                        'readonly': True},
                    {'title': 'Alignment mode:', 'name': 'align', 'type': 'group', 'expanded': False,
                    'children': [
                        {'title': 'Toggle alignment mode:', 'name': 'align_mode', 'type': 'bool',
                            'readonly': False},
                        {'title': 'Alignment mode available power (mW):', 'name': 'align_power', 'type': 'int',
                            'readonly': True},
                        {'title': 'Alignment mode wavelength (nm):', 'name': 'align_wl', 'type': 'int',
                            'readonly': True}
                        ]},
                   {'title': 'Update settings:', 'name': 'update_settings', 'type': 'bool_push', 'value': False,
                    'label': 'Update!'},
                    ]},
                ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)


    def ini_attributes(self):
        self.controller: Chameleon = None


    def init_laser(self):
        address = self.settings.child('address').value()
        initialized = self.controller.open_communication(address)
        self.update_settings_hardware()

        return initialized

    def update_settings_hardware(self):
        self.settings.child('laser_settings', 'laser_state').setValue(self.controller.get_laser_state())
        self.settings.child('laser_settings', 'laser_wl').setLimits(self.controller.get_wavelength_range())
        self.settings.child('laser_settings', 'laser_wl').setValue(self.controller.get_wavelength())
        self.settings.child('laser_settings', 'shutter_state').setValue(self.controller.get_shutter())
        power = self.controller.get_laser_power()
        self.settings.child('laser_settings', 'laser_power').setValue(power)
        align = self.controller.get_align_mode()
        self.settings.child('laser_settings', 'align', 'align_mode').setValue(align[0])
        self.settings.child('laser_settings', 'align', 'align_power').setValue(align[1])
        self.settings.child('laser_settings', 'align', 'align_wl').setValue(align[2])


    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = self.controller.get_wavelength()
        pos = int(round(pos, 0))
        pos = self.get_position_with_scaling(pos)
        return pos


    def close(self):
        """Terminate the communication protocol"""
        if self.is_master:
            self.controller.close_communication()
            pass


    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """

        if param.name() == 'address':
            self.controller.close_communication()
            initialized = self.init_laser()
            if not initialized:
                self.emit_status(ThreadCommand('Update_Status', ['Connection failed']))

        elif param.name() == 'laser_state':
            laser_state = self.settings.child('laser_settings', 'laser_state').value()
            self.controller.set_laser_state(laser_state)

        elif param.name() == 'laser_wl':
            wl = self.settings.child('laser_settings', 'laser_wl').value()
            self.controller.set_wavelength(wl)
            self.move_done()

        elif param.name() == 'update_settings':
            self.update_settings_hardware()

        elif param.name() == 'align_mode':
            self.controller.set_align_mode(param.value())

        elif param.name() == 'shutter_state':
            shutter_state = self.settings.child('laser_settings', 'shutter_state').value()
            self.controller.set_shutter(shutter_state)

        else:
            pass


    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        if self.is_master:  # is needed when controller is master
            self.controller = Chameleon()
            initialized = self.init_laser()

        else:
            self.controller = controller
            initialized = True

        info = "Initialising laser communication channel"
        return info, initialized


    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """
        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one

        self.controller.set_wavelength(int(round(value, 0)))
        self.settings.child('laser_settings', 'laser_wl').setValue(self.controller.get_wavelength())
        self.emit_status(ThreadCommand('Update_Status', ['move_abs']))

        self.poll_moving()


    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value)
        self.target_value = self.current_position + value
        value = self.set_position_with_scaling(value)

        self.controller.set_wavelength_step(int(round(value, 0)))
        self.settings.child('laser_settings', 'laser_wl').setValue(self.controller.get_wavelength())
        self.emit_status(ThreadCommand('Update_Status', ['move_rel']))

        self.poll_moving()


    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.home_stepper()
        self.emit_status(ThreadCommand('Update_Status', ['home']))


    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        self.close()
        self.emit_status(ThreadCommand('Update_Status', ['stop_motion']))
        self.controller.open_communication(self.settings.child('address'))


if __name__ == '__main__':
    main(__file__)
