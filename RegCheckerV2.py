import cv2
import re
import pytesseract
import requests
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QImage, QPixmap


class CheckIrelandWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Set up the GUI
        self.registration_number_label = QtWidgets.QLabel('Registration Number:')
        self.registration_number_edit = QtWidgets.QLineEdit()
        self.username_label = QtWidgets.QLabel('Username:')
        self.username_edit = QtWidgets.QLineEdit()
        self.check_button = QtWidgets.QPushButton('Check')
        self.check_button.clicked.connect(self.check_ireland)
        self.result_label = QtWidgets.QLabel()

        # Add to Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.registration_number_label)
        layout.addWidget(self.registration_number_edit)
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.check_button)
        layout.addWidget(self.result_label)
        self.setLayout(layout)

    def check_ireland(self):
        # Get the values from the inputs
        registration_number = self.registration_number_edit.text()
        username = self.username_edit.text()

        # Make the API request
        url = 'https://www.regcheck.org.uk/api/reg.asmx/CheckIreland'
        params = {'RegistrationNumber': registration_number, 'username': username}
        response = requests.get(url, params=params)

        # Parse the response
        if response.status_code == 200:
            result = response.text
            self.result_label.setText(result)

            # Write the result to a file
            with open('ireland_results.txt', 'a') as f:
                f.write(result + '\n')
        else:
            self.result_label.setText('Error: ' + str(response.status_code))


class UiMainWindow(object):
    def setup_ui(self, main_window):
        # Set up the Main UI Window
        main_window.setObjectName("Main_Window")
        main_window.resize(640, 480)
        self.central_widget = QtWidgets.QWidget(main_window)
        self.central_widget.setObjectName("central_widget")
        self.label = QtWidgets.QLabel(self.central_widget)
        self.label.setGeometry(QtCore.QRect(0, 0, 640, 480))
        self.label.setText("")
        self.label.setObjectName("label")
        main_window.setCentralWidget(self.central_widget)
        self.re_translate_ui(main_window)

    def re_translate_ui(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("Main_Window", "Automatic Licence Plate Recognition System"))


class ALPRSystem(QtWidgets.QMainWindow):
    def __init__(self):
        super(ALPRSystem, self).__init__()
        self.ui = UiMainWindow()

        # Create a menu bar with an exit action
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu("File")
        exit_action = QtWidgets.QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.closeEvent)
        file_menu.addAction(exit_action)
        self.ui.setup_ui(self)

        # Create a central widget and a layout for the GUI
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)

        # Create an instance of CheckIrelandWidget
        self.check_ireland_widget = CheckIrelandWidget()

        # Create a QScrollArea widget to contain the CheckIrelandWidget's output
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Add the CheckIrelandWidget to the QScrollArea
        scroll_area.setWidget(self.check_ireland_widget)

        # Add the video stream to the layout
        layout.addWidget(self.ui.label)

        # Set up the video capture
        self.cap = cv2.VideoCapture(0)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(5)

    def update_frame(self):
        # Continuously update the feed
        ret, self.image = self.cap.read()
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.process_image()

    def process_image(self):
        # Gray the Image
        gray = cv2.cvtColor(self.image, cv2.COLOR_RGB2GRAY)
        # Apply the Gaussian Blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        # Add the Canny
        canny = cv2.Canny(blur, 50, 150)
        # Find the Contours
        contours, _ = cv2.findContours(canny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            # Set the area as the contours counted
            area = cv2.contourArea(contour)
            if area > 500:
                # Draw a Bounding Box
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(self.image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                roi = gray[y:y + h, x:x + w]
                # Pytesseract conversion from Image to String text
                text = pytesseract.image_to_string(roi, config='--psm 11')
                if text:
                    # Check if the detected plate contains the letters "IRL"
                    if re.search(r'\bIRL\b', text):
                        cv2.putText(self.image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        # Display a popup message if the plate is from Ireland
                        msg = QtWidgets.QMessageBox()
                        msg.setIcon(QtWidgets.QMessageBox.Information)
                        msg.setText("Registration is from Ireland")
                        msg.setWindowTitle("ALPR System")
                        msg.exec_()
                        # Check if the detected plate contains the letters "GB"
                    elif re.search(r'\bGB\b', text):
                        cv2.putText(self.image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        # Display a popup message if the plate is from Great Britain
                        msg = QtWidgets.QMessageBox()
                        msg.setIcon(QtWidgets.QMessageBox.Information)
                        msg.setText("Registration is from Great Britain")
                        msg.setWindowTitle("ALPR System")
                        msg.exec_()
                        # Match the regex of an Irish licence plate
                    elif re.match(r'^[1-9][0-9]{0,3}-[A-Z]-[1-9][0-9]{0,4}$', text):
                        cv2.putText(self.image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        # Display a popup message if the plate is from Ireland
                        msg = QtWidgets.QMessageBox()
                        msg.setIcon(QtWidgets.QMessageBox.Information)
                        msg.setText("Registration is from Ireland")
                        msg.setWindowTitle("ALPR System")
                        msg.exec_()
                        # Match the regex of a GB licence plate
                    elif re.match(r'^[A-Z]{2}\d{2}[A-Z]{3}$', text):
                        cv2.putText(self.image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        # Display a popup message if the plate is from Great Britain
                        msg = QtWidgets.QMessageBox()
                        msg.setIcon(QtWidgets.QMessageBox.Information)
                        msg.setText("Registration is from Great Britain")
                        msg.setWindowTitle("ALPR System")
                        msg.exec_()
                    else:
                        cv2.putText(self.image, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    # Print the detected plate number to the terminal
                    print(f"Detected plate number: {text}")
            self.display_image()

    def display_image(self):
        qformat = QImage.Format_Indexed8
        if len(self.image.shape) == 3:
            if self.image.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888
        self.img = QImage(self.image, self.image.shape[1], self.image.shape[0], self.image.strides[0], qformat)
        self.img = self.img.rgbSwapped()
        self.ui.label.setPixmap(QPixmap.fromImage(self.img))
        self.ui.label.setScaledContents(True)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = ALPRSystem()
    window.show()
    sys.exit(app.exec_())
