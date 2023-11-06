from collections import OrderedDict
import importlib
import sys

import ctypes
from easydict import EasyDict as edict
import numpy as np
from qtpy import QtWidgets

from pymodaq_plugins_orsay.hardware.STEM import orsaycamera
from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, main
from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq.utils.enums import BaseEnum, enum_checker
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.control_modules.viewer_utility_classes import comon_parameters

from pymodaq_plugins_orsay import config as orsay_config


class Orsay_Camera_manufacturer(BaseEnum):
    """ Enum class of manufacturer provided by OrsayCamera dll
    """
    Ropers = 1
    Andor = 2


Ropers_models = [
    'PIXIS: 100F',
    'PIXIS: 100R',
    'PIXIS: 100C',
    'PIXIS: 100BR',
    'PIXIS: 100B',
    'PIXIS-XO: 100B',
    'PIXIS-XO: 100BR',
    'PIXIS: 1024F',
    'PIXIS: 1024B',
    'PIXIS: 1024BUV',
    'PIXIS: 1024BR',
    'PIXIS-XO: 1024B',
    'PIXIS-XO: 1024BR',
    'PIXIS-XO: 1024F',
    'PIXIS-XF: 1024F',
    'PIXIS-XF: 1024B',
    'PIXIS: 2048F',
    'PIXIS: 2048B',
    'PIXIS-XO: 2048B',
    'PIXIS-XF: 2048B',
    'PIXIS-XF: 2048F',
    'PIXIS: 256F',
    'PIXIS: 256E',
    'PIXIS: 256B',
    'PIXIS: 256BR',
    'PIXIS-XB: 256BR',
    'PIXIS: 2KF',
    'PIXIS: 2KB',
    'PIXIS-XO: 2KB',
    'PIXIS: 2KBUV',
    'PIXIS: 400F',
    'PIXIS: 400R',
    'PIXIS: 400B',
    'PIXIS: 400BR',
    'PIXIS-XO: 400B',
    'PIXIS: 512F',
    'PIXIS: 512B',
    'PIXIS: 512BUV',
    'PIXIS-XF: 512B',
    'PIXIS-XF: 512F',
    'PIXIS-XO: 512F',
    'PIXIS-XO: 512B',
    'PIXIS: 1300F',
    'PIXIS: 1300B',
    'PIXIS: 100B eXcelon',
    'PIXIS: 100BR eXcelon',
    'PIXIS: 400B eXcelon',
    'PIXIS: 400BR eXcelon',
    'PIXIS: 512B eXcelon',
    'PIXIS: 1024B eXcelon',
    'PIXIS: 1024BR eXcelon',
    'PIXIS: 1300B eXcelon',
    'PIXIS: 1300BR eXcelon',
    'PIXIS: 2048B eXcelon',
    'PIXIS: 2KB eXcelon',
    'PIXIS-XO: 1300B',
    'PIXIS-XF: 1300B',
    'PIXIS: 2048BR',
    'PIXIS-XB: 100B',
    'PIXIS-XB: 100BR',
    'PIXIS-XB: 400BR',
    'PIXIS-XB: 1024BR',
    'PIXIS-XB: 1300R',
    'PIXIS: 1300BR',
    'PIXIS: 2048BR eXcelon',
    'PIXIS: 1300F-2',
    'Quad-RO: 4096',
    'Quad-RO: 4320',
    'Quad-RO: 4096-2',
    'ProEM: 512B',
    'ProEM: 1024B',
    'ProEM: 512B eXcelon',
    'ProEM: 512BK',
    'ProEM: 512BK eXcelon',
    'ProEM: 1024B eXcelon',
    'ProEM: 1600xx(2)B eXcelon',
    'ProEM: 1600xx(4)B eXcelon',
    'ProEM: 1600xx(2)B',
    'ProEM: 1600xx(4)B',
    'PI-MAX3: 1024i',
    'PI-MAX3: 1024x256',
    'PyLoN: 100B',
    'PyLoN: 400B',
    'PyLoN: 1300B',
    'PyLoN: 100F',
    'PyLoN: 400F',
    'PyLoN: 1300F',
    'PyLoN: 100BR',
    'PyLoN: 400BR',
    'PyLoN: 256F',
    'PyLoN: 256B',
    'PyLoN: 256E',
    'PyLoN: 256BR',
    'PyLoN: 2KF',
    'PyLoN: 2KB',
    'PyLoN: 2048F',
    'PyLoN: 2048BR',
    'PyLoN: 1024B',
    'PyLoN: 100B eXcelon',
    'PyLoN: 100BR eXcelon',
    'PyLoN: 400B eXcelon',
    'PyLoN: 400BR eXcelon',
    'PyLoN: 1024B eXcelon',
    'PyLoN: 1300B eXcelon',
    'PyLoN: 2KB eXcelon',
    'PyLoN: 1300BR',
    'PyLoN: 1300BR eXcelon',
    'PyLoN: 2048B',
    'PyLoN: 2048B eXcelon',
    'PyLoN: 2048BR eXcelon',
    'PyLoN: 2KBUV',
    'PyLoN: 1300R',
    'PIoNIR: 640',
    'ProEM+: 512B',
    'ProEM+: 1024B',
    'ProEM+: 512B eXcelon',
    'ProEM+: 512BK',
    'ProEM+: 512BK eXcelon',
    'ProEM+: 1024B eXcelon',
    'ProEM+: 1600xx(2)B eXcelon',
    'ProEM+: 1600xx(4)B eXcelon',
    'ProEM+: 1600xx(2)B',
    'ProEM+: 1600xx(4)B',
    'PI-MAX4: 1024i',
    'PI-MAX4: 1024x256',
    'PI-MAX4: 1024i-RF',
    'PI-MAX4: 1024x256-RF',
    'PI-MAX4: 512EM',
    'PI-MAX4: 512B/EM',
    'PI-MAX4: 1024f',
    'PI-MAX4: 1024f-RF',
    'PI-MAX4: 1024B/EM',
    'PI-MAX4: 1024EM',
    'PI-MAX4: 2048f',
    'PI-MAX4: 2048B',
    'PI-MAX4: 2048f-RF',
    'PI-MAX4: 2048B-RF',
    'NIRvana: 640',
    'PyLoN-IR: 1024-2.2',
    'PyLoN-IR: 1024-1.7',
    'NIRvana-LN: 640',
    'ProEM-HS: 512B',
    'ProEM-HS: 512B eXcelon',
    'ProEM-HS: 1024B',
    'ProEM-HS: 1024B eXcelon',
    'ProEM-HS: 512BK',
    'ProEM-HS: 512BK eXcelon',
    'ProEM-HS: 1KB-10',
    'ProEM-HS: 1KB eXcelon-10',
    'ProEM-HS: 1024B-2',
    'ProEM-HS: 1024B eXcelon-2',
    'ProEM-HS: 1024B-3',
    'ProEM-HS: 1024B eXcelon-3',
    'NIRvana ST: 640',
    'PI-MTE: 1024F',
    'PI-MTE: 1024B',
    'PI-MTE: 1024BUV',
    'PI-MTE: 1024BR',
    'PI-MTE: 1024FT',
    'PI-MTE: 1024B/FT',
    'PI-MTE: 2KB',
    'PI-MTE: 2KBUV',
    'PI-MTE: 1300B',
    'PI-MTE: 1300R',
    'PI-MTE: 1300BR',
    'PI-MTE: 2048B',
    'PI-MTE: 2048BR',
    'BLAZE: 100B',
    'BLAZE: 400B',
    'BLAZE: 100HR',
    'BLAZE: 400HR',
    'BLAZE: 100BR',
    'BLAZE: 400BR',
    'BLAZE: 100BR LD',
    'BLAZE: 400BR LD',
    'BLAZE: 100B eXcelon',
    'BLAZE: 400B eXcelon',
    'BLAZE: 100BR eXcelon',
    'BLAZE: 400BR eXcelon',
    'BLAZE: 100HR eXcelon',
    'BLAZE: 400HR eXcelon',
    'BLAZE: 100BR LD eXcelon',
    'BLAZE: 400BR LD eXcelon',
    'FERGIE: 256B',
    'FERGIE: 256B eXcelon',
    'FERGIE: 256B/FT',
    'FERGIE: 256B/FT eXcelon',
    'FERGIE: 256BR',
    'FERGIE: 256BR eXcelon',
    'FERGIE: 256F/FT',
    'FERGIE: 256BR/FT',
    'FERGIE: 256BR/FT eXcelon',
    'SOPHIA: 2048B',
    'SOPHIA: 2048B eXcelon',
    'SOPHIA-XO: 2048B',
    'SOPHIA-XF: 2048B',
    'SOPHIA-XB: 2048B',
    'SOPHIA: 2048-13.5',
    'SOPHIA: 2048B-13.5',
    'SOPHIA: 2048BR-13.5',
    'SOPHIA: 2048B eXcelon-13.5',
    'SOPHIA: 2048BR eXcelon-13.5',
    'SOPHIA-XO: 2048B-13.5',
    'SOPHIA-XO: 2048BR-13.5',
    'SOPHIA: 2048B-HDR',
    'SOPHIA: 2048BR-HDR',
    'SOPHIA: 2048B-HDR eXcelon',
    'SOPHIA: 2048BR-HDR eXcelon',
    'SOPHIA-XO: 2048B-HDR',
    'SOPHIA-XO: 2048BR-HDR',
    'SOPHIA-XF: 2048B-HDR',
    'SOPHIA-XF: 2048BR-HDR',
    'SOPHIA-XB: 2048B-HDR',
    'SOPHIA-XB: 2048BR-HDR',
    'SOPHIA: 4096B',
    'SOPHIA: 4096B eXcelon',
    'SOPHIA-XO: 4096B',
    'SOPHIA-XF: 4096B',
    'SOPHIA-XB: 4096B',
    'SOPHIA: 4096B-HDR',
    'SOPHIA: 4096BR-HDR',
    'SOPHIA: 4096B-HDR eXcelon',
    'SOPHIA: 4096BR-HDR eXcelon',
    'SOPHIA-XO: 4096B-HDR',
    'SOPHIA-XO: 4096BR-HDR',
    'SOPHIA-XF: 4096B-HDR',
    'SOPHIA-XF: 4096BR-HDR',
    'SOPHIA-XB: 4096B-HDR',
    'SOPHIA-XB: 4096BR-HDR',
    'KURO: 1200B',
    'KURO: 1608B',
    'KURO: 2048B']

Andor_models = []


class Orsay_Camera_mode(BaseEnum):
    """ Enum class of acquisition mode
    """
    Camera = 1
    SPIM = 2


class DAQ_2DViewer_OrsayCamera(DAQ_Viewer_base):
    """ Instrument class to control Camera using the Orsay libraries: compatible with Roper/Princeton

    """
    params = comon_parameters + [
        {'title': 'Simulated camera:', 'name': 'simulated', 'type': 'bool', 'value': False, 'default': False},
        {'title': 'Manufacturer:', 'name': 'manufacturer', 'type': 'list', 'limits': Orsay_Camera_manufacturer.names(),
         'value': 'Ropers'},
        {'title': 'Model:', 'name': 'model', 'type': 'list', 'limits': Ropers_models,
         'value': orsay_config('camera', 'default')},
        {'title': 'SN:', 'name': 'serialnumber', 'type': 'str', 'value': ''},
        {'title': 'Mode Settings:', 'name': 'camera_mode_settings', 'type': 'group', 'expanded': True, 'children': [
            {'title': 'Mode:', 'name': 'camera_mode', 'type': 'list', 'limits': Orsay_Camera_mode.names()},
            {'title': 'Nx:', 'name': 'spim_x', 'type': 'int', 'value': 10, 'min': 1},
            {'title': 'Ny:', 'name': 'spim_y', 'type': 'int', 'value': 10, 'min': 1},
        ]},
        {'title': 'Exposure (s):', 'name': 'exposure', 'type': 'float', 'value': 1, 'default': 0.1},
        {'title': 'Image size:', 'name': 'image_size', 'type': 'group', 'children': [
            {'title': 'Nx:', 'name': 'Nx', 'type': 'int', 'value': 256, 'default': 256, 'readonly': True},
            {'title': 'Ny:', 'name': 'Ny', 'type': 'int', 'value': 1024, 'default': 1024, 'readonly': True},
        ]},
        {'title': 'Temperature Settings:', 'name': 'temperature_settings', 'type': 'group', 'children': [
            {'title': 'Set Point:', 'name': 'set_point', 'type': 'float', 'value': -70, 'default': -70},
            {'title': 'Current value:', 'name': 'current_value', 'type': 'float', 'value': 0, 'default': 0,
             'readonly': True},
            {'title': 'Locked:', 'name': 'locked', 'type': 'led', 'value': False, 'default': False, 'readonly': True},
        ]},
        {'title': 'Binning Settings:', 'name': 'binning_settings', 'type': 'group', 'children': [
            {'name': 'bin_x', 'type': 'int', 'value': 1, 'default': 1, 'min': 1},
            {'name': 'bin_y', 'type': 'int', 'value': 1, 'default': 1, 'min': 1}
        ]}
    ]
    hardware_averaging = False

    def ini_attributes(self):

        self.controller: orsaycamera.orsayCamera = None
        self.x_axis: Axis = None
        self.y_axis: Axis = None

        self.data = None
        self.CCDSIZEX, self.CCDSIZEY = (None, None)
        self.data_pointer = None
        self.camera_done = False
        self.spectrum_done = False
        self.spim_done = False
        self.data_shape = 'Data2D'

    def commit_settings(self, param):
        """
        """
        try:
            if param.name() == 'bin_x':
                self.controller.setBinning(param.value(), self.settings['binning_settings', 'bin_y'])
                Nx, Ny = self.controller.getImageSize()
                self.settings.child('image_size', 'Nx').setValue(Nx)
                self.settings.child('image_size', 'Ny').setValue(Ny)
            elif param.name() == 'bin_y':
                self.controller.setBinning(self.settings['binning_settings', 'bin_x'], param.value())
                Nx, Ny = self.controller.getImageSize()
                self.settings.child('image_size', 'Nx').setValue(Nx)
                self.settings.child('image_size', 'Ny').setValue(Ny)
            elif param.name() == 'exposure':
                self.controller.setExposureTime(self.settings['exposure'])
            elif param.name() == 'set_point':
                self.controller.setTemperature(param.value())
            elif param.name() == 'manufacturer':
                mod = importlib.import_module(__file__)
                models = getattr(mod, f'{param.value()}_models')
                if models == []:
                    models = ['']
                self.settings.child('model').setOpts(limits=models)
                if 'PIXIS: 256E' in models:
                    self.settings.child('model').setValue('PIXIS: 256E')

            elif param.name() == 'camera_mode':
                self.update_camera_mode(param.value())

            if param.name() in ['bin_x', 'bin_y']:
                self.get_xaxis()
                self.get_yaxis()

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))

    def dataLocker(self, camera, datatype, sx, sy, sz):
        """
            | CallBack to obtain the tab and store the newest data.
            | In a full program context, it is recommanded to lock the tab (to keep size values, type and integrity for example).
            | It permit to use the same code in case of callback.
            |

            The data type is :
                * **1**  : byte
                * **2**  : short
                * **3**  : long
                * **5**  : unsigned byte
                * **6**  : unsgned short
                * **7**  : unsigned long
                * **11** : float 32 bit
                * **12** : double 64 bit

            =============== =============== =============================================================================
            **Parameters**    **Type**        **Description**
            *camera*                          in case of differents cameras, index pointing the camera sending the datas
            *datatype*        int             defined above
            *sx*              int array       X image size
            *sy*              int array       Y image size
            *sz*              int array       Z image size
            =============== =============== =============================================================================

            Returns
            -------
            ???



       """
        sx[0] = self.settings['image_size', 'Nx']
        sy[0] = self.settings['image_size', 'Ny']
        sz[0] = 1
        datatype[0] = 11
        return self.data_pointer.value

    def dataUnlocker(self, camera, newdata):
        """
            Transmission of new acquired data

            =============== =============== ===============================
            **Parameters**   **Type**        **Description**

            *camera*         c_void pointer  pointer to camera object

            *newdata*        bool            True if new data is available
            =============== =============== ===============================

            See Also
            --------
            emit_data

        """
        # print(self.data[0:10])
        if newdata:
            self.camera_done = True
            self.emit_data()

    def spimdataLocker(self, camera, datatype, sx, sy, sz):
        """
        Même chose que pour le mode focus, mais le tableau est 3D, voire plus
        """
        SPIMX = self.settings['camera_mode_settings', 'spim_x']
        SPIMY = self.settings['camera_mode_settings', 'spim_y']
        sizex = self.settings['image_size', 'Nx']
        sx[0] = SPIMX
        sy[0] = SPIMY
        sz[0] = sizex
        datatype[0] = 11
        return self.pointeurspim.value

    def spimdataUnlocker(self, camera, newdata, running):
        if running:
            # imprime un point par spectre
            # print(".", end = "")
            pass
        else:
            self.spim_done = True
            self.emit_data()

    def spectrumdataLocker(self, camera, datatype, sx):
        """
        Callback pour obtenir le tableau ou stcoker les nouvelles données.
        Dans un programme complet il est conseillé de verrouiler ce tableau (par exemple ne pas changer sa dimension, son type, le détuire etc...)
        camera dans le cas de plusieurs camera, c'est un index qui dit quelle camera envoie des data.
        permet d'utiliser le même code pour les callback.
        Le type de données est
            1   byte
            2   short
            3   long
            5   unsigned byte
            6   unsgned short
            7   unsigned long
            11  float 32 bit
            12  double 64 bit
        """
        sizex = self.settings['image_size', 'Nx']
        sx[0] = sizex
        datatype[0] = 11
        return self.pointeurspectrum.value

    def spectrumdataUnlocker(self, camera, newdata):
        """
        Le tableau peut être utilisé
        on imprime les premières valeurs
        """
        self.spectrum_done = True
        self.emit_data()

    def emit_data(self):
        """ Method used to emit data obtained by dataUnlocker callback.
        """
        try:
            self.ind_grabbed += 1
            # print(self.ind_grabbed)
            if self.settings['camera_mode_settings', 'camera_mode'] == "Camera":
                if self.camera_done:
                    if self.settings['image_size', 'Nx'] == 1:
                        self.y_axis.index = 0
                        axis = [self.y_axis]
                    elif self.settings['image_size', 'Ny'] == 1:
                        self.x_axis.index = 0
                        axis = [self.x_axis]
                    else:
                        self.y_axis.index = 0
                        self.x_axis.index = 1
                        axis = [self.x_axis, self.y_axis]
                    self.dte_signal.emit(
                        DataToExport('OrsayCamera', data=
                        [DataFromPlugins(name=f"Camera {self.settings['model']}",
                                         data=[np.atleast_1d(np.squeeze(self.data.reshape(
                                             (self.settings['image_size', 'Ny'],
                                              self.settings['image_size', 'Nx']))))],
                                         axes=axis)]))

            else:  # spim mode
                # print("spimmode")
                if self.spectrum_done:
                    # print("spectrum done")
                    data = DataToExport('OrsaySPIM', data=
                            [DataFromPlugins(name='SPIM ',
                                             data=[np.atleast_1d(np.squeeze(self.spimdata.reshape(
                                                 (self.settings['image_size', 'Nx'],
                                                  self.settings['camera_mode_settings', 'spim_y'],
                                                  self.settings['camera_mode_settings', 'spim_x']))))],
                                             dim='DataND'),
                             DataFromPlugins(name='Spectrum',
                                             data=[self.spectrumdata],
                                             dim='Data1D')
                             ])
                    if not self.spim_done:
                        self.spectrum_done = False
                        self.dte_signal_temp.emit(data)
                    elif self.spim_done:
                        # print('spimdone')
                        self.dte_signal.emit(data)
                    self.spectrum_done = False
                    self.spim_done = False

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))

    def ini_detector(self, controller=None):
        """ Initialisation procedure of the detector in four steps :
                * Register callback to get data from camera
                * Get image size and current binning
                * Set and Get temperature from camera
                * Init axis from image

        Returns
        -------
        tuple
            The initialized status.
        """
        manufacturer = Orsay_Camera_manufacturer[self.settings['manufacturer']].value
        new_controller = None
        if self.settings['controller_status'] == "Master":
            if self.settings['simulated']:
                new_controller = orsaycamera.orsayCamera(manufacturer, self.settings['model'],
                                                         '1234', True)  # index represents manufacturer
            else:
                new_controller = orsaycamera.orsayCamera(manufacturer, self.settings['model'],
                                                          self.settings['serialnumber'],
                                                          False)  # index represents manufacturer

        self.controller = self.ini_detector_init(controller, new_controller=new_controller)

        # %%%%%%% Register callback to get data from camera
        # mode camera only
        self.fnlock = orsaycamera.DATALOCKFUNC(self.dataLocker)
        self.controller.registerDataLocker(self.fnlock)

        self.fnunlock = orsaycamera.DATAUNLOCKFUNC(self.dataUnlocker)
        self.controller.registerDataUnlocker(self.fnunlock)

        # mode SPIM+spectrum
        self.fnspimlock = orsaycamera.SPIMLOCKFUNC(self.spimdataLocker)
        self.controller.registerSpimDataLocker(self.fnspimlock)
        self.fnspimunlock = orsaycamera.SPIMUNLOCKFUNC(self.spimdataUnlocker)
        self.controller.registerSpimDataUnlocker(self.fnspimunlock)

        self.fnspectrumlock = orsaycamera.SPECTLOCKFUNC(self.spectrumdataLocker)
        self.controller.registerSpectrumDataLocker(self.fnspectrumlock)
        self.fnspectrumunlock = orsaycamera.SPECTUNLOCKFUNC(self.spectrumdataUnlocker)
        self.controller.registerSpectrumDataUnlocker(self.fnspectrumunlock)

        self.controller.setCurrentPort(0)

        # %%%%%% Get image size and current binning
        self.CCDSIZEX, self.CCDSIZEY = self.controller.getCCDSize()
        bin_x, bin_y = self.controller.getBinning()
        Nx, Ny = self.controller.getImageSize()

        self.settings.child('image_size', 'Nx').setValue(Nx)
        self.settings.child('image_size', 'Ny').setValue(Ny)
        self.settings.child('binning_settings', 'bin_x').setValue(bin_x)
        self.settings.child('binning_settings', 'bin_y').setValue(bin_y)

        # %%%%%%% Set and Get temperature from camera
        self.controller.setTemperature(self.settings['temperature_settings', 'set_point'])
        temp, locked_status = self.controller.getTemperature()
        self.settings.child('temperature_settings', 'current_value').setValue(temp)
        self.settings.child('temperature_settings', 'locked').setValue(locked_status)
        # set timer to update temperature info from controller
        self.timer = self.startTimer(2000)  # Timer event fired every 1s

        info = 'Orsay Camera initialized'

        # %%%%%%% init axes from image
        self.x_axis = self.get_xaxis()
        self.y_axis = self.get_yaxis()

        initialized = True

        return info, initialized

    def timerEvent(self, event):
        """
            | Called by set timers (only one for this self).
            | Used here to update temperature status0.

            =============== ==================== ==============================================
            **Parameters**    **Type**             **Description**

            *event*           QTimerEvent object   Containing id from timer issuing this event
            =============== ==================== ==============================================
        """
        temp, locked_status = self.controller.getTemperature()
        self.settings.child('temperature_settings', 'current_value').setValue(temp)
        self.settings.child('temperature_settings', 'locked').setValue(locked_status)

    def close(self):
        """

        """
        if self.controller is not None:
            self.controller.close()

    def get_xaxis(self) -> Axis:
        """ Obtain the horizontal axis of the image.
        """
        if self.controller is not None:
            Nx, Ny = self.controller.getImageSize()
            self.settings.child('image_size', 'Nx').setValue(Nx)
            self.settings.child('image_size', 'Ny').setValue(Ny)
            self.x_axis = Axis('Xaxis', units='pxl',
                               data=np.linspace(0, self.settings['image_size', 'Nx'] - 1,
                                                self.settings['image_size', 'Nx'], dtype=int),
                               index=1)
        else:
            raise (Exception('Camera not defined'))
        return self.x_axis

    def get_yaxis(self) -> Axis:
        """ Obtain the vertical axis of the image.
        """
        if self.controller is not None:
            Nx, Ny = self.controller.getImageSize()
            self.settings.child('image_size', 'Nx').setValue(Nx)
            self.settings.child('image_size', 'Ny').setValue(Ny)
            self.y_axis = Axis('Yaxis', units='pxl',
                               data=np.linspace(0, self.settings['image_size', 'Ny'] - 1,
                                                self.settings['image_size', 'Ny'], dtype=int),
                               index=0)
        else:
            raise (Exception('Camera not defined'))
        return self.y_axis

    def update_camera_mode(self, mode='Camera'):
        sizex = self.settings['image_size', 'Nx']
        sizey = self.settings['image_size', 'Ny']
        image_size = sizex * sizey

        if image_size == 1:
            self.data_shape = 'Data0D'
        elif sizex == 1 or sizey == 1:
            self.data_shape = 'Data1D'
        else:
            self.data_shape = 'Data2D'

        if mode == "Camera":
            # %%%%%% Initialize data: self.data for the memory to store new data and self.data_average to store the average data

            self.data = np.zeros((image_size,), dtype=np.float32)
            self.data_pointer = self.data.ctypes.data_as(ctypes.c_void_p)

        elif mode == "SPIM":
            Ny = self.settings['image_size', 'Ny']
            self.settings.child('binning_settings', 'bin_y').setValue(
                Ny * self.settings['binning_settings', 'bin_y'])
            self.commit_settings(self.settings.child('binning_settings', 'bin_y'))
            QtWidgets.QApplication.processEvents()
            # %%%%%% Initialize data: self.data for the memory to store new data and self.data_average to store the average data
            SPIMX = self.settings['camera_mode_settings', 'spim_x']
            SPIMY = self.settings['camera_mode_settings', 'spim_y']
            spimsize = sizex * SPIMY * SPIMX

            self.spimdata = np.zeros((spimsize,), dtype=np.float32)
            self.pointeurspim = self.spimdata.ctypes.data_as(ctypes.c_void_p)

            self.spectrumdata = np.zeros((sizex,), dtype=np.float32)
            self.pointeurspectrum = self.spectrumdata.ctypes.data_as(ctypes.c_void_p)

            # init the viewers
            data = DataToExport('OrsaySPIM', data=
            [DataFromPlugins(name='SPIM ',
                             data=[np.atleast_1d(self.spimdata.reshape(
                                 (self.settings['image_size', 'Nx'],
                                  self.settings['camera_mode_settings', 'spim_y'],
                                  self.settings['camera_mode_settings', 'spim_x'])))],
                             dim='DataND'),
             DataFromPlugins(name='Spectrum',
                             data=[self.spectrumdata],
                             dim='Data1D')
             ])
            self.dte_signal_temp.emit(data)

    def grab_data(self, Naverage=1, **kwargs):
        """
            Start new acquisition in two steps :
                * Initialize data: self.data for the memory to store new data and self.data_average to store the average data
                * Start acquisition with the given exposure in ms, in "1d" or "2d" mode

            =============== =========== =============================
            **Parameters**   **Type**    **Description**
            Naverage         int         Number of images to average
            =============== =========== =============================

            See Also
            --------
            DAQ_utils.ThreadCommand
        """
        try:
            self.camera_done = False
            self.spectrum_done = False
            self.spim_done = False

            self.ind_grabbed = 0  # to keep track of the current image in the average
            self.Naverage = Naverage  # no need averaging is done software wise by DAQ_Viewer_Detector

            self.update_camera_mode(self.settings['camera_mode_settings', 'camera_mode'])

            if self.settings['camera_mode_settings', 'camera_mode'] == 'Camera':
                self.controller.setAccumulationNumber(
                    Naverage)  # stop the acquisition after Navergae image if third argument of startfocus is 1
                self.controller.startFocus(self.settings['exposure'], "2d", 1)

            else:  # spim mode
                SPIMX = self.settings['camera_mode_settings', 'spim_x']
                SPIMY = self.settings['camera_mode_settings', 'spim_y']
                self.controller.startSpim(SPIMX * SPIMY, 1, self.settings['exposure'], False)
                self.controller.resumeSpim(4)  # stop eof

            # %%%%% Start acquisition with the given exposure in ms, in "1d" or "2d" mode

        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), "log"]))

    def stop(self):
        """
            stop the camera's actions.
        """
        try:
            if self.settings['camera_mode_settings', 'camera_mode'] == 'Camera':
                self.controller.stopFocus()
            else:  # spim mode
                self.controller.stopSpim(True)
        except:
            pass
        return ""


if __name__ == '__main__':
    main(__file__, init=False)
