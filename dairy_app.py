from pathlib import Path
import sys
import sqlite3
import shutil
import os
from datetime import date

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QLineEdit,
    QDialog,
    QFormLayout,
    QMessageBox,
    QScrollArea,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog
)

from PySide6.QtCore import Qt


if sys.platform == "android":
    DATABASE = str(
        Path(
            os.environ.get(
                "ANDROID_PRIVATE",
                os.getcwd()
            )
        ) / "dairy_farm.db"
    )
else:
    DATABASE = "dairy_farm.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    return sqlite3.connect(DATABASE)


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_database():

    conn = get_connection()
    cur = conn.cursor()

    # -----------------------------------------------------
    # Animals
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS animals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id TEXT UNIQUE,
            name TEXT,
            breed TEXT,
            milk_per_day REAL
        )
    """)

    # -----------------------------------------------------
    # Milk Records
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS milk_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id TEXT,
            date TEXT,
            morning_milk REAL,
            evening_milk REAL,
            total_milk REAL
        )
    """)

    # -----------------------------------------------------
    # Milk Sales
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS milk_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT,
            liters REAL,
            price_per_liter REAL,
            total_amount REAL,
            customer_id INTEGER
        )
    """)

    # -----------------------------------------------------
    # Expenses
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date TEXT,
            category TEXT,
            amount REAL,
            note TEXT
        )
    """)

    # -----------------------------------------------------
    # Customers
    # -----------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            address TEXT
        )
    """)

    # -----------------------------------------------------
    # Make sure customer_id exists in old databases
    # -----------------------------------------------------

    try:
        cur.execute(
            "ALTER TABLE milk_sales ADD COLUMN customer_id INTEGER"
        )
    except sqlite3.OperationalError:
        pass

    # -----------------------------------------------------
    # Add 15 sample cows ONLY if database is empty
    # -----------------------------------------------------

    cur.execute("SELECT COUNT(*) FROM animals")

    count = cur.fetchone()[0]

    if count == 0:

        cows = [
            ("COW-001", "Bella", "Holstein", 22),
            ("COW-002", "Daisy", "Jersey", 20),
            ("COW-003", "Luna", "Holstein", 24),
            ("COW-004", "Molly", "Jersey", 19),
            ("COW-005", "Rosie", "Holstein", 23),
            ("COW-006", "Lucy", "Sahiwal", 18),
            ("COW-007", "Coco", "Holstein", 21),
            ("COW-008", "Maggie", "Jersey", 20),
            ("COW-009", "Nelly", "Sahiwal", 17),
            ("COW-010", "Ruby", "Holstein", 25),
            ("COW-011", "Lily", "Jersey", 19),
            ("COW-012", "Dolly", "Sahiwal", 18),
            ("COW-013", "Mia", "Holstein", 22),
            ("COW-014", "Gigi", "Jersey", 20),
            ("COW-015", "Emma", "Sahiwal", 17),
        ]

        cur.executemany("""
            INSERT INTO animals
            (animal_id, name, breed, milk_per_day)
            VALUES (?, ?, ?, ?)
        """, cows)

    conn.commit()
    conn.close()


# =========================================================
# BACKUP DATABASE
# =========================================================

def backup_database(parent=None):

    if not os.path.exists(DATABASE):

        QMessageBox.warning(
            parent,
            "Backup Error",
            "Database file was not found."
        )

        return

    filename, _ = QFileDialog.getSaveFileName(
        parent,
        "Save Database Backup",
        f"dairy_farm_backup_{date.today()}.db",
        "Database Files (*.db)"
    )

    if not filename:
        return

    try:

        shutil.copy2(
            DATABASE,
            filename
        )

        QMessageBox.information(
            parent,
            "Backup Complete",
            "Database backup created successfully!\n\n"
            f"Saved to:\n{filename}"
        )

    except Exception as e:

        QMessageBox.critical(
            parent,
            "Backup Error",
            f"Could not create backup.\n\n{str(e)}"
        )


# =========================================================
# RESTORE DATABASE
# =========================================================

def restore_database(parent=None):

    filename, _ = QFileDialog.getOpenFileName(
        parent,
        "Select Database Backup",
        "",
        "Database Files (*.db)"
    )

    if not filename:
        return

    if os.path.abspath(filename) == os.path.abspath(DATABASE):

        QMessageBox.warning(
            parent,
            "Invalid Backup",
            "Please select a backup file, not the current database."
        )

        return

    answer = QMessageBox.question(
        parent,
        "Restore Database",
        "Are you sure you want to restore this backup?\n\n"
        "Your current database will be replaced.\n\n"
        "A safety backup of the current database will be created first.",
        QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No
    )

    if answer != QMessageBox.StandardButton.Yes:
        return

    try:

        # Safety backup
        safety_backup = (
            f"dairy_farm_before_restore_{date.today()}.db"
        )

        shutil.copy2(
            DATABASE,
            safety_backup
        )

        # Restore selected backup
        shutil.copy2(
            filename,
            DATABASE
        )

        QMessageBox.information(
            parent,
            "Restore Complete",
            "Database restored successfully!\n\n"
            "The application will now close.\n\n"
            "Please open the app again."
        )

        QApplication.quit()

    except Exception as e:

        QMessageBox.critical(
            parent,
            "Restore Error",
            f"Could not restore database.\n\n{str(e)}"
        )


# =========================================================
# ANIMALS
# =========================================================

def load_animals_from_database(search=""):

    conn = get_connection()
    cur = conn.cursor()

    if search.strip():

        keyword = f"%{search.strip()}%"

        cur.execute("""
            SELECT id, animal_id, name, breed, milk_per_day
            FROM animals
            WHERE animal_id LIKE ?
               OR name LIKE ?
               OR breed LIKE ?
            ORDER BY id DESC
        """, (
            keyword,
            keyword,
            keyword
        ))

    else:

        cur.execute("""
            SELECT id, animal_id, name, breed, milk_per_day
            FROM animals
            ORDER BY id DESC
        """)

    rows = cur.fetchall()

    conn.close()

    return rows


def save_animal(
    animal_id,
    name,
    breed,
    milk_per_day
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO animals
        (animal_id, name, breed, milk_per_day)
        VALUES (?, ?, ?, ?)
    """, (
        animal_id,
        name,
        breed,
        milk_per_day
    ))

    conn.commit()
    conn.close()


def delete_animal(animal_db_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM animals WHERE id = ?",
        (animal_db_id,)
    )

    conn.commit()
    conn.close()


def update_animal(
    animal_db_id,
    animal_id,
    name,
    breed,
    milk_per_day
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE animals
        SET animal_id = ?,
            name = ?,
            breed = ?,
            milk_per_day = ?
        WHERE id = ?
    """, (
        animal_id,
        name,
        breed,
        milk_per_day,
        animal_db_id
    ))

    conn.commit()
    conn.close()


# =========================================================
# MILK
# =========================================================

def save_milk_record(
    animal_id,
    morning,
    evening
):

    total = morning + evening

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO milk_records
        (animal_id, date, morning_milk, evening_milk, total_milk)
        VALUES (?, ?, ?, ?, ?)
    """, (
        animal_id,
        str(date.today()),
        morning,
        evening,
        total
    ))

    conn.commit()
    conn.close()


def get_today_milk():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(total_milk), 0)
        FROM milk_records
        WHERE date = ?
    """, (
        str(date.today()),
    ))

    value = cur.fetchone()[0]

    conn.close()

    return value


def get_total_milk():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(total_milk), 0)
        FROM milk_records
    """)

    value = cur.fetchone()[0]

    conn.close()

    return value


def load_milk_records():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT animal_id,
               date,
               morning_milk,
               evening_milk,
               total_milk
        FROM milk_records
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


# =========================================================
# SALES
# =========================================================

def save_milk_sale(
    liters,
    price,
    customer_id=None
):

    total = liters * price

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO milk_sales
        (sale_date, liters, price_per_liter,
         total_amount, customer_id)
        VALUES (?, ?, ?, ?, ?)
    """, (
        str(date.today()),
        liters,
        price,
        total,
        customer_id
    ))

    conn.commit()
    conn.close()


def get_today_sales():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM milk_sales
        WHERE sale_date = ?
    """, (
        str(date.today()),
    ))

    value = cur.fetchone()[0]

    conn.close()

    return value


def get_total_sales():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM milk_sales
    """)

    value = cur.fetchone()[0]

    conn.close()

    return value


def load_milk_sales():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT sale_date,
               liters,
               price_per_liter,
               total_amount
        FROM milk_sales
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


# =========================================================
# EXPENSES
# =========================================================

def save_expense(
    category,
    amount,
    note
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO expenses
        (expense_date, category, amount, note)
        VALUES (?, ?, ?, ?)
    """, (
        str(date.today()),
        category,
        amount,
        note
    ))

    conn.commit()
    conn.close()


def get_today_expenses():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE expense_date = ?
    """, (
        str(date.today()),
    ))

    value = cur.fetchone()[0]

    conn.close()

    return value


def get_total_expenses():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
    """)

    value = cur.fetchone()[0]

    conn.close()

    return value


def load_expenses():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT expense_date,
               category,
               amount,
               note
        FROM expenses
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


# =========================================================
# CUSTOMERS
# =========================================================

def load_customers_from_database():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id,
               name,
               phone,
               address
        FROM customers
        ORDER BY id DESC
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


def save_customer(
    name,
    phone,
    address
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO customers
        (name, phone, address)
        VALUES (?, ?, ?)
    """, (
        name,
        phone,
        address
    ))

    conn.commit()
    conn.close()


def delete_customer_from_database(
    customer_id
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM customers WHERE id = ?",
        (customer_id,)
    )

    conn.commit()
    conn.close()


# =========================================================
# ANIMAL DIALOG
# =========================================================

class AddAnimalDialog(QDialog):

    def __init__(
        self,
        parent=None,
        animal=None
    ):

        super().__init__(parent)

        self.animal = animal

        self.setWindowTitle(
            "Edit Animal" if animal else "Add Animal"
        )

        self.setMinimumWidth(350)

        layout = QFormLayout()

        self.animal_id = QLineEdit()
        self.name = QLineEdit()

        self.breed = QComboBox()

        self.breed.addItems([
            "Holstein",
            "Jersey",
            "Sahiwal",
            "Friesian",
            "Cross Breed",
            "Other"
        ])

        self.milk = QDoubleSpinBox()

        self.milk.setRange(
            0,
            100
        )

        self.milk.setDecimals(1)
        self.milk.setSuffix(" L/day")

        layout.addRow(
            "Animal ID:",
            self.animal_id
        )

        layout.addRow(
            "Name:",
            self.name
        )

        layout.addRow(
            "Breed:",
            self.breed
        )

        layout.addRow(
            "Milk/Day:",
            self.milk
        )

        buttons = QHBoxLayout()

        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(
            self.accept
        )

        cancel_btn.clicked.connect(
            self.reject
        )

        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        layout.addRow(buttons)

        self.setLayout(layout)

        if animal:

            self.animal_id.setText(
                str(animal[1])
            )

            self.name.setText(
                str(animal[2])
            )

            index = self.breed.findText(
                str(animal[3])
            )

            if index >= 0:
                self.breed.setCurrentIndex(index)

            self.milk.setValue(
                float(animal[4] or 0)
            )


# =========================================================
# MILK DIALOG
# =========================================================

class AddMilkDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "Add Milk Record"
        )

        self.setMinimumWidth(350)

        layout = QFormLayout()

        self.animal = QComboBox()

        animals = load_animals_from_database()

        for row in animals:

            self.animal.addItem(
                f"{row[1]} - {row[2]}",
                row[1]
            )

        self.morning = QDoubleSpinBox()

        self.morning.setRange(
            0,
            100
        )

        self.morning.setDecimals(1)
        self.morning.setSuffix(" L")

        self.evening = QDoubleSpinBox()

        self.evening.setRange(
            0,
            100
        )

        self.evening.setDecimals(1)
        self.evening.setSuffix(" L")

        layout.addRow(
            "Animal:",
            self.animal
        )

        layout.addRow(
            "Morning Milk:",
            self.morning
        )

        layout.addRow(
            "Evening Milk:",
            self.evening
        )

        buttons = QHBoxLayout()

        save = QPushButton("Save")
        cancel = QPushButton("Cancel")

        save.clicked.connect(
            self.accept
        )

        cancel.clicked.connect(
            self.reject
        )

        buttons.addWidget(save)
        buttons.addWidget(cancel)

        layout.addRow(buttons)

        self.setLayout(layout)


# =========================================================
# SALE DIALOG
# =========================================================

class AddSaleDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "Record Milk Sale"
        )

        self.setMinimumWidth(350)

        layout = QFormLayout()

        self.customer = QComboBox()

        self.customer.addItem(
            "Walk-in Customer",
            None
        )

        customers = load_customers_from_database()

        for row in customers:

            self.customer.addItem(
                row[1],
                row[0]
            )

        self.liters = QDoubleSpinBox()

        self.liters.setRange(
            0,
            10000
        )

        self.liters.setDecimals(1)
        self.liters.setSuffix(" L")

        self.price = QDoubleSpinBox()

        self.price.setRange(
            0,
            10000
        )

        self.price.setDecimals(2)
        self.price.setValue(200)
        self.price.setPrefix("Rs. ")

        layout.addRow(
            "Customer:",
            self.customer
        )

        layout.addRow(
            "Milk:",
            self.liters
        )

        layout.addRow(
            "Price/Liter:",
            self.price
        )

        buttons = QHBoxLayout()

        save = QPushButton("Save")
        cancel = QPushButton("Cancel")

        save.clicked.connect(
            self.accept
        )

        cancel.clicked.connect(
            self.reject
        )

        buttons.addWidget(save)
        buttons.addWidget(cancel)

        layout.addRow(buttons)

        self.setLayout(layout)


# =========================================================
# EXPENSE DIALOG
# =========================================================

class AddExpenseDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "Add Expense"
        )

        self.setMinimumWidth(350)

        layout = QFormLayout()

        self.category = QComboBox()

        self.category.addItems([
            "Feed",
            "Medicine",
            "Labor",
            "Electricity",
            "Transport",
            "Maintenance",
            "Other"
        ])

        self.amount = QDoubleSpinBox()

        self.amount.setRange(
            0,
            10000000
        )

        self.amount.setDecimals(2)
        self.amount.setPrefix("Rs. ")

        self.note = QLineEdit()

        layout.addRow(
            "Category:",
            self.category
        )

        layout.addRow(
            "Amount:",
            self.amount
        )

        layout.addRow(
            "Note:",
            self.note
        )

        buttons = QHBoxLayout()

        save = QPushButton("Save")
        cancel = QPushButton("Cancel")

        save.clicked.connect(
            self.accept
        )

        cancel.clicked.connect(
            self.reject
        )

        buttons.addWidget(save)
        buttons.addWidget(cancel)

        layout.addRow(buttons)

        self.setLayout(layout)


# =========================================================
# CUSTOMER DIALOG
# =========================================================

class CustomerDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "Add Customer"
        )

        self.setMinimumWidth(350)

        layout = QFormLayout()

        self.name = QLineEdit()
        self.phone = QLineEdit()
        self.address = QLineEdit()

        layout.addRow(
            "Name:",
            self.name
        )

        layout.addRow(
            "Phone:",
            self.phone
        )

        layout.addRow(
            "Address:",
            self.address
        )

        buttons = QHBoxLayout()

        save = QPushButton("Save")
        cancel = QPushButton("Cancel")

        save.clicked.connect(
            self.accept
        )

        cancel.clicked.connect(
            self.reject
        )

        buttons.addWidget(save)
        buttons.addWidget(cancel)

        layout.addRow(buttons)

        self.setLayout(layout)


# =========================================================
# LOGIN SYSTEM
# =========================================================

class LoginDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle(
            "Dairy Farm Login"
        )

        self.setFixedSize(
            380,
            330
        )

        self.setStyleSheet("""
            QDialog {
                background: #f4f8f5;
            }

            QLabel {
                color: #17251d;
            }

            QLineEdit {
                background: white;
                border: 1px solid #cddbd1;
                border-radius: 10px;
                padding: 11px;
                font-size: 14px;
            }

            QPushButton {
                background: #159447;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #11783a;
            }
        """)

        layout = QVBoxLayout()

        layout.setContentsMargins(
            30,
            25,
            30,
            25
        )

        logo = QLabel("🐄")

        logo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        logo.setStyleSheet(
            "font-size: 48px;"
        )

        layout.addWidget(logo)

        title = QLabel(
            "Dairy Farm"
        )

        title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #159447;
        """)

        layout.addWidget(title)

        subtitle = QLabel(
            "Smart Farm Management System"
        )

        subtitle.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        subtitle.setStyleSheet("""
            color: #718078;
            font-size: 12px;
        """)

        layout.addWidget(subtitle)

        layout.addSpacing(15)

        self.username = QLineEdit()

        self.username.setPlaceholderText(
            "Enter username"
        )

        layout.addWidget(
            self.username
        )

        self.password = QLineEdit()

        self.password.setPlaceholderText(
            "Enter password"
        )

        self.password.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        layout.addWidget(
            self.password
        )

        layout.addSpacing(10)

        login_btn = QPushButton(
            "🔐 Login"
        )

        login_btn.clicked.connect(
            self.check_login
        )

        layout.addWidget(
            login_btn
        )

        hint = QLabel(
            "Username: Hafsa chaudhary   |   Password: Hs12345"
        )

        hint.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        hint.setStyleSheet("""
            color: #87958c;
            font-size: 11px;
            padding-top: 8px;
        """)

        layout.addWidget(
            hint
        )

        self.setLayout(layout)

    def check_login(self):

        username = self.username.text().strip()

        password = self.password.text()

        if (
            username == "Hafsa chaudhary"
            and
            password == "Hs12345"
        ):

            self.accept()

        else:

            QMessageBox.warning(
                self,
                "Login Failed",
                "Incorrect username or password."
            )

            self.password.clear()

            self.password.setFocus()


# =========================================================
# MAIN APP
# =========================================================

class DairyAppBuilder(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Dairy Farm App Builder"
        )

        self.resize(
            1100,
            700
        )

        self.setStyleSheet("""
            QMainWindow {
                background: #eef4ef;
            }

            QLabel {
                color: #1f2937;
            }

            QPushButton {
                background: #159447;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #11783a;
            }

            QLineEdit,
            QComboBox,
            QDoubleSpinBox {
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 8px;
                background: white;
            }

            QScrollArea {
                border: none;
                background: white;
            }
        """)

        # =================================================
        # MAIN AREA
        # =================================================

        main = QWidget()

        main_layout = QHBoxLayout(
            main
        )

        main_layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        # =================================================
        # LEFT PANEL
        # =================================================

        left = QFrame()

        left.setFixedWidth(
            300
        )

        left.setStyleSheet("""
            QFrame {
                background: #17251d;
                border-radius: 18px;
            }
        """)

        left_layout = QVBoxLayout(
            left
        )

        title = QLabel(
            "🐄 Dairy Farm"
        )

        title.setStyleSheet("""
            color: white;
            font-size: 28px;
            font-weight: bold;
        """)

        subtitle = QLabel(
            "Farm Management System"
        )

        subtitle.setStyleSheet("""
            color: #a7c9b0;
            font-size: 13px;
        """)

        left_layout.addWidget(title)
        left_layout.addWidget(subtitle)

        left_layout.addSpacing(25)

        info = QLabel(
            "Manage your animals,\n"
            "milk production,\n"
            "customers, sales\n"
            "and expenses."
        )

        info.setStyleSheet("""
            color: #d6e6da;
            font-size: 16px;
            line-height: 1.5;
        """)

        left_layout.addWidget(
            info
        )

        left_layout.addSpacing(25)

        # =================================================
        # BACKUP BUTTON
        # =================================================

        backup_btn = QPushButton(
            "💾 Backup Database"
        )

        backup_btn.clicked.connect(
            lambda: backup_database(self)
        )

        backup_btn.setStyleSheet("""
            QPushButton {
                background: #159447;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 11px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #11783a;
            }
        """)

        left_layout.addWidget(
            backup_btn
        )

        # =================================================
        # RESTORE BUTTON
        # =================================================

        restore_btn = QPushButton(
            "♻️ Restore Database"
        )

        restore_btn.clicked.connect(
            lambda: restore_database(self)
        )

        restore_btn.setStyleSheet("""
            QPushButton {
                background: #e8f5eb;
                color: #159447;
                border: none;
                border-radius: 10px;
                padding: 11px;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #d5eedb;
            }
        """)

        left_layout.addWidget(
            restore_btn
        )

        left_layout.addStretch()

        version = QLabel(
            "Dairy Farm App v1.0"
        )

        version.setStyleSheet(
            "color:#789681;"
        )

        left_layout.addWidget(
            version
        )

        # =================================================
        # PHONE AREA
        # =================================================

        phone = QFrame()

        phone.setFixedWidth(
            430
        )

        phone.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 25px;
                border: 1px solid #dbe5de;
            }
        """)

        phone_layout = QVBoxLayout(
            phone
        )

        phone_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        # =================================================
        # HEADER
        # =================================================

        header = QFrame()

        header.setStyleSheet("""
            QFrame {
                background: #159447;
                border-top-left-radius: 25px;
                border-top-right-radius: 25px;
                border: none;
            }
        """)

        header_layout = QVBoxLayout(
            header
        )

        header_title = QLabel(
            "🐄 Dairy Farm"
        )

        header_title.setStyleSheet("""
            color: white;
            font-size: 23px;
            font-weight: bold;
        """)

        header_subtitle = QLabel(
            "Smart Farm Management"
        )

        header_subtitle.setStyleSheet("""
            color: #d9f6e1;
            font-size: 12px;
        """)

        header_layout.addWidget(
            header_title
        )

        header_layout.addWidget(
            header_subtitle
        )

        phone_layout.addWidget(
            header
        )

        # =================================================
        # SCROLL AREA
        # =================================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.content = QWidget()

        self.content_layout = QVBoxLayout(
            self.content
        )

        self.content_layout.setContentsMargins(
            15,
            15,
            15,
            15
        )

        self.scroll.setWidget(
            self.content
        )

        phone_layout.addWidget(
            self.scroll
        )

        # =================================================
        # BOTTOM NAVIGATION
        # =================================================

        nav = QFrame()

        nav.setStyleSheet("""
            QFrame {
                background: #f7faf8;
                border-bottom-left-radius: 25px;
                border-bottom-right-radius: 25px;
                border: none;
            }
        """)

        nav_layout = QHBoxLayout(
            nav
        )

        buttons = [
            ("🏠\nHome", self.show_home),
            ("🐄\nAnimals", self.show_animals),
            ("👥\nCustomers", self.show_customers),
            ("🥛\nMilk", self.show_milk),
            ("📊\nReports", self.show_reports)
        ]

        for text, function in buttons:

            btn = QPushButton(
                text
            )

            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #34453b;
                    border-radius: 8px;
                    padding: 6px;
                }

                QPushButton:hover {
                    background: #dff2e5;
                    color: #159447;
                }
            """)

            btn.clicked.connect(
                function
            )

            nav_layout.addWidget(
                btn
            )

        phone_layout.addWidget(
            nav
        )

        main_layout.addWidget(
            left
        )

        main_layout.addWidget(
            phone
        )

        main_layout.addStretch()

        self.setCentralWidget(
            main
        )

        self.show_home()

    # =====================================================
    # CLEAR SCREEN
    # =====================================================

    def clear_content(self):

        while self.content_layout.count():

            item = self.content_layout.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

    # =====================================================
    # CARD
    # =====================================================

    def create_card(
        self,
        title,
        value
    ):

        card = QFrame()

        card.setStyleSheet("""
            QFrame {
                background: #f5faf6;
                border: 1px solid #dcebe0;
                border-radius: 14px;
            }
        """)

        layout = QVBoxLayout(
            card
        )

        title_label = QLabel(
            title
        )

        title_label.setStyleSheet("""
            color: #6b7280;
            font-size: 12px;
        """)

        value_label = QLabel(
            str(value)
        )

        value_label.setStyleSheet("""
            color: #159447;
            font-size: 24px;
            font-weight: bold;
        """)

        layout.addWidget(
            title_label
        )

        layout.addWidget(
            value_label
        )

        return card

    # =====================================================
    # HOME
    # =====================================================

    def show_home(self):

        self.clear_content()

        animals = load_animals_from_database()

        customers = load_customers_from_database()

        today_milk = get_today_milk()

        today_sales = get_today_sales()

        today_expenses = get_today_expenses()

        profit = (
            today_sales
            -
            today_expenses
        )

        welcome = QLabel(
            "Welcome back! 👋"
        )

        welcome.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #17251d;
        """)

        self.content_layout.addWidget(
            welcome
        )

        subtitle = QLabel(
            "Here's your farm overview today."
        )

        subtitle.setStyleSheet(
            "color:#718078;"
        )

        self.content_layout.addWidget(
            subtitle
        )

        self.content_layout.addSpacing(
            10
        )

        overview = QLabel(
            "Farm Overview"
        )

        overview.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
        """)

        self.content_layout.addWidget(
            overview
        )

        cards = [
            ("Animals", len(animals)),
            ("Customers", len(customers)),
            ("Today's Milk", f"{today_milk:.1f} L"),
            ("Today's Sales", f"Rs. {today_sales:,.0f}"),
            ("Today's Expenses", f"Rs. {today_expenses:,.0f}"),
            ("Today's Profit", f"Rs. {profit:,.0f}")
        ]

        for title, value in cards:

            self.content_layout.addWidget(
                self.create_card(
                    title,
                    value
                )
            )

        self.content_layout.addSpacing(
            10
        )

        quick = QLabel(
            "Quick Actions"
        )

        quick.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
        """)

        self.content_layout.addWidget(
            quick
        )

        milk_btn = QPushButton(
            "🥛 Add Milk Record"
        )

        milk_btn.clicked.connect(
            self.add_milk
        )

        sale_btn = QPushButton(
            "💰 Record Milk Sale"
        )

        sale_btn.clicked.connect(
            self.add_sale
        )

        expense_btn = QPushButton(
            "💸 Add Expense"
        )

        expense_btn.clicked.connect(
            self.add_expense
        )

        self.content_layout.addWidget(
            milk_btn
        )

        self.content_layout.addWidget(
            sale_btn
        )

        self.content_layout.addWidget(
            expense_btn
        )

        self.content_layout.addSpacing(
            10
        )

        status = QLabel(
            "Farm Status"
        )

        status.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
        """)

        self.content_layout.addWidget(
            status
        )

        total_text = QLabel(
            f"Total Milk: {get_total_milk():,.1f} L\n"
            f"Total Sales: Rs. {get_total_sales():,.0f}\n"
            f"Total Expenses: Rs. {get_total_expenses():,.0f}"
        )

        total_text.setStyleSheet("""
            background: #eff8f1;
            border-radius: 12px;
            padding: 14px;
            color: #355340;
        """)

        self.content_layout.addWidget(
            total_text
        )

        self.content_layout.addStretch()

    # =====================================================
    # ANIMALS
    # =====================================================

    def show_animals(self):

        self.clear_content()

        title = QLabel(
            "🐄 Animals"
        )

        title.setStyleSheet("""
            font-size: 23px;
            font-weight: bold;
        """)

        self.content_layout.addWidget(
            title
        )

        self.animal_search = QLineEdit()

        self.animal_search.setPlaceholderText(
            "🔍 Search animal, ID or breed..."
        )

        self.animal_search.textChanged.connect(
            self.refresh_animals
        )

        self.content_layout.addWidget(
            self.animal_search
        )

        add_btn = QPushButton(
            "➕ Add New Animal"
        )

        add_btn.clicked.connect(
            self.add_animal
        )

        self.content_layout.addWidget(
            add_btn
        )

        self.animals_container = QWidget()

        self.animals_layout = QVBoxLayout(
            self.animals_container
        )

        self.animals_layout.setContentsMargins(
            0,
            10,
            0,
            0
        )

        self.content_layout.addWidget(
            self.animals_container
        )

        self.refresh_animals()

        self.content_layout.addStretch()

    def refresh_animals(self):

        if not hasattr(
            self,
            "animals_layout"
        ):
            return

        while self.animals_layout.count():

            item = self.animals_layout.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

        search = ""

        if hasattr(
            self,
            "animal_search"
        ):

            search = self.animal_search.text()

        animals = load_animals_from_database(
            search
        )

        if not animals:

            empty = QLabel(
                "No animals found.\n\n"
                "Click 'Add New Animal' to add an animal."
            )

            empty.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            empty.setStyleSheet("""
                color: #7a8a81;
                padding: 30px;
                font-size: 14px;
            """)

            self.animals_layout.addWidget(
                empty
            )

            return

        for animal in animals:

            db_id = animal[0]

            animal_id = animal[1]

            name = animal[2]

            breed = animal[3]

            milk = animal[4]

            card = QFrame()

            card.setStyleSheet("""
                QFrame {
                    background: #f8fbf9;
                    border: 1px solid #dce9df;
                    border-radius: 14px;
                }
            """)

            layout = QVBoxLayout(
                card
            )

            name_label = QLabel(
                f"🐄 {name}"
            )

            name_label.setStyleSheet("""
                font-size: 18px;
                font-weight: bold;
                color: #17251d;
            """)

            id_label = QLabel(
                f"ID: {animal_id}"
            )

            id_label.setStyleSheet(
                "color:#6b7280;"
            )

            breed_label = QLabel(
                f"Breed: {breed}"
            )

            milk_label = QLabel(
                f"🥛 Milk/Day: {float(milk):.1f} L"
            )

            milk_label.setStyleSheet("""
                color: #159447;
                font-weight: bold;
            """)

            layout.addWidget(
                name_label
            )

            layout.addWidget(
                id_label
            )

            layout.addWidget(
                breed_label
            )

            layout.addWidget(
                milk_label
            )

            buttons = QHBoxLayout()

            edit_btn = QPushButton(
                "✏️ Edit"
            )

            delete_btn = QPushButton(
                "🗑 Delete"
            )

            edit_btn.setStyleSheet("""
                QPushButton {
                    background:#e8f5eb;
                    color:#159447;
                }
            """)

            delete_btn.setStyleSheet("""
                QPushButton {
                    background:#ffe9e9;
                    color:#d33;
                }
            """)

            edit_btn.clicked.connect(
                lambda checked=False,
                a=animal:
                self.edit_animal(a)
            )

            delete_btn.clicked.connect(
                lambda checked=False,
                a=db_id:
                self.delete_animal(a)
            )

            buttons.addWidget(
                edit_btn
            )

            buttons.addWidget(
                delete_btn
            )

            layout.addLayout(
                buttons
            )

            self.animals_layout.addWidget(
                card
            )

    # =====================================================
    # ADD ANIMAL
    # =====================================================

    def add_animal(self):

        dialog = AddAnimalDialog(
            self
        )

        if dialog.exec():

            animal_id = (
                dialog.animal_id.text()
                .strip()
            )

            name = (
                dialog.name.text()
                .strip()
            )

            breed = (
                dialog.breed.currentText()
            )

            milk = (
                dialog.milk.value()
            )

            if not animal_id or not name:

                QMessageBox.warning(
                    self,
                    "Missing Information",
                    "Please enter Animal ID and Name."
                )

                return

            try:

                save_animal(
                    animal_id,
                    name,
                    breed,
                    milk
                )

                QMessageBox.information(
                    self,
                    "Success",
                    "Animal added successfully! 🐄"
                )

                self.show_animals()

            except sqlite3.IntegrityError:

                QMessageBox.warning(
                    self,
                    "Duplicate ID",
                    "This Animal ID already exists."
                )

    # =====================================================
    # EDIT ANIMAL
    # =====================================================

    def edit_animal(
        self,
        animal
    ):

        dialog = AddAnimalDialog(
            self,
            animal
        )

        if dialog.exec():

            try:

                update_animal(
                    animal[0],
                    dialog.animal_id.text().strip(),
                    dialog.name.text().strip(),
                    dialog.breed.currentText(),
                    dialog.milk.value()
                )

                QMessageBox.information(
                    self,
                    "Updated",
                    "Animal updated successfully."
                )

                self.show_animals()

            except sqlite3.IntegrityError:

                QMessageBox.warning(
                    self,
                    "Error",
                    "Animal ID already exists."
                )

    # =====================================================
    # DELETE ANIMAL
    # =====================================================

    def delete_animal(
        self,
        animal_id
    ):

        answer = QMessageBox.question(
            self,
            "Delete Animal",
            "Are you sure you want to delete this animal?"
        )

        if answer == QMessageBox.StandardButton.Yes:

            delete_animal(
                animal_id
            )

            self.show_animals()

    # =====================================================
    # CUSTOMERS
    # =====================================================

    def show_customers(self):

        self.clear_content()

        title = QLabel(
            "👥 Customers"
        )

        title.setStyleSheet("""
            font-size: 23px;
            font-weight: bold;
        """)

        self.content_layout.addWidget(
            title
        )

        add_btn = QPushButton(
            "➕ Add Customer"
        )

        add_btn.clicked.connect(
            self.add_customer
        )

        self.content_layout.addWidget(
            add_btn
        )

        customers = (
            load_customers_from_database()
        )

        if not customers:

            label = QLabel(
                "No customers added yet."
            )

            label.setStyleSheet(
                "color:#7b8b82; padding:20px;"
            )

            self.content_layout.addWidget(
                label
            )

        for customer in customers:

            card = QFrame()

            card.setStyleSheet("""
                QFrame {
                    background:#f8fbf9;
                    border:1px solid #dce9df;
                    border-radius:14px;
                }
            """)

            layout = QVBoxLayout(
                card
            )

            name = QLabel(
                f"👤 {customer[1]}"
            )

            name.setStyleSheet("""
                font-size:18px;
                font-weight:bold;
            """)

            phone = QLabel(
                f"📞 {customer[2] or 'No phone'}"
            )

            address = QLabel(
                f"📍 {customer[3] or 'No address'}"
            )

            layout.addWidget(
                name
            )

            layout.addWidget(
                phone
            )

            layout.addWidget(
                address
            )

            delete_btn = QPushButton(
                "🗑 Delete"
            )

            delete_btn.setStyleSheet("""
                QPushButton {
                    background:#ffe9e9;
                    color:#d33;
                }
            """)

            delete_btn.clicked.connect(
                lambda checked=False,
                cid=customer[0]:
                self.delete_customer(cid)
            )

            layout.addWidget(
                delete_btn
            )

            self.content_layout.addWidget(
                card
            )

        self.content_layout.addStretch()

    def add_customer(self):

        dialog = CustomerDialog(
            self
        )

        if dialog.exec():

            name = (
                dialog.name.text()
                .strip()
            )

            phone = (
                dialog.phone.text()
                .strip()
            )

            address = (
                dialog.address.text()
                .strip()
            )

            if not name:

                QMessageBox.warning(
                    self,
                    "Missing Name",
                    "Please enter customer name."
                )

                return

            save_customer(
                name,
                phone,
                address
            )

            QMessageBox.information(
                self,
                "Success",
                "Customer added successfully."
            )

            self.show_customers()

    def delete_customer(
        self,
        customer_id
    ):

        answer = QMessageBox.question(
            self,
            "Delete Customer",
            "Delete this customer?"
        )

        if answer == QMessageBox.StandardButton.Yes:

            delete_customer_from_database(
                customer_id
            )

            self.show_customers()

    # =====================================================
    # MILK
    # =====================================================

    def show_milk(self):

        self.clear_content()

        title = QLabel(
            "🥛 Milk Production"
        )

        title.setStyleSheet("""
            font-size:23px;
            font-weight:bold;
        """)

        self.content_layout.addWidget(
            title
        )

        add_btn = QPushButton(
            "➕ Add Milk Record"
        )

        add_btn.clicked.connect(
            self.add_milk
        )

        self.content_layout.addWidget(
            add_btn
        )

        total = QLabel(
            f"Today's Milk: {get_today_milk():.1f} L"
        )

        total.setStyleSheet("""
            background:#eaf7ed;
            color:#159447;
            padding:15px;
            border-radius:12px;
            font-size:18px;
            font-weight:bold;
        """)

        self.content_layout.addWidget(
            total
        )

        records = (
            load_milk_records()
        )

        for row in records:

            card = QFrame()

            card.setStyleSheet("""
                QFrame {
                    background:#f8fbf9;
                    border:1px solid #dce9df;
                    border-radius:12px;
                }
            """)

            layout = QVBoxLayout(
                card
            )

            layout.addWidget(
                QLabel(
                    f"🐄 {row[0]}   •   {row[1]}"
                )
            )

            layout.addWidget(
                QLabel(
                    f"Morning: {row[2]:.1f} L"
                )
            )

            layout.addWidget(
                QLabel(
                    f"Evening: {row[3]:.1f} L"
                )
            )

            total_label = QLabel(
                f"Total: {row[4]:.1f} L"
            )

            total_label.setStyleSheet("""
                color:#159447;
                font-weight:bold;
            """)

            layout.addWidget(
                total_label
            )

            self.content_layout.addWidget(
                card
            )

        self.content_layout.addStretch()

    def add_milk(self):

        animals = (
            load_animals_from_database()
        )

        if not animals:

            QMessageBox.warning(
                self,
                "No Animals",
                "Please add an animal first."
            )

            return

        dialog = AddMilkDialog(
            self
        )

        if dialog.exec():

            animal_id = (
                dialog.animal.currentData()
            )

            morning = (
                dialog.morning.value()
            )

            evening = (
                dialog.evening.value()
            )

            save_milk_record(
                animal_id,
                morning,
                evening
            )

            QMessageBox.information(
                self,
                "Saved",
                "Milk record saved successfully."
            )

            self.show_milk()

    # =====================================================
    # SALES
    # =====================================================

    def add_sale(self):

        dialog = AddSaleDialog(
            self
        )

        if dialog.exec():

            liters = (
                dialog.liters.value()
            )

            price = (
                dialog.price.value()
            )

            customer_id = (
                dialog.customer.currentData()
            )

            if liters <= 0:

                QMessageBox.warning(
                    self,
                    "Invalid",
                    "Enter milk quantity."
                )

                return

            save_milk_sale(
                liters,
                price,
                customer_id
            )

            total = (
                liters * price
            )

            QMessageBox.information(
                self,
                "Sale Saved",
                f"Milk sale saved.\n\n"
                f"Total: Rs. {total:,.0f}"
            )

            self.show_home()

    # =====================================================
    # EXPENSES
    # =====================================================

    def show_expenses(self):

        self.clear_content()

        title = QLabel(
            "💸 Expenses"
        )

        title.setStyleSheet("""
            font-size:23px;
            font-weight:bold;
        """)

        self.content_layout.addWidget(
            title
        )

        add_btn = QPushButton(
            "➕ Add Expense"
        )

        add_btn.clicked.connect(
            self.add_expense
        )

        self.content_layout.addWidget(
            add_btn
        )

        total = QLabel(
            f"Total Expenses: "
            f"Rs. {get_total_expenses():,.0f}"
        )

        total.setStyleSheet("""
            background:#fff6e8;
            padding:15px;
            border-radius:12px;
            font-size:18px;
            font-weight:bold;
        """)

        self.content_layout.addWidget(
            total
        )

        expenses = (
            load_expenses()
        )

        for row in expenses:

            card = QFrame()

            card.setStyleSheet("""
                QFrame {
                    background:#f8fbf9;
                    border:1px solid #dce9df;
                    border-radius:12px;
                }
            """)

            layout = QVBoxLayout(
                card
            )

            layout.addWidget(
                QLabel(
                    f"💸 {row[1]}   •   {row[0]}"
                )
            )

            amount = QLabel(
                f"Rs. {row[2]:,.0f}"
            )

            amount.setStyleSheet("""
                color:#d97706;
                font-size:17px;
                font-weight:bold;
            """)

            layout.addWidget(
                amount
            )

            if row[3]:

                layout.addWidget(
                    QLabel(
                        str(row[3])
                    )
                )

            self.content_layout.addWidget(
                card
            )

        self.content_layout.addStretch()

    def add_expense(self):

        dialog = AddExpenseDialog(
            self
        )

        if dialog.exec():

            category = (
                dialog.category.currentText()
            )

            amount = (
                dialog.amount.value()
            )

            note = (
                dialog.note.text()
                .strip()
            )

            if amount <= 0:

                QMessageBox.warning(
                    self,
                    "Invalid Amount",
                    "Enter expense amount."
                )

                return

            save_expense(
                category,
                amount,
                note
            )

            QMessageBox.information(
                self,
                "Saved",
                "Expense saved successfully."
            )

            self.show_expenses()

    # =====================================================
    # REPORTS
    # =====================================================

    def show_reports(self):

        self.clear_content()

        title = QLabel(
            "📊 Reports"
        )

        title.setStyleSheet("""
            font-size:23px;
            font-weight:bold;
        """)

        self.content_layout.addWidget(
            title
        )

        self.content_layout.addWidget(
            self.create_card(
                "Total Milk",
                f"{get_total_milk():,.1f} L"
            )
        )

        self.content_layout.addWidget(
            self.create_card(
                "Total Sales",
                f"Rs. {get_total_sales():,.0f}"
            )
        )

        self.content_layout.addWidget(
            self.create_card(
                "Total Expenses",
                f"Rs. {get_total_expenses():,.0f}"
            )
        )

        profit = (
            get_total_sales()
            -
            get_total_expenses()
        )

        self.content_layout.addWidget(
            self.create_card(
                "Estimated Profit",
                f"Rs. {profit:,.0f}"
            )
        )

        self.content_layout.addSpacing(
            10
        )

        milk_title = QLabel(
            "Recent Milk Sales"
        )

        milk_title.setStyleSheet("""
            font-size:17px;
            font-weight:bold;
        """)

        self.content_layout.addWidget(
            milk_title
        )

        sales = (
            load_milk_sales()
        )

        if not sales:

            self.content_layout.addWidget(
                QLabel(
                    "No milk sales recorded yet."
                )
            )

        for row in sales:

            self.content_layout.addWidget(
                QLabel(
                    f"📅 {row[0]}   |   "
                    f"{row[1]:.1f} L   |   "
                    f"Rs. {row[3]:,.0f}"
                )
            )

        self.content_layout.addSpacing(
            15
        )

        expense_title = QLabel(
            "Recent Expenses"
        )

        expense_title.setStyleSheet("""
            font-size:17px;
            font-weight:bold;
        """)

        self.content_layout.addWidget(
            expense_title
        )

        expenses = (
            load_expenses()
        )

        if not expenses:

            self.content_layout.addWidget(
                QLabel(
                    "No expenses recorded yet."
                )
            )

        for row in expenses:

            self.content_layout.addWidget(
                QLabel(
                    f"📅 {row[0]}   |   "
                    f"{row[1]}   |   "
                    f"Rs. {row[2]:,.0f}"
                )
            )

        self.content_layout.addStretch()

    # =====================================================
    # EXPENSE NAVIGATION
    # =====================================================

    def show_expenses_page(self):

        self.show_expenses()


# =========================================================
# START APP WITH LOGIN
# =========================================================

if __name__ == "__main__":

    # Initialize existing database
    init_database()

    # Start application
    app = QApplication(sys.argv)

    # Show login first
    login = LoginDialog()

    if login.exec():

        # Login successful
        window = DairyAppBuilder()

        window.show()

        sys.exit(
            app.exec()
        )

    else:

        # Login cancelled
        sys.exit(0)