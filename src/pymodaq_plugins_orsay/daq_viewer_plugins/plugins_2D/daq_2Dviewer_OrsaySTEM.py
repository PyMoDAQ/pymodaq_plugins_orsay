import ctypes


import numpy as np
from qtpy import QtWidgets
from qtpy.QtCore import QThread, Slot, QRectF


from pymodaq.control_modules.viewer_utility_classes import DAQ_Viewer_base, comon_parameters, main
from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq.utils.data import DataFromPlugins, Axis, DataToExport
from pymodaq.utils.parameter import utils as putils

from pymodaq_plugins_orsay.hardware.STEM import orsayscan
from pymodaq_plugins_orsay.hardware.STEM.orsayscan_position import OrsayScanPosition

try:
    from pymodaq_plugins_orsay.daq_viewer_plugins.plugins_2D.daq_2Dviewer_OrsayCamera import DAQ_2DViewer_OrsayCamera

    is_Orsay_camera = True
    params_camera = DAQ_2DViewer_OrsayCamera.params
except:
    is_Orsay_camera = False
    params_camera = []


#
# is_Orsay_camera=False
# params_camera=[]


class DAQ_2DViewer_OrsaySTEM(DAQ_Viewer_base):
    """

    """
    is_Orsay_camera = is_Orsay_camera

    hardware_averaging = False
    params = comon_parameters + [
        {'title': 'Do HyperSpectroscopy:', 'name': 'do_hyperspectroscopy', 'type': 'bool', 'value': False},
        {'title': 'HyperSpectroscopy:', 'name': 'hyperspectroscopy', 'visible': False, 'type': 'group', 'children':
            params_camera},
        {'title': 'ROIselection', 'name': 'roi_group', 'type': 'group', 'children': [
            {'title': 'Use ROI:', 'name': 'use_roi', 'type': 'bool', 'value': False},
            {'title': 'X0:', 'name': 'x0', 'type': 'int', 'min': 0},
            {'title': 'Y0:', 'name': 'y0', 'type': 'int', 'min': 0},
            {'title': 'Width:', 'name': 'width', 'type': 'int', 'min': 1},
            {'title': 'Height:', 'name': 'height', 'type': 'int', 'min': 1},
            ]},

        {'title': 'STEM Settings:', 'name': 'stem_settings', 'type': 'group', 'children': [
            {'title': 'Spot option:', 'name': 'spot_settings', 'type': 'group', 'children': [
                {'title': 'Go to spot after:', 'name': 'is_spot', 'type': 'bool', 'value': True},
                {'title': 'Pos x:', 'name': 'spot_x', 'type': 'int', 'min': 0, 'value': 0},
                # max is set using Nx value
                {'title': 'Pos y:', 'name': 'spot_y', 'type': 'int', 'min': 0, 'value': 0},
                # max is set using Ny value
            ]},

            {'title': 'Pixels:', 'name': 'pixels_settings', 'type': 'group', 'children': [
                {'title': 'Nx:', 'name': 'Nx', 'type': 'int', 'min': 1, 'value': 32},
                {'title': 'Ny:', 'name': 'Ny', 'type': 'int', 'min': 1, 'value': 32},
                {'title': 'x2:', 'name': 'mult2', 'type': 'bool_push', 'value': False},
                {'title': '/2:', 'name': 'div2', 'type': 'bool_push', 'value': False},
                # {'title': 'SubArea:', 'name': 'subarea', 'type': 'group', 'expanded': False, 'children':[
                #    {'title': 'Use subarea:', 'name': 'use_subarea', 'type': 'bool', 'value': False},
                #    {'title': 'Nx:', 'name': 'Nxsub', 'type': 'int', 'min': 0, 'value': 256},
                #    {'title': 'Ny:', 'name': 'Nysub', 'type': 'int', 'min': 0, 'value': 256},
                #    {'title': 'Start x:', 'name': 'startx', 'type': 'int', 'min': 0, 'value': 0},
                #    {'title': 'Start y:', 'name': 'starty', 'type': 'int', 'min': 0, 'value': 0},
                #    ]},
                {'title': 'Line averaging:', 'name': 'line_averaging', 'type': 'int', 'min': 1, 'value': 1,
                 'readonly': True},
                {'title': 'Scan mode:', 'name': 'scan_mode', 'type': 'list', 'value': 'Normal',
                 'limits': ['Normal', 'Random', 'Ebm']},
            ]},
            {'title': 'Mag. Rot.:', 'name': 'mag_rot', 'type': 'group', 'children': [
                {'title': 'Field:', 'name': 'field', 'type': 'slide', 'value': 1e-7, 'limits': [1e-7, 1],
                 'subtype': 'log'},
                {'title': 'Angle (°):', 'name': 'angle', 'type': 'slide', 'limits': [-180, 180], 'value': 0,
                 'subtype': 'linear'},
            ]},
            {'title': 'Inputs:', 'name': 'inputs', 'type': 'group', 'children': [
                {'title': 'Input 1:', 'name': 'input1', 'type': 'list', 'limits': []},
                {'title': 'Input 2:', 'name': 'input2', 'type': 'list', 'limits': []},
            ]},
            {'title': 'Times:', 'name': 'times', 'type': 'group', 'children': [
                {'title': 'Live Time (µs):', 'name': 'pixel_time_live', 'type': 'slide', 'value': 10, 'subtype': 'log',
                 'limits': [1, 1e6]},
                {'title': 'Capture Time (µs):', 'name': 'pixel_time_capture', 'type': 'slide', 'value': 10,
                 'subtype': 'log', 'limits': [1, 1e6]},
            ]},
        ]},
    ]

    def __init__(self, parent=None, params_state=None):

        super().__init__(parent, params_state)  # initialize base class with commom attributes and methods

        self.settings.child('do_hyperspectroscopy').show(self.is_Orsay_camera)
        self.settings.child('hyperspectroscopy').show(self.is_Orsay_camera)
        if self.is_Orsay_camera:
            self.camera = DAQ_2DViewer_OrsayCamera(parent=parent,
                                                   params_state=self.settings.child('hyperspectroscopy').saveState())
        else:
            self.camera = None
        self.settings.child('hyperspectroscopy').show(False)

        self.data_spectrum_spim_ready = False
        self.data_stem_ready = False
        self.data_spectrum_ready = False
        self.stem_scan_finished = False
        self.max_field = 1
        self.x_axis = None
        self.y_axis = None
        self.stem_scan = None
        self.spim_scan = None
        self.data_stem = None
        self.SIZEX, self.SIZEY = (None, None)
        self.SIZE_SPIMX, self.SIZE_SPIMY = (None, None)
        self.data_stem_pointer = None
        self.inputs = []

        self.data_stem = None  # buffer for HADF type of data typically shape (2*32*32) (2 for 2 inputs)

        self.data_stem_current: np.ndarray = None  # local buffer to be dislpayed from time to time.typically shape (2,32,32)
        self.data_stem_STEM_as_reference: DataFromPlugins = None  # used to keep data on screen while doing hyperspectroscopy
        self.data_stem_pointer = None  # pointer to the data array
        self.data_spectrum_spim: DataToExport = None  # data received from the camera object

    def ROISelect(self, pos_size: QRectF):
        self.settings.child('roi_group', 'x0').setValue(int(pos_size.x()))
        self.settings.child('roi_group', 'y0').setValue(int(pos_size.y()))
        self.settings.child('roi_group', 'width').setValue(int(pos_size.width()))
        self.settings.child('roi_group', 'height').setValue(int(pos_size.height()))

    def mult_image(self):
        Nx = self.settings['stem_settings', 'pixels_settings', 'Nx']
        Ny = self.settings['stem_settings', 'pixels_settings', 'Ny']
        self.settings.child('stem_settings', 'pixels_settings', 'Nx').setValue(2 * Nx)
        self.settings.child('stem_settings', 'pixels_settings', 'Ny').setValue(2 * Ny)
        self.init_data(2 * Nx, 2 * Ny)

    def divide_image(self):
        Nx = self.settings['stem_settings', 'pixels_settings', 'Nx']
        Ny = self.settings['stem_settings', 'pixels_settings', 'Ny']
        self.settings.child('stem_settings', 'pixels_settings', 'Nx').setValue(max([1, int(Nx / 2)]))
        self.settings.child('stem_settings', 'pixels_settings', 'Ny').setValue(max([1, int(Ny / 2)]))
        self.init_data(max([1, int(Nx / 2)]), max([1, int(Ny / 2)]))

    def commit_settings(self, param):
        """
            | Activate parameters changes on the hardware from parameter's name.
            |

            =============== ================================    =========================
            **Parameters**   **Type**                           **Description**
            *param*          instance of pyqtgraph parameter    The parameter to activate
            =============== ================================    =========================

            Three profile of parameter :
                * **bin_x** : set binning camera from bin_x parameter's value
                * **bin_y** : set binning camera from bin_y parameter's value
                * **set_point** : Set the camera's temperature from parameter's value.

        """
        try:
            if param.name() == 'mult2':
                if param.value():
                    self.mult_image()
                    param.setValue(False)
                Nx = self.settings['stem_settings', 'pixels_settings', 'Nx']
                Ny = self.settings['stem_settings', 'pixels_settings', 'Ny']
                self.settings.child('stem_settings', 'spot_settings', 'spot_x').setOpts(bounds=(0, Nx - 1))
                self.settings.child('stem_settings', 'spot_settings', 'spot_y').setOpts(bounds=(0, Ny - 1))

            if param.name() == 'div2':
                if param.value():
                    self.divide_image()
                    param.setValue(False)
                Nx = self.settings['stem_settings', 'pixels_settings', 'Nx']
                Ny = self.settings['stem_settings', 'pixels_settings', 'Ny']
                self.settings.child('stem_settings', 'spot_settings', 'spot_x').setOpts(bounds=(0, Nx - 1))
                self.settings.child('stem_settings', 'spot_settings', 'spot_y').setOpts(bounds=(0, Ny - 1))

            elif param.name() == 'input1' or param.name() == 'input2':
                input1 = self.settings['stem_settings', 'inputs', 'input1']
                input2 = self.settings['stem_settings', 'inputs', 'input2']
                self.stem_scan.SetInputs([self.inputs.index(input1), self.inputs.index(input2)])
                self.spim_scan.SetInputs([self.inputs.index(input1), self.inputs.index(input2)])

            elif param.name() == 'Nx' or param.name() == 'Ny':
                self.init_data(self.settings['stem_settings', 'pixels_settings', 'Nx'],
                               self.settings['stem_settings', 'pixels_settings', 'Ny'])
                Nx = self.settings['stem_settings', 'pixels_settings', 'Nx']
                Ny = self.settings['stem_settings', 'pixels_settings', 'Ny']
                self.settings.child('stem_settings', 'spot_settings', 'spot_x').setOpts(bounds=(0, Nx - 1))
                self.settings.child('stem_settings', 'spot_settings', 'spot_y').setOpts(bounds=(0, Ny - 1))

            elif param.name() in putils.iter_children(self.settings.child('stem_settings', 'times'), []):
                self.stem_scan.pixelTime = param.value() / 1e6

            elif param.name() == 'angle':
                self.stem_scan.setScanRotation(self.settings['stem_settings', 'mag_rot', 'angle'])
                self.get_set_field()
            elif param.name() == 'field':
                self.get_set_field()

            elif param.name() == 'do_hyperspectroscopy':
                if param.value():
                    data_stem_STEM_as_reference = self.data_stem.reshape((2, self.SIZEX, self.SIZEY)).astype(np.float64)
                    self.data_stem_STEM_as_reference = DataToExport('stem', data=[
                        DataFromPlugins(name=self.settings['stem_settings', 'inputs', 'input1'],
                                        data=[data_stem_STEM_as_reference[0]], dim='Data2D'),
                        DataFromPlugins(name=self.settings['stem_settings', 'inputs', 'input2'],
                                        data=[data_stem_STEM_as_reference[1]], dim='Data2D'), ])

                # init the viewers
                self.emit_data_init()

                if self.is_Orsay_camera:
                    self.settings.child('hyperspectroscopy').show(param.value())
                    if param.value():
                        self.settings.child('roi_group').show(True)
                        self.settings.child('roi_group', 'use_roi').setValue(True)
                        self.settings.child('roi_group', 'use_roi').setOpts(readonly=True)

                        QtWidgets.QApplication.processEvents()
                        self.init_data()

                        # init the viewers type
                        self.dte_signal_temp(DataToExport('stem', data=
                            [DataFromPlugins(name='SPIM ', data=[np.zeros((1024, 10, 10))], dim='DataND',
                                             nav_indexes=(1, 2)),
                             # data from SPIM camera
                             DataFromPlugins(name='Spectrum', data=[np.zeros((1024,))], dim='Data1D')]))
                    else:
                        self.settings.child('roi_group', 'use_roi').setOpts(readonly=False)
                        if self.camera is None:
                            # remove viewers related to camera
                            self.dte_signal_temp(DataToExport('stem', data=[]))

            elif param.name() in putils.iter_children(self.settings.child('hyperspectroscopy'),
                                                      []):  # parameters related to camera
                if self.camera is not None:
                    self.camera.commit_settings(param)


        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))

    def update_live(self, live=False):
        if live:
            self.stem_scan.registerUnlockerA(self.fnunlockA_live)
            self.stem_scan.pixelTime = self.settings['stem_settings', 'times', 'pixel_time_live'] / 1e6
        else:
            self.stem_scan.registerUnlockerA(self.fnunlockA)
            self.stem_scan.pixelTime = self.settings['stem_settings', 'times', 'pixel_time_capture'] / 1e6

    def dataLocker(self, gene, datatype, sx, sy, sz):
        """
        Callback pour obtenir le tableau ou stcoker les nouvelles données.
        Dans un programme complet il est conseillé de verrouiler ce tableau (par exemple ne pas changer sa dimension, son type, le détuire etc...)
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
        sx[0] = self.settings['stem_settings', 'pixels_settings', 'Nx']
        sy[0] = self.settings['stem_settings', 'pixels_settings', 'Ny']
        sz[0] = 2  # 2 inputs
        datatype[0] = 2
        return self.data_stem_pointer.value

    def spim_dataLocker(self, gene, datatype, sx, sy, sz):
        """
        Callback pour obtenir le tableau ou stcoker les nouvelles données.
        Dans un programme complet il est conseillé de verrouiler ce tableau (par exemple ne pas changer sa dimension, son type, le détuire etc...)
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
        sx[0] = self.settings['stem_settings', 'pixels_settings', 'Nx']
        sy[0] = self.settings['stem_settings', 'pixels_settings', 'Ny']
        sz[0] = 2  # 2 inputs
        datatype[0] = 2
        return self.data_stem_pointer.value

    def dataUnlocker(self, gene, newdata):
        """
        Le tableau peut être utilisé
        """
        # if newdata:
        #    self.emit_data()
        pass

    def dataUnlockerA(self, gene, newdata, imagenb, rect):
        """
        Le tableau peut être utilisé
        """
        Nscan = imagenb
        ##self.emit_data_live()
        if newdata and Nscan != self.curr_scan:
            print('Nscan:{:}'.format(Nscan))
            self.curr_scan = Nscan
            self.stem_scan_finished = True
            self.stem_done()
        else:
            print('emit temp')
            self.stem_done()

    def spim_dataUnlockerA(self, gene, newdata, imagenb, rect):
        """
        Le tableau peut être utilisé
        """
        Nscan = imagenb
        ##self.emit_data_live()
        if newdata and Nscan != self.curr_scan:
            print('Nscan:{:}'.format(Nscan))
            self.curr_scan = Nscan
            self.stem_scan_finished = True
            self.stem_done()
        else:
            print('emit temp')
            self.stem_done()

    def dataUnlockerA_live(self, gene, newdata, imagenb, rect):
        """
        Le tableau peut être utilisé
        """
        Nscan = imagenb

        self.emit_data_live()

    def spim_done(self, data_spectrum_spim: DataToExport):
        self.data_spectrum_spim_ready = True
        self.data_spectrum_spim = data_spectrum_spim
        # self.emit_data()

    def spectrum_done(self, data_spectrum_spim: DataToExport):
        self.data_spectrum_ready = True
        self.data_spectrum_spim = data_spectrum_spim
        # self.emit_data()

    def stem_done(self):
        self.data_stem_ready = True
        self.data_stem_current = self.data_stem.reshape((2, self.SIZEX,
                                                         self.SIZEY)).astype(float)
        self.emit_data()

    def emit_data(self):
        # data_stem = self.data_stem.reshape((2, self.SIZEX,
        #                                     self.SIZEY)).astype(float)

        if not self.settings['do_hyperspectroscopy']:
            data_stem = [
                DataFromPlugins(name=self.settings['stem_settings', 'inputs', 'input1'],
                                data=[self.data_stem_current[0]], dim='Data2D'),
                DataFromPlugins(name=self.settings['stem_settings', 'inputs', 'input2'],
                                data=[self.data_stem_current[1]], dim='Data2D'), ]
            if self.data_stem_ready:
                if self.stem_scan_finished:
                    self.data_grabed_signal.emit(data_stem)
                    self.stem_scan.stopImaging(True)
                else:
                    self.data_grabed_signal_temp.emit(data_stem)
        else:
            data_stem = [
                DataFromPlugins(name='SPIM ' + self.settings['stem_settings', 'inputs', 'input1'],
                                data=[self.data_stem_current[0]], dim='Data2D'),
                DataFromPlugins(name='SPIM ' + self.settings['stem_settings', 'inputs', 'input2'],
                                data=[self.data_stem_current[1]], dim='Data2D'), ]
            if self.data_spectrum_spim_ready and self.stem_scan_finished:  # all data have been taken
                self.spim_scan.stopImaging(True)
                self.data_grabed_signal.emit(self.data_stem_STEM_as_reference + data_stem + self.data_spectrum_spim)

            else:
                self.data_grabed_signal_temp.emit(
                    self.data_stem_STEM_as_reference + data_stem + self.data_spectrum_spim)

    def emit_data_init(self):
        data_stem = self.data_stem.reshape((2, self.SIZEX,
                                            self.SIZEY)).astype(float)
        if not self.settings['do_hyperspectroscopy']:
            data_stem = DataToExport('stem', data=[
                DataFromPlugins(name=self.settings['stem_settings', 'inputs', 'input1'],
                                data=[data_stem[0]],
                                dim='Data2D'),
                DataFromPlugins(name=self.settings['stem_settings', 'inputs', 'input2'],
                                data=[data_stem[1]],
                                dim='Data2D'), ])

            self.dte_signal_temp.emit(data_stem)
        else:
            dte = DataToExport('stem', data=[
                DataFromPlugins(name='SPIM ' + self.settings['stem_settings', 'inputs', 'input1'],
                                data=[data_stem[0]],
                                dim='Data2D'),
                DataFromPlugins(name='SPIM ' + self.settings['stem_settings', 'inputs', 'input2'],
                                data=[data_stem[1]],
                                dim='Data2D'), ])
            if self.data_stem_STEM_as_reference is None:
                dte.append([
                    DataFromPlugins(name=self.settings['stem_settings', 'inputs', 'input1'],
                                    data=[data_stem[0]],
                                    dim='Data2D'),
                    DataFromPlugins(name=self.settings['stem_settings', 'inputs', 'input2'],
                                    data=[data_stem[1]],
                                    dim='Data2D'), ])
            else:
                dte.append(self.data_stem_STEM_as_reference)
            dte.append(self.data_spectrum_spim)
            self.dte_signal_temp.emit(dte)

    def emit_data_live(self):
        """
        temporary datas emitter when acquisition is running
        """
        data_stem = self.data_stem.reshape((2, self.settings['stem_settings', 'pixels_settings', 'Ny'],
                                            self.settings['stem_settings', 'pixels_settings',
                                            'Nx'])).astype(float)
        # print('livedata')
        self.data_grabed_signal_temp.emit([DataFromPlugins(
            name=self.settings['stem_settings', 'inputs', 'input1'], data=[data_stem[0]], dim='Data2D'),
            DataFromPlugins(
                name=self.settings['stem_settings', 'inputs', 'input2'],
                data=[data_stem[1]], dim='Data2D')]
        )

    def list_inputs(self, scan):
        nbinputs = scan.getInputsCount()
        self.inputs = []
        k = 0
        while (k < nbinputs):
            unipolar, offset, name, ind = scan.getInputProperties(k)
            self.inputs.append(name)
            k += 1
        self.settings.child('stem_settings', 'inputs', 'input1').setOpts(limits=self.inputs)
        self.settings.child('stem_settings', 'inputs', 'input2').setOpts(limits=self.inputs)
        if 'BF' in self.inputs:
            self.settings.child('stem_settings', 'inputs', 'input1').setValue('BF')

        if 'HADF' in self.inputs:
            self.settings.child('stem_settings', 'inputs', 'input1').setValue('HADF')

    def init_data(self, Nx=None, Ny=None):
        # %%%%%% Initialize data: self.data_stem for the memory to store new data and self.data_stem_average to store the average data
        if not self.settings['do_hyperspectroscopy']:
            self.SIZEX = Nx
            self.SIZEY = Ny

            self.stem_scan.setImageSize(Nx, Ny)
            self.stem_scan.setImageArea(Nx, Ny, 0, Nx, 0, Ny)
        else:
            Nx = self.settings['hyperspectroscopy', 'camera_mode_settings', 'spim_x']
            Ny = self.settings['hyperspectroscopy', 'camera_mode_settings', 'spim_y']
            startx = self.settings['roi_group', 'x0']
            starty = self.settings['roi_group', 'y0']
            endx = startx + self.settings['roi_group', 'width']
            endy = starty + self.settings['roi_group', 'height']

            self.SIZEX = Nx
            self.SIZEY = Ny
            self.spim_scan.setImageArea(Nx, Ny, startx, endx, starty, endy)

        self.data_spectrum_spim = [DataFromPlugins(name='SPIM ',
                                                   data=[np.zeros((
                                                       self.settings['hyperspectroscopy', 'image_size', 'Nx'],
                                                       self.settings['hyperspectroscopy', 'camera_mode_settings', 'spim_y'],
                                                       self.settings['hyperspectroscopy', 'camera_mode_settings', 'spim_x']))],
                                                   dim='DataND', nav_indexes=(1, 2)),
                                   DataFromPlugins(name='Spectrum', data=[np.zeros((
                                       self.settings['hyperspectroscopy', 'image_size', 'Nx'],))],
                                                   dim='Data1D')]

        self.data_stem = np.zeros((2 * Nx * Ny), dtype=np.int16)
        self.data_stem_current = np.zeros((2, Nx, Ny), dtype=np.int16)
        self.data_stem_pointer = self.data_stem.ctypes.data_as(ctypes.c_void_p)

    def ini_detector(self, controller=None):
        """
            Initialisation procedure of the detector in four steps :
                * Register callback to get data from camera
                * Get image size and current binning
                * Set and Get temperature from camera
                * Init axes from image

            ============== ================================================ ==========================================================================================
            **Parameters**  **Type**                                         **Description**

            *controller*    instance of the specific controller object       If defined this hardware will use it and will not initialize its own controller instance
            ============== ================================================ ==========================================================================================

            Returns
            -------
            Easydict
                dictionnary containing keys:
                 * *info* : string displaying various info
                 * *controller*: instance of the controller object in order to control other axes without the need to init the same controller twice
                 * *stage*: instance of the stage (axis or whatever) object
                 * *initialized*: boolean indicating if initialization has been done corretly

            See Also
            --------
             DAQ_utils.ThreadCommand
            
        """

        # init camera for SPIM if present
        if self.is_Orsay_camera:
            self.camera.parent_parameters_path = ['hyperspectroscopy']
            info, initialized = self.camera.ini_detector()
            if initialized:
                self.camera.settings.child('camera_mode_settings', 'camera_mode').setValue('SPIM')
                self.camera.update_camera_mode('SPIM')
                self.camera.settings.child('camera_mode_settings').show(True)
                self.camera.settings.child('binning_settings').show(False)
                self.camera.data_grabed_signal_temp.connect(self.spectrum_done)
                self.camera.data_grabed_signal.connect(self.spim_done)
            else:
                self.is_Orsay_camera = False

        # init STEM if present
        if self.settings['controller_status'] == "Slave":
            if controller is None:
                raise Exception('no controller has been defined externally while this detector is a slave one')
            else:
                self.stem_scan = controller
        else:
            self.stem_scan = OrsayScanPosition(1, 0)  # to be used to scan STEM only

        self.spim_scan = OrsayScanPosition(2,
                                           self.stem_scan.orsayscan)  # to be used when performing hyperspectroscopy SPIM

        # get/set inputs
        self.list_inputs(self.stem_scan)

        input1 = self.settings['stem_settings', 'inputs', 'input1']
        input2 = self.settings['stem_settings', 'inputs', 'input2']
        self.stem_scan.SetInputs([self.inputs.index(input1), self.inputs.index(input2)])
        self.spim_scan.SetInputs([self.inputs.index(input1), self.inputs.index(input2)])

        # %%%%%%% Register callback to get data from camera
        self.fnlock = orsayscan.LOCKERFUNC(self.dataLocker)
        self.stem_scan.registerLocker(self.fnlock)

        self.SPIM_fnlock = orsayscan.LOCKERFUNC(self.spim_dataLocker)
        self.spim_scan.registerLocker(self.SPIM_fnlock)

        self.fnunlockA = orsayscan.UNLOCKERFUNCA(self.dataUnlockerA)
        self.fnunlockA_live = orsayscan.UNLOCKERFUNCA(self.dataUnlockerA_live)
        self.SPIM_funlockA = orsayscan.UNLOCKERFUNCA(self.spim_dataUnlockerA)

        self.stem_scan.registerUnlockerA(self.fnunlockA)
        self.spim_scan.registerUnlockerA(self.SPIM_funlockA)

        # %%%%%%%%%% set initial scan image size
        Nx = self.settings['stem_settings', 'pixels_settings', 'Nx']
        Ny = self.settings['stem_settings', 'pixels_settings', 'Ny']
        self.stem_scan.setImageSize(Nx, Ny)
        self.init_data(Nx, Ny)

        # init the viewers
        self.emit_data_init()

        # %%%%%%%%%%% set pixel time
        self.stem_scan.pixelTime = self.settings['stem_settings', 'times', 'pixel_time_live'] / 1e6
        self.stem_scan.setScanRotation(self.settings['stem_settings', 'mag_rot', 'angle'])
        self.get_set_field()

        # %%%%%%% init axes from image
        self.x_axis = self.get_xaxis()
        self.y_axis = self.get_yaxis()

        initialized = True
        self.controller = self.stem_scan
        return 'init', initialized

    def get_set_field(self):
        self.max_field = self.stem_scan.GetMaxFieldSize()
        field = self.settings['stem_settings', 'mag_rot', 'field']

        self.settings.child('stem_settings', 'mag_rot', 'field').setLimits(
            [self.settings.child('stem_settings', 'mag_rot', 'field').opts['limits'][0], self.max_field])
        self.settings.child('stem_settings', 'mag_rot', 'field').setValue(field)
        self.stem_scan.SetFieldSize(field)

    def close(self):
        """

        """
        if self.spim_scan is not None:
            self.spim_scan.close()
        if self.stem_scan is not None:
            self.stem_scan.close()

    def get_xaxis(self):
        """
            Obtain the horizontal axis of the image.

            Returns
            -------
            1D numpy array
                Contains a vector of integer corresponding to the horizontal camera pixels.
        """
        if self.stem_scan is not None:
            Nx, Ny = self.stem_scan.getImageSize()
            self.settings.child('stem_settings', 'pixels_settings', 'Nx').setValue(Nx)
            self.settings.child('stem_settings', 'pixels_settings', 'Ny').setValue(Ny)
            self.x_axis = Axis('x_axis', data=np.linspace(0, Nx - 1, Nx, dtype=int), index=1)
        else:
            raise (Exception('Camera not defined'))
        return self.x_axis

    def get_yaxis(self):
        """
            Obtain the vertical axis of the image.

            Returns
            -------
            1D numpy array
                Contains a vector of integer corresponding to the vertical camera pixels.
        """
        if self.stem_scan is not None:
            Nx, Ny = self.stem_scan.getImageSize()
            self.settings.child('stem_settings', 'pixels_settings', 'Nx').setValue(Nx)
            self.settings.child('stem_settings', 'pixels_settings', 'Ny').setValue(Ny)
            self.y_axis = Axis('y_axis', data=np.linspace(0, Ny - 1, Ny, dtype=int), index=0)
        else:
            raise (Exception('Camera not defined'))
        return self.y_axis

    def grab_data(self, Naverage=1, **kwargs):
        """
            Start new acquisition in two steps :
                * Initialize data: self.data_stem for the memory to store new data and self.data_stem_average to store the average data
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

            self.data_spectrum_spim_ready = False
            self.data_stem_ready = False
            self.data_spectrum_ready = False
            self.stem_scan_finished = False

            self.curr_scan = 0

            # %%%%% Start acquisition
            time_sleep = self.stem_scan.GetImageTime()

            if 'live' in kwargs:
                self.update_live(kwargs['live'])

            mode = self.settings.child('stem_settings', 'pixels_settings', 'scan_mode').opts['limits'].index(
                self.settings['stem_settings', 'pixels_settings', 'scan_mode'])

            if self.settings['do_hyperspectroscopy']:
                self.init_data()
                self.spim_scan.setScanClock(0)
                self.spim_scan.pixelTime = self.camera.settings['exposure']
                self.spim_scan.startSpim(mode, self.settings['stem_settings', 'pixels_settings',
                'line_averaging'], Nspectra=1, save2D=False)
                self.camera.grab(Naverage, **kwargs)
            else:
                if self.settings['roi_group', 'use_roi']:
                    startx = self.settings['roi_group', 'x0']
                    starty = self.settings['roi_group', 'y0']
                    width = self.settings['roi_group', 'width']
                    height = self.settings['roi_group', 'height']
                    endx = startx + width
                    endy = starty + height
                    self.stem_scan.setImageArea(width, height, startx, endx, starty, endy)
                else:
                    width = self.settings['stem_settings', 'pixels_settings', 'Nx']
                    height = self.settings['stem_settings', 'pixels_settings', 'Ny']
                    self.stem_scan.setImageArea(width, height, 0, width, 0, height)
                self.stem_scan.startImaging(mode, self.settings['stem_settings', 'pixels_settings',
                'line_averaging'])

            # self.stem_scan.stopImaging(False) #will stop the acquisition when the image is done



        except Exception as e:
            self.emit_status(ThreadCommand('Update_Status', [getLineInfo() + str(e), "log"]))

    def stop(self):
        """
            stop the stem's actions.
        """
        try:
            self.stem_scan.stopImaging(True)
            self.spim_scan.s
            if self.settings['do_hyperspectroscopy']:
                self.camera.stop()
            if self.settings['stem_settings', 'spot_settings', 'is_spot']:
                self.stem_scan.OrsayScanSetProbeAt(1, self.settings['stem_settings', 'spot_settings',
                'spot_x'],
                                                   self.settings['stem_settings', 'spot_settings',
                                                   'spot_y'])
        except:
            pass
        return ""


if __name__ == '__main__':
    main(__file__, init=False)
