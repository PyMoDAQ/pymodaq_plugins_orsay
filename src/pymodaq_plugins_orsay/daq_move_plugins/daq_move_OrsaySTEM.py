from qtpy.QtCore import QTimer
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType

from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq_plugins_orsay.hardware.STEM.orsayscan_position import OrsayScanPosition
from pymodaq.utils.data import DataActuator


class DAQ_Move_OrsaySTEM(DAQ_Move_base):
    """
        Wrapper object to access the Mock fonctionnalities, similar wrapper for all controllers.

        =============== ==============
        **Attributes**    **Type**
        *params*          dictionnary
        =============== ==============
    """
    _controller_units = 'pxls'

    is_multiaxes = True
    _axis_names = ['X', 'Y']
    _epsilon = 1
    data_actuator_type = DataActuatorType['DataActuator']


    params = [{'title': 'Pixels:', 'name': 'pixels_settings', 'type': 'group', 'children': [
        {'title': 'Nx:', 'name': 'Nx', 'type': 'int', 'min': 1, 'value': 256},
        {'title': 'Ny:', 'name': 'Ny', 'type': 'int', 'min': 1, 'value': 256}]}] \
             + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: OrsayScanPosition = None

    def ini_stage(self, controller=None):
        """

        """
        if self.settings['multiaxes', 'multi_status'] == "Slave":
            new_controller = None
        else:
            new_controller = OrsayScanPosition(1, 0)
        self.controller = self.ini_stage_init(old_controller=controller,
                                              new_controller=new_controller)

        if self.settings['multiaxes', 'multi_status'] == "Slave":
            sizex, sizey = self.controller.getImageSize()
            self.settings.child('pixels_settings', 'Nx').setOpts(readonly=True)
            self.settings.child('pixels_settings', 'Ny').setOpts(readonly=True)
            self.settings.child('pixels_settings', 'Nx').setValue(sizex)
            self.settings.child('pixels_settings', 'Ny').setValue(sizey)

        else:  # Master stage
            self.settings.child('pixels_settings', 'Nx').setOpts(readonly=False)
            self.settings.child('pixels_settings', 'Ny').setOpts(readonly=False)
            self.controller.setImageSize(self.settings['pixels_settings', 'Nx'],
                                         self.settings['pixels_settings', 'Ny'])
            sizex, sizey = self.controller.getImageSize()
            self.controller.setImageArea(sizex, sizey, 0, sizex, 0, sizey)

        self.settings.child('bounds', 'is_bounds').setValue(True)
        self.settings.child('bounds', 'min_bound').setValue(0)

        if self.axis_name == self.axis_names[0]:
            self.settings.child('bounds', 'max_bound').setValue(sizex - 1)
        else:
            self.settings.child('bounds', 'max_bound').setValue(sizey - 1)

        # set timer to update image size from controller
        self.timer: QTimer = self.startTimer(1000)  # Timer event fired every 1s

        info = "STEM coil"
        initialized = True
        return info, initialized

    def timerEvent(self, event):
        """ this is used to update image area if any call of the controller within multiple instance has been
        triggered and image size has been changed
        """
        try:
            sizex, sizey = self.controller.getImageSize()
            if sizex != self.settings['pixels_settings', 'Nx'] or sizey != self.settings['pixels_settings', 'Ny']:
                # try:
                #    self.settings.sigTreeStateChanged.disconnect(self.send_param_status)
                # except: pass
                self.controller.setImageSize(sizex, sizey)
                self.controller.setImageArea(sizex, sizey, 0, sizex, 0, sizey)
                self.settings.child('pixels_settings', 'Nx').setValue(sizex)
                self.settings.child('pixels_settings', 'Ny').setValue(sizey)

                if self.axis_name == self.axis_names[0]:
                    self.settings.child('bounds', 'max_bound').setValue(sizex - 1)
                else:
                    self.settings.child('bounds', 'max_bound').setValue(sizey - 1)

                # self.settings.sigTreeStateChanged.connect(self.send_param_status)
        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), "log"]))

    def commit_settings(self, param):
        """
            | Called after a param_tree_changed signal from DAQ_Move_main.

        """

        if param.name() == 'Nx' or param.name() == 'Ny':
            self.controller.setImageSize(self.settings['pixels_settings', 'Nx'], self.settings['pixels_settings', 'Ny'])
            sizex, sizey = self.controller.getImageSize()
            self.controller.setImageArea(sizex, sizey, 0, sizex, 0, sizey)
            if param.name() == 'Nx' and self.axis_name == self.axis_names[0]:
                self.settings.child('bounds', 'max_bound').setValue(param.value() - 1)
            elif param.name() == 'Ny' and self.axis_name == self.axis_names[1]:
                self.settings.child('bounds', 'max_bound').setValue(param.value() - 1)

    def close(self):
        """
        
        """
        try:
            self.timer.stop()
            self.killTimer(self.timer)
            if self.controller is not None:
                self.controller.close()
        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), "log"]))

    def stop_motion(self):
        """
          Call the specific move_done function (depending on the hardware).

          See Also
          --------
          move_done
        """
        self.move_done()

    def get_actuator_value(self):
        """
            Get the current position from the hardware with scaling conversion.

            Returns
            -------
            float
                The position obtained after scaling conversion.

            See Also
            --------
            DAQ_Move_base.get_position_with_scaling, daq_utils.ThreadCommand
        """
        pos = self.current_value
        self.emit_status(ThreadCommand('check_position', [pos]))
        return pos

    def move_abs(self, position: DataActuator):
        """

        """
        position = self.check_bound(position)
        self.target_value = position

        if self.axis_name == self.axis_names[0]:
            px = int(position.value())
            py = int(self.controller.y)
        else:
            px = int(self.controller.x)
            py = int(position.value())

        self.controller.OrsayScanSetProbeAt(1, px, py)

        self.current_value = position  # no check of the current position is possible...
        self.poll_moving()

    def move_rel(self, position):
        """
            Make the relative move from the given position after thread command signal was received in DAQ_Move_main.

            =============== ========= =======================
            **Parameters**  **Type**   **Description**

            *position*       float     The absolute position
            =============== ========= =======================

            See Also
            --------
            hardware.set_position_with_scaling, DAQ_Move_base.poll_moving

        """
        position = self.check_bound(self.current_value + position) - self.current_value
        self.target_value = position + self.current_value

        if self.axis_name == self.axis_names[0]:
            px = int(self.target_value.value())
            py = int(self.controller.y)
        else:
            px = int(self.controller.x)
            py = int(self.target_value.value())

        self.controller.OrsayScanSetProbeAt(1, px, py)

        self.current_value = self.target_value  # no check of the current position is possible...
        self.poll_moving()

    def move_home(self):
        """
          Send the update status thread command.
            See Also
            --------
            daq_utils.ThreadCommand
        """
        self.controller.OrsayScanSetProbeAt(1, 0, 0)


if __name__ == '__main__':
    main(__file__, init=False)
