from PyQt5 import QtCore, QtGui, QtWidgets
import serial.tools.list_ports
import serial , time, sys, glob, platform, os, zlib
from PyQt5.QtCore import pyqtSignal
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

filename = ""
filepath = ""
portname = ""
recording = False

def errorHandler(exctype, value, traceback):
    print(exctype, value, traceback)
    
sys.excepthook = errorHandler

class GraphWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.canvas)

    def plot_graph(self, times, db_levels):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(times, db_levels)
        ax.set_xlabel('Time (Seconds)')
        ax.set_ylabel('Decibels (dB)')
        ax.set_title('Time to Decibel Graph')
        self.figure.tight_layout()
        self.canvas.draw()

class ADThread(QtCore.QThread):
    data_fsave = pyqtSignal(list, list, list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.inp = ""

    def run(self):
        global ser
        while True:
            # self.inp = ser.readline().decode('utf-8').strip()
            pass

    def send_data(self):
        global ser

class SoundThread(QtCore.QThread):
    graph_updated = pyqtSignal(list, list)
    stop_save = pyqtSignal(list, list, list)

    def __init__(self, sample_rate=44100, block_size=1024):
        super().__init__()
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.running = False
        self.db_levels = []
        self.times = []
        self.pressure_levels = []

    def calculate_db(self, audio_data):
        rms = np.sqrt(np.mean(np.square(audio_data)))
        db = 20 * np.log10(rms)
        return db

    def callback(self, indata, frames, timestamp, status):
        db_level = self.calculate_db(indata)
        elapsed_time = time.time() - self.start_time
        self.db_levels.append(db_level)
        self.times.append(elapsed_time)

    def run(self):
        self.start_time = time.time()
        with sd.InputStream(callback=self.callback, channels=1, samplerate=self.sample_rate, blocksize=self.block_size):
            self.running = True 
            while self.running:
                pass

    def stop(self):
        self.running = False
        self.wait()
        self.graph_updated.emit(list(self.times), list(self.db_levels))
        self.stop_save.emit(list(self.times), list(self.db_levels), list(self.pressure_levels))

    # def emit_graph(self):
    #     self.graph_updated.emit(list(self.times), list(self.db_levels))

class SaveThread(QtCore.QThread):
    complete = pyqtSignal()

    def __init__(self, times, db_levels, pressure_levels, parent=None):
        super().__init__(parent)
        self.times = times
        self.db_levels = db_levels
        self.pressure_levels = pressure_levels

    def run(self):
        global filename, filepath
        fn = filename + ".txt"
        openfile = open(os.path.join(filepath, fn), "wb")
        sendtext = ""
        for x in range(len(self.times)):
            sendtext += (str(self.times[x]) + " " + str(self.db_levels[x]) + "\n")
        comp = zlib.compress(sendtext.encode('utf-8'), 9)
        openfile.write(comp)
        openfile.close()
        self.complete.emit()

class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(480, 640)
        MainWindow.setMinimumSize(QtCore.QSize(480, 640))
        MainWindow.setMaximumSize(QtCore.QSize(480, 640))
        MainWindow.setMouseTracking(False)
        MainWindow.setAutoFillBackground(False)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 400, 461, 231))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.line = QtWidgets.QFrame(self.verticalLayoutWidget)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        self.GraphLabel = QtWidgets.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(14)
        self.GraphLabel.setFont(font)
        self.GraphLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.GraphLabel.setObjectName("GraphLabel")
        self.verticalLayout.addWidget(self.GraphLabel)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.GetFileDiagButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        self.GetFileDiagButton.setMaximumSize(QtCore.QSize(100, 16777215))
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(14)
        self.GetFileDiagButton.setFont(font)
        self.GetFileDiagButton.setObjectName("GetFileDiagButton")
        self.GetFileDiagButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.GetFileDiagButton.clicked.connect(self.getfile)
        self.horizontalLayout_3.addWidget(self.GetFileDiagButton)
        self.FilePath = QtWidgets.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(10)
        self.FilePath.setWordWrap(True)
        self.FilePath.setFont(font)
        self.FilePath.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.FilePath.setObjectName("FilePath")
        self.horizontalLayout_3.addWidget(self.FilePath)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.PressureLabel = QtWidgets.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(14)
        self.PressureLabel.setFont(font)
        self.PressureLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.PressureLabel.setObjectName("PressureLabel")
        self.verticalLayout.addWidget(self.PressureLabel)
        self.FilenameLineEdit = QtWidgets.QLineEdit(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(14)
        self.FilenameLineEdit.setFont(font)
        self.FilenameLineEdit.setObjectName("FilenameLineEdit")
        self.verticalLayout.addWidget(self.FilenameLineEdit)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.PortLabel = QtWidgets.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(14)
        self.PortLabel.setFont(font)
        self.PortLabel.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.PortLabel.setObjectName("PortLabel")
        self.horizontalLayout_2.addWidget(self.PortLabel)
        self.PortDropDown = QtWidgets.QComboBox(self.verticalLayoutWidget)
        self.PortDropDown.setMinimumSize(QtCore.QSize(305, 35))
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(14)
        self.PortDropDown.setFont(font)
        self.PortDropDown.setObjectName("ComPortDropDown")
        self.horizontalLayout_2.addWidget(self.PortDropDown)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.SaveButton = QtWidgets.QPushButton(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(14)
        self.SaveButton.setFont(font)
        self.SaveButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.SaveButton.setObjectName("SaveButton")
        self.SaveButton.clicked.connect(self.save)
        self.horizontalLayout_2.addWidget(self.SaveButton)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(10, 10, 461, 131))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.StartRecordLabel = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        self.StartRecordLabel.setMaximumSize(QtCore.QSize(135, 16777215))
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(20)
        self.StartRecordLabel.setFont(font)
        self.StartRecordLabel.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.StartRecordLabel.setObjectName("StartRecordLabel")
        self.horizontalLayout.addWidget(self.StartRecordLabel)
        self.RecordButton = QtWidgets.QPushButton(self.verticalLayoutWidget_2)
        self.RecordButton.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.RecordButton.sizePolicy().hasHeightForWidth())
        self.RecordButton.setSizePolicy(sizePolicy)
        self.RecordButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.RecordButton.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("./icons/startrecord.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.RecordButton.setIcon(icon)
        self.RecordButton.setIconSize(QtCore.QSize(50, 50))
        self.RecordButton.setAutoDefault(False)
        self.RecordButton.setDefault(False)
        self.RecordButton.setFlat(False)
        self.RecordButton.setObjectName("RecordButton")
        self.RecordButton.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.RecordButton.clicked.connect(self.recordClick)
        self.horizontalLayout.addWidget(self.RecordButton)
        self.label = QtWidgets.QLabel(self.verticalLayoutWidget_2)
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(20)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.ProgressBar = QtWidgets.QProgressBar(self.verticalLayoutWidget_2)
        font = QtGui.QFont()
        font.setFamily("AppleSDGothicNeoB00")
        font.setPointSize(10)
        self.ProgressBar.setFont(font)
        self.ProgressBar.setProperty("value", 0)
        self.ProgressBar.setRange(0, 1)
        self.ProgressBar.setTextVisible(False)
        self.ProgressBar.setObjectName("ProgressBar")
        self.verticalLayout_2.addWidget(self.ProgressBar)
        self.line_2 = QtWidgets.QFrame(self.verticalLayoutWidget_2)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.verticalLayout_2.addWidget(self.line_2)
        self.ShowGraphLabel = GraphWidget(self.centralwidget)
        self.ShowGraphLabel.setGeometry(QtCore.QRect(0, 135, 480, 270))
        self.ShowGraphLabel.setObjectName("ShowGraphLabel")
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        if platform.system() == 'Windows':
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                self.PortDropDown.addItem(str(p.device))
        elif platform.system() == 'Darwin':
            ports = glob.glob('/dev/tty.*')
            for p in ports:
                self.PortDropDown.addItem(str(p))
        else:
            print("Unsupported OS")
            sys.exit()

        self.PortDropDown.addItem("COM1")

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "ADSync - made by Jooney Han"))
        self.GraphLabel.setText(_translate("MainWindow", "파일 저장 위치:"))
        self.GetFileDiagButton.setText(_translate("MainWindow", "폴더 선택"))
        self.FilePath.setText(_translate("MainWindow", "file path"))
        self.PressureLabel.setText(_translate("MainWindow", "파일 저장 이름:"))
        self.PortLabel.setText(_translate("MainWindow", "포트: "))
        self.SaveButton.setText(_translate("MainWindow", "저장"))
        self.StartRecordLabel.setText(_translate("MainWindow", "녹음 시작:"))

    def getfile(self):
        self.FilePath.setText(QtWidgets.QFileDialog.getExistingDirectory(self.centralwidget, 'Select Directory'))
    
    def save(self):
        global filename, filepath, portname, ser
        filename = self.FilenameLineEdit.text()
        filepath = self.FilePath.text()
        portname = self.PortDropDown.currentText()
        ser = serial.Serial(portname, 9600, timeout=1)

    def recordClick(self):
        global ser, filename, filepath, recording 
        if recording == False:
            self.RecordButton.setIcon(QtGui.QIcon("./icons/stoprecord.png"))
            self.StartRecordLabel.setText("녹음 중...")
            recording = True
            self.thread1 = ADThread()
            ser.flushInput()
            self.thread1.start()
            self.start_listening()
        else:
            self.RecordButton.setIcon(QtGui.QIcon("./icons/startrecord.png"))
            self.RecordButton.setDisabled(True)
            self.StartRecordLabel.setText("녹음 시작:")
            recording = False
            self.thread1.terminate()
            self.sound_meter_thread.stop()

    def start_listening(self):
        self.ProgressBar.setRange(0, 0)
        self.sound_meter_thread = SoundThread()
        self.sound_meter_thread.graph_updated.connect(self.show_graph)
        self.sound_meter_thread.stop_save.connect(self.save_file)
        # self.update_timer = QtCore.QTimer()
        # self.update_timer.timeout.connect(self.sound_meter_thread.emit_graph)
        # self.update_timer.start(2000)
        self.sound_meter_thread.start() 

    def save_file(self, times, db_levels, pressure_levels):
        self.sthread = SaveThread(times, db_levels, pressure_levels)
        self.sthread.complete.connect(self.after_save)
        self.sthread.start()
        
    def after_save(self):
        self.ProgressBar.setRange(0, 1)
        self.label.setText("저장 완료! ")
        self.ftimer = QtCore.QTimer()
        self.ftimer.timeout.connect(lambda: {self.fade(self.label), self.ftimer.stop()})
        self.ftimer.start(1000)
        self.sthread.terminate()
        self.RecordButton.setDisabled(False)

    def show_graph(self, times, db_levels):
        self.ShowGraphLabel.plot_graph(times, db_levels)

    def fade(self, widget):
        self.effect = QtWidgets.QGraphicsOpacityEffect()
        widget.setGraphicsEffect(self.effect)
        self.animation = QtCore.QPropertyAnimation(self.effect, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.start()
        self.animation.finished.connect(lambda: {self.label.setText(""), self.effect.deleteLater()})

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())