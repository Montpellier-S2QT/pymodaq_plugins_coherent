
from typing import Union, List, Dict
from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun,
                                                          main, DataActuatorType, DataActuator)

from pymodaq_utils.utils import ThreadCommand  # object used to send info back to the main thread
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_coherent.hardware.chameleon import Chameleon
from pymodaq_plugins_coherent.hardware.utils import get_resources


class DAQ_Move_Chameleon(DAQ_Move_base):
    """ Instrument plugin class for an actuator.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    TODO Complete the docstring of your plugin with:
        * The set of controllers and actuators that should be compatible with this instrument plugin.
        * With which instrument and controller it has been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    # TODO add your particular attributes here if any

    """
    is_multiaxes = False  # TODO for your plugin set to True if this plugin is controlled for a multiaxis controller
    _axis_names: Union[List[str], Dict[str, int]] = ['Wavelength']  # TODO for your plugin: complete the list
    _controller_units: Union[str, List[str]] = 'nm'  # TODO for your plugin: put the correct unit here, it could be
    # TODO  a single str (the same one is applied to all axes) or a list of str (as much as the number of axes)
    _epsilon: Union[float, List[float]] = 0.1  # TODO replace this by a value that is correct depending on your controller
    # TODO it could be a single float of a list of float (as much as the number of axes)


    params = [{'title': 'Address:', 'name': 'address', 'type': 'list', 'limits': get_resources()},
                {'title': 'Laser Settings:', 'name': 'laser_settings', 'type': 'group', 'expanded': True,
               'children': [
                    {'title': 'Laser state', 'name': 'laser_state', 'type': 'list', 'limits': ['ON', 'OFF'],
                        'readonly': False},
                    {'title': 'Wavelength (nm):', 'name': 'laser_wl', 'type': 'float',
                    'readonly': False},
                    {'title': 'Power (mW):', 'name': 'laser_power', 'type': 'float',
                        'readonly': True},
                   {'title': 'Power reading:', 'name': 'update_power', 'type': 'bool_push', 'value': False,
                    'label': 'Update!'},
                    {'title': 'Shutter:', 'name': 'shutter_state', 'type': 'list', 'limits': ['OPEN', 'CLOSED'],
                        'readonly': False},
                    ]},
                ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)
    # _epsilon is the initial default value for the epsilon parameter allowing pymodaq to know if the controller reached
    # the target value. It is the developer responsibility to put here a meaningful value


    def ini_attributes(self):
        self.controller: Chameleon = None
        pass


    def init_laser(self):

        address = self.settings.child(('address')).value()
        initialized = self.controller.open_communication(address)

        self.settings.child(('laser_settings', 'laser_state')).setValue(self.controller.get_laser_state())
        self.settings.child(('laser_settings', 'laser_wl')).setLimits(self.controller.get_wavelength_range())
        self.settings.child(('laser_settings', 'laser_wl')).setValue(self.controller.get_wavelength())
        self.settings.child(('laser_settings', 'laser_power')).setValue(self.controller.get_laser_power())
        self.settings.child(('laser_settings', 'shutter_state')).setValue(self.controller.get_shutter())

        return initialized


    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """

        pos = self.controller.get_wavelength()
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
            initialized = self.init_laser()
            if not initialized:
                self.emit_status(ThreadCommand('Update_Status', ['Connection failed']))

        elif param.name() == 'laser_state':
            laser_state = self.settings.child(('laser_settings', 'laser_state')).value()
            self.controller.set_laser_state(laser_state)

        elif param.name() == 'laser_wl':
            wl = self.settings.child(('laser_settings', 'laser_wl')).value()
            self.controller.set_wavelength(wl)

        elif param.name() == 'update_power':
            self.settings.child(('laser_settings', 'laser_power')).setValue(self.controller.get_laser_power())

        elif param.name() == 'shutter_state':
            shutter_state = self.settings.child(('laser_settings', 'shutter_state')).value()
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

        self.controller.set_wavelength(value)
        self.settings.child('laser_settings', 'laser_wl').setValue(self.controller.get_wavelength())
        self.emit_status(ThreadCommand('Update_Status', ['Wavelength set (absolute)']))
        self.emit_status(ThreadCommand('move_done'))


    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value)
        self.target_value = value
        value = self.set_position_relative_with_scaling(value)

        ## TODO for your custom plugin
        self.controller.set_wavelength(value)
        self.settings.child('laser_settings', 'laser_wl').setValue(self.controller.get_wavelength())
        self.emit_status(ThreadCommand('Update_Status', ['Wavelength set (relative)']))
        self.emit_status(ThreadCommand('move_done'))


    def move_home(self):
        """Call the reference method of the controller"""

        ## TODO for your custom plugin
        raise NotImplementedError  # when writing your own plugin remove this line
        self.controller.your_method_to_get_to_a_known_reference()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))


    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""

        ## TODO for your custom plugin
        raise NotImplementedError  # when writing your own plugin remove this line
        self.controller.your_method_to_stop_positioning()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))


if __name__ == '__main__':
    main(__file__)
