### PH 322 - OpenBCI & BrainFlow EEG Data Analysis Exploration Project: Livestream Segment - Dan Jang
## Credits to BrainFlow API Docs for Python File I/O & Band Power Examples

## Libraries
#import argparse
import logging
import pyqtgraph as pg
import pyqtgraph.exporters
import numpy as np
import matplotlib.pyplot as plt
from brainflow.data_filter import DataFilter, FilterTypes, AggOperations, WindowOperations, DetrendOperations
from brainflow.board_shim import BoardShim, BrainFlowInputParams, LogLevels, BoardIds
from pyqtgraph.Qt import QtGui, QtCore
from IPython.display import display, Image

csv_file = "./data/BrainFlow-RAW_2023-03-02_19-06-28_0.csv"
#data = np.loadtxt(csv_file, delimiter='\t', skiprows=1)

## Credits to the following post for help on snapshotting a PyQtGraph frame (https://stackoverflow.com/questions/65023730/is-it-possible-to-use-pyqtgraph-functions-to-plot-inline-on-jupyter-notebook)
def show_image(data):
    image = pg.image(data)
    image_file = "ph322-eegproject-danj-livestream-snapshot.png"
    exporter = pg.exporters.ImageExporter(image.imageItem).export(image_file)
    image.close()
    display(Image(filename=image_file))

class Graph:
    def __init__(self, board_shim):
        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 50
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate

        self.app = QtGui.QApplication([])
        self.win = pg.GraphicsWindow(title='BrainFlow Plot', size=(800, 600))

        self._init_timeseries()

        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(self.update_speed_ms)
        QtGui.QApplication.instance().exec_()

    def _init_timeseries(self):
        self.plots = list()
        self.curves = list()
        for i in range(len(self.exg_channels)):
            p = self.win.addPlot(row=i, col=0)
            p.showAxis('left', False)
            p.setMenuEnabled('left', False)
            p.showAxis('bottom', False)
            p.setMenuEnabled('bottom', False)
            if i == 0:
                p.setTitle('TimeSeries Plot')
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)

    def update(self):
        data = self.board_shim.get_current_board_data(self.num_points)
        for count, channel in enumerate(self.exg_channels):
            # plot timeseries
            DataFilter.detrend(data[channel], DetrendOperations.CONSTANT.value)
            DataFilter.perform_bandpass(data[channel], self.sampling_rate, 3.0, 45.0, 2,
                                        FilterTypes.BUTTERWORTH_ZERO_PHASE, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 48.0, 52.0, 2,
                                        FilterTypes.BUTTERWORTH_ZERO_PHASE, 0)
            DataFilter.perform_bandstop(data[channel], self.sampling_rate, 58.0, 62.0, 2,
                                        FilterTypes.BUTTERWORTH_ZERO_PHASE, 0)
            self.curves[count].setData(data[channel].tolist())

        self.app.processEvents()


def main():
    BoardShim.enable_dev_board_logger()
    logging.basicConfig(level=logging.DEBUG)

    # parser = argparse.ArgumentParser()
    # # use docs to check which parameters are required for specific board, e.g. for Cyton - set serial port
    # parser.add_argument('--timeout', type=int, help='timeout for device discovery or connection', required=False,
    #                     default=0)
    # parser.add_argument('--ip-port', type=int, help='ip port', required=False, default=0)
    # parser.add_argument('--ip-protocol', type=int, help='ip protocol, check IpProtocolType enum', required=False,
    #                     default=0)
    # parser.add_argument('--ip-address', type=str, help='ip address', required=False, default='')
    # parser.add_argument('--serial-port', type=str, help='serial port', required=False, default='')
    # parser.add_argument('--mac-address', type=str, help='mac address', required=False, default='')
    # parser.add_argument('--other-info', type=str, help='other info', required=False, default='')
    # parser.add_argument('--streamer-params', type=str, help='streamer params', required=False, default='')
    # parser.add_argument('--serial-number', type=str, help='serial number', required=False, default='')
    # parser.add_argument('--board-id', type=int, help='board id, check docs to get a list of supported boards',
    #                     required=False, default=BoardIds.SYNTHETIC_BOARD)
    # parser.add_argument('--file', type=str, help='file', required=False, default='')
    # parser.add_argument('--master-board', type=int, help='master board id for streaming and playback boards',
    #                     required=False, default=BoardIds.NO_BOARD)
    # args = parser.parse_args()

    params = BrainFlowInputParams()
    params.ip_port = 0
    params.serial_port = ''
    params.mac_address = ''
    params.other_info = ''
    params.serial_number = ''
    params.ip_address = ''
    params.ip_protocol = 0
    params.timeout = 0
    params.file = csv_file
    params.master_board = BoardIds.NO_BOARD
    
    defaultboard = BoardIds.SYNTHETIC_BOARD
    streamerparams = ''

    board_shim = BoardShim(defaultboard, params)
    try:
        board_shim.prepare_session()
        board_shim.start_stream(450000, streamerparams)
        Graph(board_shim)
    except BaseException:
        logging.warning('Exception', exc_info=True)
    finally:
        logging.info('End')
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()


if __name__ == '__main__':
    main()