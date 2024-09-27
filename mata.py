import sys
import os
import cv2
import sqlite3
import numpy as np
from datetime import datetime
from PyQt5 import QtWidgets, QtGui, QtCore

# Database Manager
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('podoscope.db')
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Create customers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                age INTEGER,
                phone TEXT,
                email TEXT
            )
        ''')
        # Create visits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS visits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                date TEXT,
                image_path TEXT,
                note TEXT,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            )
        ''')
        self.conn.commit()

    def add_customer(self, first_name, last_name, age, phone, email):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO customers (first_name, last_name, age, phone, email)
            VALUES (?, ?, ?, ?, ?)
        ''', (first_name, last_name, age, phone, email))
        self.conn.commit()
        return cursor.lastrowid

    def get_customer_by_id(self, customer_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE id = ?', (customer_id,))
        row = cursor.fetchone()
        if row:
            keys = ['id', 'first_name', 'last_name', 'age', 'phone', 'email']
            return dict(zip(keys, row))
        else:
            return None

    def search_customers(self, search_text):
        cursor = self.conn.cursor()
        query = '%' + search_text + '%'
        cursor.execute('''
            SELECT * FROM customers
            WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR email LIKE ?
        ''', (query, query, query, query))
        rows = cursor.fetchall()
        keys = ['id', 'first_name', 'last_name', 'age', 'phone', 'email']
        return [dict(zip(keys, row)) for row in rows]

    def get_all_customers(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM customers')
        rows = cursor.fetchall()
        keys = ['id', 'first_name', 'last_name', 'age', 'phone', 'email']
        return [dict(zip(keys, row)) for row in rows]

    def delete_customer(self, customer_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
        self.conn.commit()

    def add_visit(self, customer_id, date, image_path, note):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO visits (customer_id, date, image_path, note)
            VALUES (?, ?, ?, ?)
        ''', (customer_id, date, image_path, note))
        self.conn.commit()
        return cursor.lastrowid

    def get_visits_by_customer_id(self, customer_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM visits WHERE customer_id = ?', (customer_id,))
        rows = cursor.fetchall()
        keys = ['id', 'customer_id', 'date', 'image_path', 'note']
        return [dict(zip(keys, row)) for row in rows]

    def get_all_visits(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM visits')
        rows = cursor.fetchall()
        keys = ['id', 'customer_id', 'date', 'image_path', 'note']
        return [dict(zip(keys, row)) for row in rows]

    def get_visit_by_id(self, visit_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM visits WHERE id = ?', (visit_id,))
        row = cursor.fetchone()
        if row:
            keys = ['id', 'customer_id', 'date', 'image_path', 'note']
            return dict(zip(keys, row))
        else:
            return None

    def delete_visit(self, visit_id):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM visits WHERE id = ?', (visit_id,))
        self.conn.commit()

# Main Application Class
class PodoscopeApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Podoscope Application")
        self.setGeometry(100, 100, 800, 600)
        self.db_manager = DatabaseManager()

        # Apply dark theme
        self.apply_dark_theme()

        self.initUI()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #2e2e2e;
                color: white;
            }
            QLabel, QPushButton, QLineEdit, QTextEdit, QTableWidget, QHeaderView::section, QSlider::handle:horizontal, QComboBox {
                color: white;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: none;
                padding: 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QLineEdit, QTextEdit {
                background-color: #3a3a3a;
                border: 1px solid #5a5a5a;
                padding: 5px;
                color: white;
            }
            QSlider::groove:horizontal {
                height: 10px;
                background: #3a3a3a;
            }
            QSlider::handle:horizontal {
                background: #5a5a5a;
                width: 20px;
                margin: -5px 0;
            }
            QLabel {
                color: white; /* Toto zabezpečí, že všetky QLabely budú mať bielu farbu */
            }
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #5a5a5a;
                color: white;
            }
            QTableWidget {
                background-color: #3a3a3a;
                color: white;
                selection-background-color: #5a5a5a;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: white;
            }
            QListWidget, QMenu, QMenuBar {
                background-color: #2e2e2e;
                color: white;
            }
            QMenuBar::item:selected {
                background-color: #3a3a3a;
            }
            QMenu::item:selected {
                background-color: #3a3a3a;
            }
        """)

    def initUI(self):
        # Create main widget and layout
        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout()

        # Live Camera Feed
        self.camera_label = QtWidgets.QLabel()
        self.camera_label.setAlignment(QtCore.Qt.AlignCenter)
        self.camera_label.setFixedSize(640, 480)
        main_layout.addWidget(self.camera_label, alignment=QtCore.Qt.AlignCenter)

        # Capture Button
        self.capture_button = QtWidgets.QPushButton("Snímať")
        self.capture_button.clicked.connect(self.open_customer_selection)
        main_layout.addWidget(self.capture_button, alignment=QtCore.Qt.AlignCenter)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Menu bar
        self.create_menu()

        # Start camera feed
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QtWidgets.QMessageBox.critical(self, "Camera Error", "Unable to access the camera.")
            return

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def create_menu(self):
        menubar = self.menuBar()

        customers_menu = menubar.addMenu('Zákazníci')
        visits_menu = menubar.addMenu('Vizity')
        help_menu = menubar.addMenu('Pomoc')

        # Customers Menu Actions
        add_customer_action = QtWidgets.QAction('Pridať zákazníka', self)
        add_customer_action.triggered.connect(self.add_customer_dialog)
        customers_menu.addAction(add_customer_action)

        list_customers_action = QtWidgets.QAction('Zoznam zákazníkov', self)
        list_customers_action.triggered.connect(self.list_customers)
        customers_menu.addAction(list_customers_action)

        # Visits Menu Actions
        view_visits_action = QtWidgets.QAction('Zobraziť vizity', self)
        view_visits_action.triggered.connect(self.view_visits)
        visits_menu.addAction(view_visits_action)

        # Help Menu Actions
        about_action = QtWidgets.QAction('O aplikácii', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = cv2.flip(image, 1)
            height, width, channel = image.shape
            bytesPerLine = channel * width
            q_img = QtGui.QImage(image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(q_img)
            # Scale pixmap to fit label size
            pixmap = pixmap.scaled(self.camera_label.width(), self.camera_label.height(), QtCore.Qt.KeepAspectRatio)
            self.camera_label.setPixmap(pixmap)

    def open_customer_selection(self):
        # Pause the camera
        self.timer.stop()

        # Open customer selection dialog
        dialog = CustomerSelectionDialog(self.db_manager)
        if dialog.exec_():
            customer_id = dialog.get_selected_customer()
            if customer_id == -1:
                # Guest, do not save
                self.display_captured_image()
            elif customer_id == 0:
                # Add new customer
                self.add_customer_dialog()
                # Resume camera
                self.timer.start(30)
            else:
                # Save image and create visit entry
                self.save_image_and_visit(customer_id)
        else:
            # Resume the camera
            self.timer.start(30)

    def add_customer_dialog(self):
        dialog = AddCustomerDialog(self.db_manager)
        if dialog.exec_():
            QtWidgets.QMessageBox.information(self, "Success", "Customer added successfully!")
        else:
            pass

    def list_customers(self):
        dialog = ListCustomersDialog(self.db_manager)
        dialog.exec_()

    def save_image_and_visit(self, customer_id):
        # Create directory if it doesn't exist
        customer = self.db_manager.get_customer_by_id(customer_id)
        directory = os.path.join('Gallery', f"{customer['first_name']}_{customer['last_name']}")
        os.makedirs(directory, exist_ok=True)

        # Save image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_path = os.path.join(directory, f"{timestamp}.png")
        cv2.imwrite(image_path, self.current_frame)

        # Add visit to database
        visit_id = self.db_manager.add_visit(customer_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), image_path, '')

        # Open Image Edit Dialog
        self.image_edit_dialog = ImageEditDialog(self.current_frame, image_path, visit_id, self.db_manager)
        self.image_edit_dialog.exec_()

        # Resume camera
        self.timer.start(30)

    def display_captured_image(self):
        # Open Image Edit Dialog in Guest Mode
        self.image_edit_dialog = ImageEditDialog(self.current_frame)
        self.image_edit_dialog.exec_()

        # Resume camera
        self.timer.start(30)

    def view_visits(self):
        dialog = VisitsDialog(self.db_manager)
        dialog.exec_()

    def show_about_dialog(self):
        QtWidgets.QMessageBox.about(self, "O aplikácii", "Podoscope Application\nVerzia 1.0\n© 2023")

    def closeEvent(self, event):
        # Release the camera when the application is closed
        self.cap.release()
        event.accept()

# Customer Selection Dialog
class CustomerSelectionDialog(QtWidgets.QDialog):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.selected_customer_id = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Výber zákazníka")
        self.resize(400, 300)

        self.apply_dark_theme()

        layout = QtWidgets.QVBoxLayout()

        # Search bar
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Vyhľadať zákazníkov...")
        self.search_bar.textChanged.connect(self.update_customer_list)
        layout.addWidget(self.search_bar)

        # Customer list
        self.customer_list = QtWidgets.QListWidget()
        self.customer_list.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.customer_list)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.select_button = QtWidgets.QPushButton("Vybrať")
        self.select_button.clicked.connect(self.select_customer)
        self.select_button.setEnabled(False)
        self.guest_button = QtWidgets.QPushButton("Hosť")
        self.guest_button.clicked.connect(self.select_guest)
        self.add_customer_button = QtWidgets.QPushButton("Pridať zákazníka")
        self.add_customer_button.clicked.connect(self.add_customer)
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.guest_button)
        button_layout.addWidget(self.add_customer_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.update_customer_list()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e;
            }
        """)

    def update_customer_list(self):
        search_text = self.search_bar.text()
        customers = self.db_manager.search_customers(search_text)
        self.customer_list.clear()
        for customer in customers:
            item_text = f"{customer['first_name']} {customer['last_name']} - {customer['phone']}"
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.UserRole, customer['id'])
            self.customer_list.addItem(item)

    def on_item_clicked(self, item):
        self.selected_customer_id = item.data(QtCore.Qt.UserRole)
        self.select_button.setEnabled(True)

    def select_customer(self):
        if self.selected_customer_id:
            self.accept()

    def select_guest(self):
        self.selected_customer_id = -1
        self.accept()

    def add_customer(self):
        self.selected_customer_id = 0
        self.accept()

    def get_selected_customer(self):
        return self.selected_customer_id

# Image Edit Dialog
class ImageEditDialog(QtWidgets.QDialog):
    def __init__(self, image, image_path=None, visit_id=None, db_manager=None):
        super().__init__()
        self.original_image = image
        self.edit_image = image.copy()
        self.image_path = image_path
        self.visit_id = visit_id
        self.db_manager = db_manager
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Úprava obrázka")
        self.resize(800, 600)

        self.apply_dark_theme()

        layout = QtWidgets.QVBoxLayout()

        # Image display
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setFixedSize(640, 480)
        layout.addWidget(self.image_label)

        self.show_image(self.edit_image)

        # Filters
        filter_layout = QtWidgets.QGridLayout()

        # Brightness slider
        self.brightness_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(QtWidgets.QLabel("Jas"), 0, 0)
        filter_layout.addWidget(self.brightness_slider, 0, 1)

        # Contrast slider
        self.contrast_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_slider.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(QtWidgets.QLabel("Kontrast"), 1, 0)
        filter_layout.addWidget(self.contrast_slider, 1, 1)

        # Saturation slider
        self.saturation_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.saturation_slider.setRange(-100, 100)
        self.saturation_slider.setValue(0)
        self.saturation_slider.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(QtWidgets.QLabel("Saturácia"), 2, 0)
        filter_layout.addWidget(self.saturation_slider, 2, 1)

        # Shading slider
        self.shading_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.shading_slider.setRange(1, 200)
        self.shading_slider.setValue(100)
        self.shading_slider.valueChanged.connect(self.apply_filters)
        filter_layout.addWidget(QtWidgets.QLabel("Tiene"), 3, 0)
        filter_layout.addWidget(self.shading_slider, 3, 1)

        layout.addLayout(filter_layout)

        # Note field
        self.note_field = QtWidgets.QTextEdit()
        self.note_field.setPlaceholderText("Napíšte poznámku...")
        layout.addWidget(self.note_field)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("Uložiť")
        self.save_button.clicked.connect(self.save_edited_image)
        self.cancel_button = QtWidgets.QPushButton("Zrušiť")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e;
            }
        """)

    def show_image(self, image):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channel = image.shape
        bytesPerLine = channel * width
        q_img = QtGui.QImage(image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(q_img)
        # Scale pixmap to fit label size
        pixmap = pixmap.scaled(self.image_label.width(), self.image_label.height(), QtCore.Qt.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)

    def apply_filters(self):
        image = self.original_image.copy()

        # Apply brightness and contrast
        brightness = self.brightness_slider.value()
        contrast = self.contrast_slider.value()

        # Adjust brightness and contrast
        image = cv2.convertScaleAbs(image, alpha=1 + (contrast / 100), beta=brightness)

        # Convert to HSV for saturation adjustment
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype("float32")

        saturation = self.saturation_slider.value()
        h, s, v = cv2.split(hsv_image)
        s = s + saturation
        s = np.clip(s, 0, 255)
        hsv_image = cv2.merge([h, s, v])
        image = cv2.cvtColor(hsv_image.astype("uint8"), cv2.COLOR_HSV2BGR)

        # Apply shading (gamma correction)
        gamma_value = self.shading_slider.value() / 100.0
        invGamma = 1.0 / gamma_value
        table = np.array([((i / 255.0) ** invGamma) * 255
                          for i in np.arange(0, 256)]).astype("uint8")
        image = cv2.LUT(image, table)

        self.edit_image = image
        self.show_image(self.edit_image)

    def save_edited_image(self):
        if self.image_path and self.visit_id and self.db_manager:
            # Overwrite the existing image
            cv2.imwrite(self.image_path, self.edit_image)
            # Update note in database
            note = self.note_field.toPlainText()
            cursor = self.db_manager.conn.cursor()
            cursor.execute('UPDATE visits SET note = ? WHERE id = ?', (note, self.visit_id))
            self.db_manager.conn.commit()
            QtWidgets.QMessageBox.information(self, "Úspech", "Obrázok a poznámka boli úspešne uložené!")
            self.accept()
        else:
            # For guest, just show a message
            QtWidgets.QMessageBox.information(self, "Info", "Obrázok nebol uložený (Hosť).")
            self.accept()

# Add Customer Dialog
class AddCustomerDialog(QtWidgets.QDialog):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Pridať zákazníka")
        self.resize(400, 300)

        self.apply_dark_theme()

        layout = QtWidgets.QFormLayout()

        self.first_name_field = QtWidgets.QLineEdit()
        self.last_name_field = QtWidgets.QLineEdit()
        self.age_field = QtWidgets.QSpinBox()
        self.age_field.setRange(0, 120)
        self.phone_field = QtWidgets.QLineEdit()
        self.email_field = QtWidgets.QLineEdit()

        layout.addRow("Meno:", self.first_name_field)
        layout.addRow("Priezvisko:", self.last_name_field)
        layout.addRow("Vek:", self.age_field)
        layout.addRow("Telefón:", self.phone_field)
        layout.addRow("Email:", self.email_field)

        # Buttons
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.add_customer)
        self.button_box.rejected.connect(self.reject)
        layout.addRow(self.button_box)

        self.setLayout(layout)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e;
            }
        """)

    def add_customer(self):
        # Validate input
        first_name = self.first_name_field.text()
        last_name = self.last_name_field.text()
        age = self.age_field.value()
        phone = self.phone_field.text()
        email = self.email_field.text()

        if not first_name or not last_name:
            QtWidgets.QMessageBox.warning(self, "Chyba", "Meno a priezvisko sú povinné.")
            return

        # Add customer to the database
        self.db_manager.add_customer(first_name, last_name, age, phone, email)
        self.accept()

# List Customers Dialog
class ListCustomersDialog(QtWidgets.QDialog):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Zákazníci")
        self.resize(600, 400)

        self.apply_dark_theme()

        layout = QtWidgets.QVBoxLayout()

        # Customer list
        self.customer_table = QtWidgets.QTableWidget()
        self.customer_table.setColumnCount(5)
        self.customer_table.setHorizontalHeaderLabels(['Meno', 'Priezvisko', 'Vek', 'Telefón', 'Email'])
        self.customer_table.horizontalHeader().setStretchLastSection(True)
        self.customer_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        layout.addWidget(self.customer_table)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("Pridať")
        self.add_button.clicked.connect(self.add_customer)
        self.delete_button = QtWidgets.QPushButton("Odstrániť")
        self.delete_button.clicked.connect(self.delete_customer)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.load_customers()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e;
            }
        """)

    def load_customers(self):
        customers = self.db_manager.get_all_customers()
        self.customer_table.setRowCount(0)
        for customer in customers:
            row_position = self.customer_table.rowCount()
            self.customer_table.insertRow(row_position)
            self.customer_table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(customer['first_name']))
            self.customer_table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(customer['last_name']))
            self.customer_table.setItem(row_position, 2, QtWidgets.QTableWidgetItem(str(customer['age'])))
            self.customer_table.setItem(row_position, 3, QtWidgets.QTableWidgetItem(customer['phone']))
            self.customer_table.setItem(row_position, 4, QtWidgets.QTableWidgetItem(customer['email']))
            self.customer_table.setRowHeight(row_position, 50)

    def add_customer(self):
        dialog = AddCustomerDialog(self.db_manager)
        if dialog.exec_():
            self.load_customers()

    def delete_customer(self):
        selected_rows = self.customer_table.selectionModel().selectedRows()
        if selected_rows:
            response = QtWidgets.QMessageBox.question(self, "Potvrdiť odstránenie", "Naozaj chcete odstrániť vybraných zákazníkov?")
            if response == QtWidgets.QMessageBox.Yes:
                for index in selected_rows:
                    row = index.row()
                    customer_id = self.db_manager.get_all_customers()[row]['id']
                    self.db_manager.delete_customer(customer_id)
                self.load_customers()

# Visits Dialog with Filters
class VisitsDialog(QtWidgets.QDialog):
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Vizity")
        self.resize(800, 600)

        self.apply_dark_theme()

        layout = QtWidgets.QVBoxLayout()

        # Filter options
        filter_layout = QtWidgets.QHBoxLayout()
        self.customer_filter_combo = QtWidgets.QComboBox()
        self.customer_filter_combo.addItem("Všetci zákazníci", 0)
        customers = self.db_manager.get_all_customers()
        for customer in customers:
            customer_name = f"{customer['first_name']} {customer['last_name']}"
            self.customer_filter_combo.addItem(customer_name, customer['id'])
        self.customer_filter_combo.currentIndexChanged.connect(self.load_visits)

        self.date_from = QtWidgets.QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QtCore.QDate.currentDate().addMonths(-1))
        self.date_from.dateChanged.connect(self.load_visits)

        self.date_to = QtWidgets.QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QtCore.QDate.currentDate())
        self.date_to.dateChanged.connect(self.load_visits)

        filter_layout.addWidget(QtWidgets.QLabel("Zákazník:"))
        filter_layout.addWidget(self.customer_filter_combo)
        filter_layout.addWidget(QtWidgets.QLabel("Od:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QtWidgets.QLabel("Do:"))
        filter_layout.addWidget(self.date_to)

        layout.addLayout(filter_layout)

        # Visits list
        self.visits_table = QtWidgets.QTableWidget()
        self.visits_table.setColumnCount(5)
        self.visits_table.setHorizontalHeaderLabels(['Meno zákazníka', 'Dátum', 'Obrázok', 'Poznámka', 'Akcie'])
        self.visits_table.horizontalHeader().setStretchLastSection(True)
        self.visits_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.visits_table.verticalHeader().setVisible(False)
        layout.addWidget(self.visits_table)

        self.setLayout(layout)

        self.load_visits()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e;
            }
        """)

    def load_visits(self):
        customer_id = self.customer_filter_combo.currentData()
        date_from = self.date_from.date().toPyDate()
        date_to = self.date_to.date().toPyDate()

        visits = self.db_manager.get_all_visits()
        filtered_visits = []
        for visit in visits:
            visit_date = datetime.strptime(visit['date'], '%Y-%m-%d %H:%M:%S').date()
            if (customer_id == 0 or visit['customer_id'] == customer_id) and (date_from <= visit_date <= date_to):
                filtered_visits.append(visit)

        self.visits_table.setRowCount(0)
        for visit in filtered_visits:
            customer = self.db_manager.get_customer_by_id(visit['customer_id'])
            customer_name = f"{customer['first_name']} {customer['last_name']}"
            row_position = self.visits_table.rowCount()
            self.visits_table.insertRow(row_position)
            self.visits_table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(customer_name))
            self.visits_table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(visit['date']))
            self.visits_table.setItem(row_position, 2, QtWidgets.QTableWidgetItem(os.path.basename(visit['image_path'])))
            self.visits_table.setItem(row_position, 3, QtWidgets.QTableWidgetItem(visit['note']))

            # Actions (View Button)
            view_button = QtWidgets.QPushButton("Zobraziť")
            view_button.clicked.connect(lambda checked, v_id=visit['id']: self.view_visit(v_id))
            self.visits_table.setCellWidget(row_position, 4, view_button)

    def view_visit(self, visit_id):
        visit = self.db_manager.get_visit_by_id(visit_id)
        dialog = VisitDetailsDialog(self.db_manager, visit)
        dialog.exec_()

# Visit Details Dialog
class VisitDetailsDialog(QtWidgets.QDialog):
    def __init__(self, db_manager, visit):
        super().__init__()
        self.db_manager = db_manager
        self.visit = visit
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Detaily vizity")
        self.resize(800, 600)

        self.apply_dark_theme()

        layout = QtWidgets.QVBoxLayout()

        # Image display
        self.image_label = QtWidgets.QLabel()
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setFixedSize(640, 480)
        layout.addWidget(self.image_label)

        image = cv2.imread(self.visit['image_path'])
        if image is not None:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            height, width, channel = image.shape
            bytesPerLine = channel * width
            q_img = QtGui.QImage(image.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888)
            pixmap = QtGui.QPixmap.fromImage(q_img)
            # Scale pixmap to fit label size
            pixmap = pixmap.scaled(self.image_label.width(), self.image_label.height(), QtCore.Qt.KeepAspectRatio)
            self.image_label.setPixmap(pixmap)

        # Note
        self.note_field = QtWidgets.QTextEdit()
        self.note_field.setText(self.visit['note'])
        layout.addWidget(self.note_field)

        # Save button
        button_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("Uložiť poznámku")
        self.save_button.clicked.connect(self.save_note)
        self.close_button = QtWidgets.QPushButton("Zavrieť")
        self.close_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #2e2e2e;
            }
        """)

    def save_note(self):
        note = self.note_field.toPlainText()
        cursor = self.db_manager.conn.cursor()
        cursor.execute('UPDATE visits SET note = ? WHERE id = ?', (note, self.visit['id']))
        self.db_manager.conn.commit()
        QtWidgets.QMessageBox.information(self, "Úspech", "Poznámka bola úspešne uložená!")

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = PodoscopeApp()
    window.show()
    sys.exit(app.exec_())
