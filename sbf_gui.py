from __future__ import unicode_literals
from sbf_satellite import Satellite
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import dates as md
from numpy import arange, sin, pi
from PyQt5 import QtCore, QtWidgets
import sys
import os
import random
import matplotlib

matplotlib.use('Qt5Agg')


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent, satellite, band, width, height, dpi):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        self.compute_initial_figure(satellite, band)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self, satellite, band):
        pass


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)

    def compute_initial_figure(self, satellite, band):
        for sig_num in satellite.signals:
            for sat in satellite.signals[sig_num]:
                if satellite.sig_num_ref[sig_num]["band"] == band:
                    self.axes.plot_date(satellite.signals[sig_num][sat]["datetime"],
                                        satellite.signals[sig_num][sat]["snr"],
                                        '.',
                                        markersize=4.5,
                                        label="{} {}, {}".format(satellite.sig_num_ref[sig_num]["constellation"], sat, satellite.sig_num_ref[sig_num]["sig_type"]))
                for event in satellite.events["datetime"]:
                    self.axes.axvline(x=event, color='k', linewidth=0.5, alpha=0.3)

        self.axes.xaxis.set_major_formatter(md.DateFormatter("%H:%M:%S"))
        self.axes.set_ylabel("SNR [dB-Hz]")

        self.fig.autofmt_xdate()


    def update_figure(self, satellite, band):
        self.axes.cla()
        self.compute_initial_figure(satellite,band)
        self.draw()


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, sbf_file):
        self.satellite = Satellite(sbf_file)

        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("sbf viewer")

        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        self.file_menu = QtWidgets.QMenu(' &File', self)
        self.file_menu.addAction(' &Open file', self.load_file,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.file_menu.addAction(' &Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QtWidgets.QMenu(' &Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction(' &About', self.about)

        self.main_widget = QtWidgets.QWidget(self)

        l = QtWidgets.QVBoxLayout(self.main_widget)
        self.top_plot = MyDynamicMplCanvas(self.main_widget, self.satellite, 1, width=5, height=4, dpi=100)
        self.bot_plot = MyDynamicMplCanvas(self.main_widget, self.satellite, 2, width=5, height=4, dpi=100)
        l.addWidget(self.top_plot)
        l.addWidget(self.bot_plot)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, "About", "written by Marco Job, 2019")

    def load_file(self):
        filename = self.openFileNameDialog()
        self.satellite.load_file(filename)
        self.top_plot.update_figure(self.satellite,1)
        self.bot_plot.update_figure(self.satellite,2)

    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        return filename


def run_GUI(sbf_file=''):
    qApp = QtWidgets.QApplication(sys.argv)

    aw = ApplicationWindow(sbf_file)
    aw.setWindowTitle("sbf viewer")
    aw.show()
    sys.exit(qApp.exec_())
