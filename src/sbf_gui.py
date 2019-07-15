from __future__ import unicode_literals
from .sbf_satellite import Satellite
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


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent, dict_df, events, width, height, dpi):
        self.datetimeformat = "%Y-%m-%d %H:%M:%S.%f"
        self.epoch = datetime.datetime.strptime("1980-01-06 00:00:00.000", self.datetimeformat)

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)

        self.compute_initial_figure(dict_df, events)

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self, dict_df, events):
        pass


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)

    def compute_initial_figure(self, dict_df, events):
        self.axes.xaxis_date()
        for sat in dict_df:
            self.axes.plot_date(self.get_time(1,dict_df[sat].index), 
                                dict_df[sat],
                                '.',
                                markersize=4.5)

        self.axes.xaxis.set_major_formatter(md.DateFormatter("%H:%M:%S"))
        self.axes.set_ylabel("SNR [dB-Hz]")
        self.fig.autofmt_xdate()

        self.show_events(events)
        self.show_mean(dict_df, events)


    def show_events(self, events):
        for trig in events['tow']:
            self.axes.axvline(x=self.get_time_s(1,trig), color='k', linewidth=0.5, alpha=0.3)


    def show_mean(self, dict_df, events):
        mean_avg = list()
        mean_val = 0
        mean_len = 0
        if events['tow'] == list():
            for sat in dict_df:
                val_list = dict_df[sat].mean().tolist()
                mean_avg.append(val_list[0])
        else:
            for sat in dict_df:
                mean_avg.append(self.get_event_mean(dict_df[sat], events))

        mean_avg = list(filter(lambda a: a != 0, mean_avg))
        mean_avg.sort(reverse=True)

        if len(mean_avg) < 7:
            mean_val = mean(mean_avg)
            mean_len = len(mean_avg)
        else:
            mean_val = mean(mean_avg[:7])
            mean_len = 7
        axes_xlim_r = self.axes.get_xlim()
        self.axes.axhline(y=mean_val, color='k', linewidth=1.0, linestyle='dashed', alpha=0.7)
        self.axes.axhline(y=max(mean_avg), color='k', linewidth=1.0, linestyle='dashed', alpha=0.7)
        self.axes.set_title("Max: {:.2f}, mean of top {} sats): {:.2f}".format(max(mean_avg), mean_len, mean_val), fontsize=10)


    def update_figure(self, dict_df):
        self.axes.cla()
        self.axes.xaxis_date()
        for sat in dict_df:
            self.axes.plot_date(self.get_time(1,dict_df[sat].index), 
                                dict_df[sat],
                                '.',
                                markersize=4.5)
        self.axes.xaxis.set_major_formatter(md.DateFormatter("%H:%M:%S"))
        self.axes.set_ylabel("SNR [dB-Hz]")
        self.fig.autofmt_xdate()


    def get_event_mean(self, sat, events):
        mean_list = list()
        for trig in events['tow']:
            trig_alt = int(trig/100)*100
            value_event = sat.loc[sat.index == trig_alt]
            if not value_event.empty:
                val_list = value_event[0].tolist()
                mean_list.append(val_list[0])
        if not mean_list == list():
            return mean(mean_list)
        else:
            return 0


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
        self.dict_df_1 = self.satellite.dict_df_1
        self.dict_df_2 = self.satellite.dict_df_2
        self.events = self.satellite.events

        self.enable_events = True
        self.enable_mean = True

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
        self.top_plot = MyDynamicMplCanvas(self.main_widget, self.dict_df_1, self.events, width=5, height=4, dpi=100)
        self.bot_plot = MyDynamicMplCanvas(self.main_widget, self.dict_df_2, self.events, width=5, height=4, dpi=100)
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
        self.dict_df_1 = self.satellite.dict_df_1
        self.dict_df_2 = self.satellite.dict_df_2
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
        self.top_plot.update_figure(self.dict_df_1)
        self.bot_plot.update_figure(self.dict_df_2)
        
        if self.enable_mean:
            self.top_plot.show_mean(self.dict_df_1, self.events)
            self.bot_plot.show_mean(self.dict_df_2, self.events)

        if self.enable_events:
            self.top_plot.show_events(self.events)
            self.bot_plot.show_events(self.events)

        self.top_plot.draw()
        self.bot_plot.draw()

    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","All Files (*);;Python Files (*.py)", options=options)
        return filename


def run_GUI(satellite):
    qApp = QtWidgets.QApplication(sys.argv)

    aw = ApplicationWindow(satellite)
    aw.setWindowTitle("sbf viewer")
    aw.show()
    sys.exit(qApp.exec_())
