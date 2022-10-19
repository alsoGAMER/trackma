# This file is part of Trackma.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import os
import sys

from trackma import utils
from trackma.ui.qt.mainwindow import MainWindow


def main(force_qt4=False, force_qt6=False):
    print("Trackma-qt v{}".format(utils.VERSION))

    debug = False

    if '-h' in sys.argv:
        print("Usage: trackma-qt [options]")
        print()
        print('Options:')
        print(' -d  Shows debugging information')
        print(' -4  Force Qt4')
        print(' -6  Force Qt6')
        print(' -h  Shows this help')
        sys.exit(0)
    if '-d' in sys.argv:
        print('Showing debug information.')
        debug = True
    if '-4' in sys.argv:
        print('Forcing Qt4.')
        force_qt4 = True
    if '-6' in sys.argv:
        print('Forcing Qt6.')
        force_qt6 = True

    if not force_qt4:
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            os.environ['PYQT5'] = "1"
        except ImportError:
            print("Couldn't import Qt5 dependencies. "
                  "Make sure you installed the PyQt5 package.")

    if 'PYQT5' not in os.environ:
        try:
            import sip
            sip.setapi('QVariant', 2)
            from PyQt4.QtGui import QApplication, QMessageBox
        except ImportError:
            print("Couldn't import Qt4 dependencies. "
                  "Make sure you installed the PyQt4 package.")
            sys.exit(-1)
    
    if force_qt6:
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            os.environ['PYQT6'] = "1"
        except ImportError as e:
            print("Error while import pyqt6")
            print(e)
            sys.exit(-1)
    
    if 'PYQT6' not in os.environ:
        try:
            import sip
            sip.setapi('QVariant', 3)
            from PyQt5.QtWidgets import QApplication, QMessageBox
        except ImportError as e:
            print("Couldn't import Qt5 dependencies. "
                  "Make sure you installed the PyQt5 package.")
            # print(e)
            sys.exit(-1)
    
    try:
        from PIL import Image
        os.environ['imaging_available'] = "1"
    except ImportError:
        try:
            import Image
            os.environ['imaging_available'] = "1"
        except ImportError:
            print("Warning: PIL or Pillow isn't available. "
                  "Preview images will be disabled.")

    app = QApplication(sys.argv)
    app.setApplicationName("trackma")
    app.setDesktopFileName("trackma")
    if os.name == "nt":
        import ctypes
        myappid = 'trackma' + utils.VERSION
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    try:
        # keep the variable around to prevent it from being gc'ed
        main_window = MainWindow(debug)
        sys.exit(app.exec_())
    except utils.TrackmaFatal as e:
        QMessageBox.critical(None, 'Fatal Error', "{0}".format(e), QMessageBox.Ok)
