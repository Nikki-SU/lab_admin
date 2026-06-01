#!/usr/bin/env python3
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QSplitter,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QMenu, QStatusBar
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QAction
import requests
from datetime import datetime
import json


class APIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.token = None
        self.headers = {}
    
    def login(self, username, password):
        response = requests.post(
            f"{self.base_url}/api/auth/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            return True
        return False
    
    def get_current_user(self):
        response = requests.get(
            f"{self.base_url}/api/users/me",
            headers=self.headers
        )
        if response.status_code == 200:
            return response.json()
        return None
    
    def get_data_files(self, mode="person"):
        response = requests.get(
            f"{self.base_url}/api/files/data",
            headers=self.headers,
            params={"mode": mode}
        )
        if response.status_code == 200:
            return response.json()
        return {"files": [], "total": 0}
    
    def get_collab_files(self, mode="date"):
        response = requests.get(
            f"{self.base_url}/api/files/collab",
            headers=self.headers,
            params={"mode": mode}
        )
        if response.status_code == 200:
            return response.json()
        return {"files": [], "total": 0}
    
    def get_edited_files(self):
        response = requests.get(
            f"{self.base_url}/api/files/edited",
            headers=self.headers
        )
        if response.status_code == 200:
            return response.json()
        return {"files": [], "total": 0}
    
    def upload_data_file(self, filepath, operator_id=None):
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            files = {'file': f}
            data = {}
            if operator_id:
                data['operator_id'] = operator_id
            
            response = requests.post(
                f"{self.base_url}/api/files/upload/data",
                headers=self.headers,
                files=files,
                data=data
            )
        return response.status_code == 200
    
    def upload_collab_file(self, filepath):
        filename = os.path.basename(filepath)
        with open(filepath, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.base_url}/api/files/upload/collab",
                headers=self.headers,
                files=files
            )
        return response.status_code == 200
    
    def download_file(self, file_id, save_path):
        response = requests.get(
            f"{self.base_url}/api/files/download/{file_id}",
            headers=self.headers,
            stream=True
        )
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        return False
    
    def get_logs(self):
        response = requests.get(
            f"{self.base_url}/api/logs/my",
            headers=self.headers
        )
        if response.status_code == 200:
            return response.json()
        return []


class LoginWindow(QWidget):
    logged_in = pyqtSignal(str)
    
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("LabVault - Login")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("LabVault")
        title.setStyleSheet("font-size: 32px; font-weight: bold; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        form_layout = QVBoxLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(40)
        form_layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        form_layout.addWidget(self.password_input)
        
        login_btn = QPushButton("Login")
        login_btn.setMinimumHeight(40)
        login_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px;")
        login_btn.clicked.connect(self.login)
        form_layout.addWidget(login_btn)
        
        layout.addLayout(form_layout)
        self.setLayout(layout)
    
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if self.api.login(username, password):
            self.logged_in.emit(username)
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password")


class DataFilesTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.current_mode = "person"
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.person_mode_btn = QPushButton("👤 Person Mode")
        self.person_mode_btn.setCheckable(True)
        self.person_mode_btn.setChecked(True)
        self.person_mode_btn.clicked.connect(lambda: self.switch_mode("person"))
        
        self.experiment_mode_btn = QPushButton("🔬 Experiment Mode")
        self.experiment_mode_btn.setCheckable(True)
        self.experiment_mode_btn.clicked.connect(lambda: self.switch_mode("experiment"))
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        
        upload_btn = QPushButton("📤 Upload")
        upload_btn.clicked.connect(self.upload_file)
        
        toolbar.addWidget(self.person_mode_btn)
        toolbar.addWidget(self.experiment_mode_btn)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(upload_btn)
        
        layout.addLayout(toolbar)
        
        # File table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Filename", "Owner", "Type", "Uploaded", "Edited", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        self.refresh()
    
    def switch_mode(self, mode):
        self.current_mode = mode
        self.person_mode_btn.setChecked(mode == "person")
        self.experiment_mode_btn.setChecked(mode == "experiment")
        self.refresh()
    
    def refresh(self):
        data = self.api.get_data_files(self.current_mode)
        self.populate_table(data["files"])
    
    def populate_table(self, files):
        self.table.setRowCount(0)
        
        for row, file in enumerate(files):
            self.table.insertRow(row)
            
            filename_item = QTableWidgetItem(file["name"])
            if file["edited"]:
                filename_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 0, filename_item)
            
            self.table.setItem(row, 1, QTableWidgetItem(file["owner_id"]))
            self.table.setItem(row, 2, QTableWidgetItem(
                file.get("metadata", {}).get("experiment_type", "N/A")
            ))
            
            upload_time = file["upload_time"].split("T")[0] if "T" in file["upload_time"] else file["upload_time"]
            self.table.setItem(row, 3, QTableWidgetItem(upload_time))
            self.table.setItem(row, 4, QTableWidgetItem("Yes" if file["edited"] else "No"))
            
            download_btn = QPushButton("Download")
            download_btn.clicked.connect(lambda _, f=file: self.download_file(f))
            self.table.setCellWidget(row, 5, download_btn)
    
    def upload_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select File")
        if filepath:
            if self.api.upload_data_file(filepath):
                QMessageBox.information(self, "Success", "File uploaded successfully!")
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", "Failed to upload file. Please check filename format.")
    
    def download_file(self, file):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", file["name"])
        if save_path:
            if self.api.download_file(file["id"], save_path):
                QMessageBox.information(self, "Success", "File downloaded successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to download file")


class CollabFilesTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.current_mode = "date"
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.person_mode_btn = QPushButton("👤 Person Mode")
        self.person_mode_btn.setCheckable(True)
        self.person_mode_btn.clicked.connect(lambda: self.switch_mode("person"))
        
        self.date_mode_btn = QPushButton("📅 Date Mode")
        self.date_mode_btn.setCheckable(True)
        self.date_mode_btn.setChecked(True)
        self.date_mode_btn.clicked.connect(lambda: self.switch_mode("date"))
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        
        upload_btn = QPushButton("📤 Upload")
        upload_btn.clicked.connect(self.upload_file)
        
        toolbar.addWidget(self.person_mode_btn)
        toolbar.addWidget(self.date_mode_btn)
        toolbar.addStretch()
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(upload_btn)
        
        layout.addLayout(toolbar)
        
        # File table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Filename", "Uploader", "Size", "Uploaded", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        self.refresh()
    
    def switch_mode(self, mode):
        self.current_mode = mode
        self.person_mode_btn.setChecked(mode == "person")
        self.date_mode_btn.setChecked(mode == "date")
        self.refresh()
    
    def refresh(self):
        data = self.api.get_collab_files(self.current_mode)
        self.populate_table(data["files"])
    
    def populate_table(self, files):
        self.table.setRowCount(0)
        
        for row, file in enumerate(files):
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(file["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(file["owner_id"]))
            
            size_mb = file["size"] / (1024 * 1024) if file["size"] else 0
            self.table.setItem(row, 2, QTableWidgetItem(f"{size_mb:.2f} MB"))
            
            upload_time = file["upload_time"].split("T")[0] if "T" in file["upload_time"] else file["upload_time"]
            self.table.setItem(row, 3, QTableWidgetItem(upload_time))
            
            download_btn = QPushButton("Download")
            download_btn.clicked.connect(lambda _, f=file: self.download_file(f))
            self.table.setCellWidget(row, 4, download_btn)
    
    def upload_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Select File")
        if filepath:
            if self.api.upload_collab_file(filepath):
                QMessageBox.information(self, "Success", "File uploaded successfully!")
                self.refresh()
            else:
                QMessageBox.warning(self, "Error", "Failed to upload file")
    
    def download_file(self, file):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", file["name"])
        if save_path:
            if self.api.download_file(file["id"], save_path):
                QMessageBox.information(self, "Success", "File downloaded successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to download file")


class EditedFilesTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        info = QLabel("⚠️ These files have been edited and do not have system trust endorsement")
        info.setStyleSheet("color: #d32f2f; font-weight: bold; padding: 10px; background-color: #ffebee;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        toolbar = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Filename", "Owner", "Edit Count", "Uploaded", "Original", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("QTableWidget { background-color: #fff3e0; }")
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        self.refresh()
    
    def refresh(self):
        data = self.api.get_edited_files()
        self.populate_table(data["files"])
    
    def populate_table(self, files):
        self.table.setRowCount(0)
        
        for row, file in enumerate(files):
            self.table.insertRow(row)
            
            filename_item = QTableWidgetItem(f"⚠️ {file['name']}")
            filename_item.setForeground(Qt.GlobalColor.red)
            filename_item.setFont(filename_item.font())
            filename_item.font().setBold(True)
            self.table.setItem(row, 0, filename_item)
            
            self.table.setItem(row, 1, QTableWidgetItem(file["owner_id"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(file["edit_count"])))
            
            upload_time = file["upload_time"].split("T")[0] if "T" in file["upload_time"] else file["upload_time"]
            self.table.setItem(row, 3, QTableWidgetItem(upload_time))
            
            has_original = "Yes" if file.get("original_file_id") else "No"
            self.table.setItem(row, 4, QTableWidgetItem(has_original))
            
            download_btn = QPushButton("Download")
            download_btn.clicked.connect(lambda _, f=file: self.download_file(f))
            self.table.setCellWidget(row, 5, download_btn)
    
    def download_file(self, file):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", file["name"])
        if save_path:
            if self.api.download_file(file["id"], save_path):
                QMessageBox.information(self, "Success", "File downloaded successfully!")
            else:
                QMessageBox.warning(self, "Error", "Failed to download file")


class LogsTab(QWidget):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Operator", "Location", "Action", "Detail"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        self.refresh()
    
    def refresh(self):
        logs = self.api.get_logs()
        self.populate_table(logs)
    
    def populate_table(self, logs):
        self.table.setRowCount(0)
        
        for row, log in enumerate(logs):
            self.table.insertRow(row)
            
            ts = log["timestamp"].replace("T", " ").split(".")[0] if "T" in log["timestamp"] else log["timestamp"]
            self.table.setItem(row, 0, QTableWidgetItem(ts))
            self.table.setItem(row, 1, QTableWidgetItem(log["operator"]))
            self.table.setItem(row, 2, QTableWidgetItem(log["location"]))
            self.table.setItem(row, 3, QTableWidgetItem(log["action"]))
            self.table.setItem(row, 4, QTableWidgetItem(log["detail"]))


class MainWindow(QMainWindow):
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.init_ui()
    
    def init_ui(self):
        user = self.api.get_current_user()
        username = user.get("name", user.get("id", "User")) if user else "User"
        
        self.setWindowTitle(f"LabVault - {username}")
        self.setMinimumSize(1000, 700)
        
        # Create tabs
        tabs = QTabWidget()
        
        self.data_tab = DataFilesTab(self.api)
        self.collab_tab = CollabFilesTab(self.api)
        self.edited_tab = EditedFilesTab(self.api)
        self.logs_tab = LogsTab(self.api)
        
        tabs.addTab(self.data_tab, "📊 Data Files")
        tabs.addTab(self.collab_tab, "👥 Collaboration")
        tabs.addTab(self.edited_tab, "⚠️ Edited Files")
        tabs.addTab(self.logs_tab, "📜 Logs")
        
        self.setCentralWidget(tabs)
        
        # Status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Connected to LabVault")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    api = APIClient()
    
    login_window = LoginWindow(api)
    
    def on_login(username):
        login_window.close()
        main_window = MainWindow(api)
        main_window.show()
    
    login_window.logged_in.connect(on_login)
    login_window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
