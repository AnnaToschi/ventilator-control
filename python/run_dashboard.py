# import sys
# from PyQt5.QtWidgets import QDialog, QApplication
# from dashboard import Ui_Dialog


# from epics import caget, caput, cainfo
# import os
 
# os.environ['EPICS_CA_ADDR_LIST'] = 'localhost'
# os.environ['EPICS_CA_AUTO_ADDR_LIST'] = 'NO'

# class AppWindow(QDialog):
#     def __init__(self):
#         super().__init__()
#         self.ui = Ui_Dialog()
#         self.ui.setupUi(self)
#         self.show()  

#     def on_click(self):
#         print('PyQt5 button click')

# app = QApplication(sys.argv)
# w = AppWindow()
# w.show()
# sys.exit(app.exec_())


from epics import caget, caput, cainfo
import os
 
os.environ['EPICS_CA_ADDR_LIST'] = 'localhost'
os.environ['EPICS_CA_AUTO_ADDR_LIST'] = 'NO'

caput('Raspi:central:Set-PEEP',10)
print(caget('Raspi:central:Set-PEEP'))
