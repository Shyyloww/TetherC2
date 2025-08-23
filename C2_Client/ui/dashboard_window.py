# C2_Client/ui/dashboard_window.py
import re
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QSplitter, QVBoxLayout,
                             QLabel, QPushButton, QMessageBox, QCheckBox,
                             QScrollArea, QApplication, QStackedWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QParallelAnimationGroup
from PyQt6.QtGui import QPixmap, QPainter
from ui.builder_pane import BuilderPane
from ui.options_pane import OptionsPane
from ui.animated_spinner import AnimatedSpinner

class SessionsPanelWidget(QWidget):
    # This widget now only handles the custom background painting.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SessionsPanel")
        self.background_pixmap = QPixmap()

    def update_background_icon(self, theme_name):
        sanitized_name = re.sub(r'[\s()]', '_', theme_name).replace('__', '_').strip('_')
        icon_path = f"session_icons/{sanitized_name}_icon.png"
        original_pixmap = QPixmap(icon_path)
        if not original_pixmap.isNull():
            new_width = int(original_pixmap.width() * 0.5)
            self.background_pixmap = original_pixmap.scaledToWidth(new_width, Qt.TransformationMode.SmoothTransformation)
        else:
            fallback_pixmap = QPixmap("session_icons/Dark_Default_icon.png")
            if not fallback_pixmap.isNull():
                new_width = int(fallback_pixmap.width() * 0.5)
                self.background_pixmap = fallback_pixmap.scaledToWidth(new_width, Qt.TransformationMode.SmoothTransformation)
            else:
                self.background_pixmap = QPixmap()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background_pixmap.isNull():
            center_x = self.rect().width() // 2
            center_y = self.rect().height() // 2
            x = center_x - (self.background_pixmap.width() // 2)
            y = center_y - (self.background_pixmap.height() // 2)
            painter.drawPixmap(x, y, self.background_pixmap)

class DashboardWindow(QWidget):
    build_requested = pyqtSignal(dict)
    sign_out_requested = pyqtSignal()
    setting_changed = pyqtSignal(str, object)
    session_interact_requested = pyqtSignal(str, dict, str)
    data_updated_for_session = pyqtSignal(str, str, dict)
    stop_build_requested = pyqtSignal()

    def __init__(self, api_client, db_manager, username):
        super().__init__()
        self.api = api_client
        self.db = db_manager
        self.username = username
        self.sessions = {}
        self.session_widgets = {}
        self.active_animations = []
        self.countdown_seconds = 30
        self.is_refreshing = False

        main_layout = QHBoxLayout(self)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.splitter)
        
        self.builder_pane = BuilderPane(self.db)
        self.builder_pane.build_requested.connect(self.build_requested)
        self.builder_pane.stop_build_requested.connect(self.stop_build_requested.emit)
        
        # --- OVERHAULED SESSION PANEL LAYOUT ---
        self.sessions_panel_container = QWidget()
        sessions_panel_layout = QVBoxLayout(self.sessions_panel_container)
        sessions_panel_layout.setContentsMargins(10,10,10,10)

        sessions_header_layout = QHBoxLayout()
        sessions_header_layout.addWidget(QLabel("<h2>SESSIONS</h2>"))
        sessions_header_layout.addStretch()
        self.auto_refresh_checkbox = QCheckBox("Auto Refresh")
        self.auto_refresh_checkbox.setChecked(True)
        self.countdown_label = QLabel(f"Next in: {self.countdown_seconds}s")
        sessions_header_layout.addWidget(self.auto_refresh_checkbox)
        sessions_header_layout.addWidget(self.countdown_label)
        self.refresh_button = QPushButton("Refresh Now")
        self.refresh_button.setFixedWidth(110)
        self.refresh_button.clicked.connect(self.refresh_all_data)
        sessions_header_layout.addWidget(self.refresh_button)
        sessions_panel_layout.addLayout(sessions_header_layout)

        self.header_widget = self._create_header_widget()
        sessions_panel_layout.addWidget(self.header_widget)
        
        # Use QStackedWidget to manage session list vs loading screen
        self.content_stack = QStackedWidget()
        sessions_panel_layout.addWidget(self.content_stack)

        # Page 0: Session List
        self.session_list_page = SessionsPanelWidget()
        session_list_page_layout = QVBoxLayout(self.session_list_page)
        session_list_page_layout.setContentsMargins(0,0,0,0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.sessions_frame = QWidget()
        self.sessions_frame.setStyleSheet("background: transparent;")
        self.sessions_frame_layout = QVBoxLayout(self.sessions_frame)
        self.sessions_frame_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.sessions_frame_layout.setSpacing(8)
        self.scroll_area.setWidget(self.sessions_frame)
        session_list_page_layout.addWidget(self.scroll_area)

        # Page 1: Loading Widget
        self.loading_page = self._create_loading_widget()

        self.content_stack.addWidget(self.session_list_page)
        self.content_stack.addWidget(self.loading_page)

        self.options_pane = OptionsPane(self.db)
        self.options_pane.sign_out_requested.connect(self.sign_out_requested)
        self.options_pane.setting_changed.connect(self.setting_changed)
        self.options_pane.panel_reset_requested.connect(self.reset_panel_sizes)
        self.options_pane.sanitize_requested.connect(self.handle_sanitize_request)
        self.options_pane.delete_account_requested.connect(self.handle_delete_account_request)
        
        self.splitter.addWidget(self.builder_pane)
        self.splitter.addWidget(self.sessions_panel_container)
        self.splitter.addWidget(self.options_pane)
        self.splitter.setSizes([300, 800, 300])
        
        self.status_poll_timer = QTimer(self); self.status_poll_timer.timeout.connect(self.poll_for_status_updates)
        self.full_refresh_timer = QTimer(self); self.full_refresh_timer.timeout.connect(self.refresh_all_data)
        self.ui_update_timer = QTimer(self); self.ui_update_timer.timeout.connect(self.update_countdown)
        self.auto_refresh_checkbox.stateChanged.connect(self.toggle_auto_refresh)
        
        self.update_background_icon(self.db.load_setting("theme", "Dark (Default)"))
        self.start_polling()

    def _create_header_widget(self):
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 6, 10, 6) # Adjusted margins to align with session cards
        labels = ["Status", "User@Host", "Operating System", "Session ID", "Open"]
        stretches = [0, 1, 1, 1, 0]
        fixed_widths = [120, -1, -1, -1, 120]
        for i, text in enumerate(labels):
            label = QLabel(f"<b>{text}</b>")
            if fixed_widths[i] > 0: label.setFixedWidth(fixed_widths[i])
            header_layout.addWidget(label, stretches[i], Qt.AlignmentFlag.AlignCenter)
        return header_widget

    def _create_loading_widget(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        spinner = AnimatedSpinner(self)
        label = QLabel("Refreshing Sessions...")
        layout.addStretch()
        layout.addWidget(spinner, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        return widget

    def update_background_icon(self, theme_name):
        self.session_list_page.update_background_icon(theme_name)

    def toggle_auto_refresh(self, state):
        if state == Qt.CheckState.Checked.value:
            self.countdown_label.show()
            self.refresh_all_data()
            self.full_refresh_timer.start(30000)
            self.ui_update_timer.start(1000)
        else:
            self.countdown_label.hide()
            self.full_refresh_timer.stop()
            self.ui_update_timer.stop()

    def update_countdown(self):
        self.countdown_seconds -= 1
        if self.countdown_seconds < 0: self.countdown_seconds = 0
        self.countdown_label.setText(f"Next in: {self.countdown_seconds}s")
    
    def handle_sanitize_request(self):
        if self.api.sanitize_data(self.username): self.refresh_all_data()
    def handle_delete_account_request(self):
        if self.api.delete_account(self.username): self.sign_out_requested.emit()

    def start_polling(self):
        self.refresh_all_data()
        self.status_poll_timer.start(5000)
        if self.auto_refresh_checkbox.isChecked():
            self.full_refresh_timer.start(30000)
            self.ui_update_timer.start(1000)

    def refresh_all_data(self):
        if self.is_refreshing: return
        self.is_refreshing = True
        self.countdown_seconds = 30
        self.countdown_label.setText(f"Next in: {self.countdown_seconds}s")
        
        # Stop any animations and clear old widgets immediately
        if self.active_animations:
            for anim in self.active_animations:
                anim.stop()
        self._clear_layout(self.sessions_frame_layout)
        self.session_widgets.clear()
        
        self.content_stack.setCurrentIndex(1) # Show loading page
        QTimer.singleShot(500, self._fetch_data_for_refresh)

    def _fetch_data_for_refresh(self):
        response = self.api.get_all_vault_data(self.username)
        
        try:
            if response and response.get("success"):
                new_session_data = response.get("data", {})
                for sid, sdata in self.sessions.items():
                    if sid in new_session_data and 'status' in sdata:
                        new_session_data[sid]['status'] = sdata['status']
                self.sessions = new_session_data
            else:
                self.sessions.clear()
        finally:
            self._animate_new_sessions_in()

    def _animate_new_sessions_in(self):
        self.content_stack.setCurrentIndex(0) # Switch back to the session list page
        
        self.active_animations.clear()
        sorted_sessions = sorted(self.sessions.items(), key=lambda item: (item[1].get('status', 'Offline') != 'Online', item[0]))
        
        temp_widgets = []
        for session_id, data in sorted_sessions:
            widget = self._create_session_widget(session_id, data)
            self.sessions_frame_layout.addWidget(widget)
            temp_widgets.append(widget)
        
        QApplication.processEvents()

        delay = 0
        for i, widget in enumerate(temp_widgets):
            session_id = sorted_sessions[i][0]
            self.session_widgets[session_id] = widget
            
            end_pos = widget.pos()
            start_pos = QPoint(end_pos.x(), -60) # Start from a fixed position above the frame
            
            anim = QPropertyAnimation(widget, b"pos")
            anim.setDuration(400)
            anim.setStartValue(start_pos)
            anim.setEndValue(end_pos)
            anim.setEasingCurve(QEasingCurve.Type.OutBounce)
            
            QTimer.singleShot(delay, anim.start)
            self.active_animations.append(anim)
            delay += 50

        self.is_refreshing = False

    def poll_for_status_updates(self):
        live_response = self.api.discover_sessions(self.username)
        live_sids = set(live_response.get('sessions', {}).keys()) if live_response else set()
        for sid, sdata in self.sessions.items():
            new_status = 'Online' if sid in live_sids else 'Offline'
            if sdata.get('status') != new_status:
                self.sessions[sid]['status'] = new_status
                if sid in self.session_widgets:
                    status_button = self.session_widgets[sid].findChild(QPushButton, "StatusButton")
                    if status_button:
                        status_button.setText(new_status.upper())
                        status_button.setProperty("status", new_status.lower())
                        status_button.style().unpolish(status_button); status_button.style().polish(status_button)

    def _clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _create_session_widget(self, session_id, data):
        widget = QWidget()
        widget.setObjectName("SessionEntryWidget") # For styling
        
        layout = QHBoxLayout(widget)
        # --- MODIFICATION: Added padding to create a card-like effect ---
        layout.setContentsMargins(10, 8, 10, 8)

        status = data.get('status', 'Offline')
        metadata = data.get('metadata', {})
        
        status_button = QPushButton(status.upper())
        status_button.setObjectName("StatusButton"); status_button.setProperty("status", status.lower())
        status_button.setEnabled(False); status_button.setFixedWidth(120)
        layout.addWidget(status_button, 0, Qt.AlignmentFlag.AlignCenter)

        user_host = QLabel(f"{metadata.get('user', 'N/A')}@{metadata.get('hostname', 'N/A')}")
        os_info = QLabel(metadata.get('os', 'Unknown'))
        sid_info = QLabel(session_id)
        
        layout.addWidget(user_host, 1, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(os_info, 1, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sid_info, 1, Qt.AlignmentFlag.AlignCenter)
        
        interact_button = QPushButton("Interact")
        interact_button.setObjectName("InteractButton"); interact_button.setFixedWidth(120)
        interact_button.clicked.connect(lambda chk, sid=session_id, sdata=data: self.session_interact_requested.emit(sid, sdata, sdata.get('status', 'Offline')))
        layout.addWidget(interact_button, 0, Qt.AlignmentFlag.AlignCenter)
        
        return widget

    def stop_polling(self):
        self.status_poll_timer.stop()
        self.full_refresh_timer.stop()
        self.ui_update_timer.stop()

    def reset_panel_sizes(self):
        self.splitter.setSizes([300, 800, 300])

    def send_task_from_session(self, sid, task):
        self.api.send_task(self.username, sid, task)