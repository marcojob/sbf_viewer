from __future__ import unicode_literals
from .satellite import Satellite
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import dates as md
from PyQt5 import QtCore, QtWidgets
from numpy import mean, nan
import sys
import os
import random
import matplotlib
import datetime
import calendar

matplotlib.use('Qt5Agg')

DEFAULT_VALUE = 'N/A'

class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent, sat, band, width, height, dpi):
        self.datetimeformat = "%Y-%m-%d %H:%M:%S.%f"
        self.epoch = datetime.datetime.strptime("1980-01-06 00:00:00.000", self.datetimeformat)

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        self.compute_initial_figure(sat, band)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self, sat, band):
        pass


class DynamicMplCanvas(MplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MplCanvas.__init__(self, *args, **kwargs)

    def compute_initial_figure(self, sat, band):
        self.axes.xaxis_date()
        dict_df = sat.dict_df[band]
        for key in dict_df:
            self.axes.plot_date(self.get_time(1, dict_df[key].index),
                                dict_df[key],
                                '.',
                                markersize=4.5)

        self.axes.xaxis.set_major_formatter(md.DateFormatter("%H:%M:%S"))
        self.axes.set_ylabel("SNR [dB-Hz]")
        self.fig.autofmt_xdate()

        self.show_events(sat.events)
        self.show_mean(sat, band)

    def show_events(self, events):
        for trig in events['tow']:
            self.axes.axvline(x=self.get_time_s(1, trig), color='k', linewidth=0.5, alpha=0.3)

    def show_mean(self, sat, band):
        axes_xlim_r = self.axes.get_xlim()
        len_val, val = sat.get_top_mean(band)
        max_val = sat.get_max_mean(band)
        self.axes.axhline(y=val, color='k', linewidth=1.0, linestyle='dashed', alpha=0.7)
        self.axes.axhline(y=max_val, color='k', linewidth=1.0, linestyle='dashed', alpha=0.7)
        if not max_val == DEFAULT_VALUE:
            self.axes.set_title("Max: {:.2f}, mean of top {} sats: {:.2f}".format(
                max_val, len_val, val), fontsize=10)

    def update_figure(self, sat, band):
        dict_df = sat.dict_df[band]
        self.axes.cla()
        self.axes.xaxis_date()
        for sat in dict_df:
            self.axes.plot_date(self.get_time(1, dict_df[sat].index),
                                dict_df[sat],
                                '.',
                                markersize=4.5)
        self.axes.xaxis.set_major_formatter(md.DateFormatter("%H:%M:%S"))
        self.axes.set_ylabel("CNR [dB-Hz]")
        self.fig.autofmt_xdate()

    def get_time(self, wnc, tow_list):
        xc_dt = []
        for tow in tow_list:
            elapsed = datetime.timedelta(days=(wnc*7), seconds=(tow / 1000), milliseconds=(tow - (tow / 1000)*1000))
            xc_str = datetime.datetime.strftime(self.epoch + elapsed, self.datetimeformat)
            xc_dt.append(datetime.datetime.strptime(xc_str, "%Y-%m-%d %H:%M:%S.%f"))
        return xc_dt

    def get_time_s(self, wnc, tow):
        elapsed = datetime.timedelta(days=(wnc*7), seconds=(tow / 1000), milliseconds=(tow - (tow / 1000)*1000))
        xc_str = datetime.datetime.strftime(self.epoch + elapsed, self.datetimeformat)
        xc_dt = datetime.datetime.strptime(xc_str, "%Y-%m-%d %H:%M:%S.%f")
        return xc_dt


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, satellite):
        self.satellite = satellite
        self.enable_events = True
        self.enable_mean = True

        QtWidgets.QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle('sbf viewer')
        self.resize(1500, 1000)

        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        self.file_menu = QtWidgets.QMenu(' &File', self)
        self.file_menu.addAction(' &Open file', self.load_file,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_O)
        self.file_menu.addAction(' &Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.settings_menu = QtWidgets.QMenu(' &Settings', self)
        self.settings_menu.addAction(' &Toggle events', self.toggle_events,
                                     QtCore.Qt.CTRL + QtCore.Qt.Key_T)
        self.settings_menu.addAction(' &Toggle mean', self.toggle_mean,
                                     QtCore.Qt.CTRL + QtCore.Qt.Key_M)
        self.menuBar().addMenu(self.settings_menu)

        self.help_menu = QtWidgets.QMenu(' &Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction(' &About', self.about)

        self.main_widget = QtWidgets.QWidget(self)

        l = QtWidgets.QVBoxLayout(self.main_widget)
        self.top_plot = DynamicMplCanvas(self.main_widget, self.satellite, '1', width=5, height=4, dpi=100)
        self.bot_plot = DynamicMplCanvas(self.main_widget, self.satellite, '2', width=5, height=4, dpi=100)
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
        self.dict_df = self.satellite.dict_df
        self.events = self.satellite.events
        print("Loaded new file {}".format(filename))

        self.enable_events = True
        self.enable_mean = True

        self.update_view()

    def toggle_events(self):
        if self.enable_events:
            self.enable_events = False
        else:
            self.enable_events = True
        self.update_view()

    def toggle_mean(self):
        if self.enable_mean:
            self.enable_mean = False
        else:
            self.enable_mean = True
        self.update_view()

    def update_view(self):
        self.top_plot.update_figure(self.satellite, '1')
        self.bot_plot.update_figure(self.satellite, '2')

        if self.enable_mean:
            self.top_plot.show_mean(self.satellite, '1')
            self.bot_plot.show_mean(self.satellite, '2')

        if self.enable_events:
            self.top_plot.show_events(self.satellite.events)
            self.bot_plot.show_events(self.satellite.events)

        self.top_plot.draw()
        self.bot_plot.draw()

    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "QFileDialog.getOpenFileName()", "", "All Files (*);;Python Files (*.py)", options=options)
        return filename


def run_GUI(satellite):
    qApp = QtWidgets.QApplication(sys.argv)
    aw = ApplicationWindow(satellite)
    aw.setWindowTitle("sbf viewer")
    aw.show()
    sys.exit(qApp.exec_())
