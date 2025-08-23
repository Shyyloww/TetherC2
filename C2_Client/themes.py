# C2_Client/ui/themes.py
class ThemeManager:
    @staticmethod
    def get_stylesheet(theme_name):
        base_style = """
            #DisclaimerLabel { font-size: 12pt; }
            QWidget { font-family: Segoe UI; font-size: 10pt; }
            QPushButton:focus, QComboBox:focus, QCheckBox:focus, QSpinBox:focus, QLineEdit:focus, QTextEdit:focus, QTabBar::tab:focus, QListWidget::item:focus { outline: none; }
            QStatusBar { font-size: 9pt; }
            QMenu { padding: 5px; }
            QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { font-weight: bold; padding: 6px; }
            QSpinBox::up-button, QSpinBox::down-button { width: 0px; border: none; }
            QSpinBox { padding-right: 1px; }
            QComboBox { padding-left: 5px; }
            QComboBox QAbstractItemView::item { padding-left: 10px; }
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QTableWidget { border: none; }
            QTableWidget::item { padding-left: 10px; padding-right: 10px; padding-top: 8px; padding-bottom: 8px; }
            QHeaderView::section { font-weight: bold; padding: 8px; border: none; }
            QScrollBar:vertical { border: none; width: 8px; margin: 0px 0 0px 0; }
            QScrollBar::handle:vertical { border-radius: 4px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical { background: none; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
            QCheckBox::indicator { width: 13px; height: 13px; border-radius: 3px; }
            QPushButton#InteractButton { font-size: 11pt; font-weight: bold; border-radius: 4px; padding: 6px 10px; }
            QPushButton#StatusButton { font-size: 9pt; font-weight: bold; border-radius: 4px; padding: 6px 10px; min-width: 70px; }
            QLabel#HeaderStatusLabel { font-size: 10pt; font-weight: bold; border-radius: 4px; padding: 8px; }
            QTabWidget::pane { border: none; padding: 10px; }
            QTabBar::tab { padding: 8px 20px; border-radius: 4px; margin-right: 2px; font-weight: bold; }
            QDateTimeEdit { padding: 4px; border-radius: 4px; }
            QDateTimeEdit::down-button { subcontrol-origin: padding; subcontrol-position: top right; width: 20px; border-left-width: 1px; border-left-style: solid; border-top-right-radius: 3px; border-bottom-right-radius: 3px; }
            
            QGroupBox {
                border: 1px solid; /* color is set by theme */
                border-radius: 8px;
                margin-top: 15px;
            }
            QGroupBox::title {
                font-weight: bold;
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 4px 15px;
                border-radius: 5px;
            }
        """
        
        dark_theme = """
            #SessionEntryWidget { background-color: rgba(60, 60, 60, 0.8); border: 1px solid #555; border-radius: 5px; }
            #SessionEntryWidget:hover { background-color: rgba(74, 74, 74, 0.9); }
            AnimatedSpinner { qproperty-penColor: #f0f0f0; }
            #DisclaimerScreen { background-color: #2b2b2b; color: #f0f0f0; }
            #TitleLabel { font-family: "Segoe UI Black", "Segoe UI"; font-size: 64pt; font-weight: 900; }
            #WelcomeSubLabelTop { font-size: 12pt; color: #aaa; }
            #WelcomeSubLabelBottom { font-size: 12pt; color: #aaa; padding-top: 10px; padding-bottom: 25px; }
            #WelcomeScreen QPushButton { font-size: 21pt; padding: 18px 36px; font-weight: bold; }
            #LoginScreen QLineEdit, #CreateScreen QLineEdit { font-size: 16pt; padding: 12px; }
            #LoginScreen QPushButton, #CreateScreen QPushButton { font-size: 16pt; padding: 12px; }
            #LoginScreen QCheckBox { font-size: 11pt; }
            #SubtleButton { font-size: 11pt; border: none; color: #aaa; background-color: transparent; } #SubtleButton:hover { color: #ddd; }
            QLineEdit::placeholder, QTextEdit::placeholder { color: #8a8a8a; }
            QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #2b2b2b; color: #f0f0f0; }
            QGroupBox { background-color: #3c3c3c; border-color: #555; }
            QGroupBox::title { background-color: #3c3c3c; color: #f0f0f0; border: 1px solid #555; }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #252525; color: #f0f0f0; border: 1px solid #555; selection-background-color: #555; border-radius: 4px; }
            QDateTimeEdit::down-button { border-left-color: #555; }
            QDateTimeEdit::down-button:hover { background-color: #666; }
            QComboBox QAbstractItemView { background-color: #3c3c3c; color: #f0f0f0; border: 1px solid #555; selection-background-color: #555; }
            QPushButton { background-color: #555; border: 1px solid #666; padding: 5px; border-radius: 3px; }
            QPushButton:hover { background-color: #666; } QPushButton:pressed { background-color: #777; }
            QPushButton#InteractButton { background-color: #4CAF50; color: white; border: none; }
            QPushButton#InteractButton:hover { background-color: #5cb85c; }
            QCheckBox::indicator { border: 1px solid #666; background-color: #252525; } QCheckBox::indicator:checked { background-color: #f0f0f0; image: url(none); }
            QTableWidget { background-color: #3c3c3c; alternate-background-color: #454545; }
            QTableWidget::item { border-bottom: 1px solid #454545; }
            QTableWidget::item:hover { background-color: #454545; }
            QTableWidget::item:selected { background-color: #555; color: #f0f0f0; }
            QHeaderView::section { background-color: #2b2b2b; border-bottom: 2px solid #555; }
            QLabel, QCheckBox { color: #f0f0f0; background-color: transparent;} h2 { color: #66b2ff; }
            QSplitter::handle { background-color: #555; }
            QScrollBar:vertical { background: #3c3c3c; } QScrollBar::handle:vertical { background: #666; }
            QMenu::item:selected { background-color: #666; }
            QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { background-color: #9d2d2d; color: white; border-color: #666; }
            QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
            QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
            QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
            QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
            QTabBar::tab { background-color: #3c3c3c; color: #f0f0f0; border: 1px solid #555; }
            QTabBar::tab:hover { background-color: #4a4a4a; }
            QTabBar::tab:selected { background-color: #555; border: 1px solid #666; }
            QTabBar::tab:disabled { color: #888888; background-color: #303030; }
            QLabel#InactivityNoticeLabel { font-size: 9pt; color: #888; }
            #SplashScreen, #LoadingScreen { background-color: #2b2b2b; color: #f0f0f0; }
            #LoadingScreen #TitleLabel { color: #f0f0f0; }
            #LoadingStatusLabel { font-size: 14pt; color: #aaa; }
            DataHarvestPane QListWidget { background-color: #3c3c3c; border: 1px solid #555; }
            DataHarvestPane QListWidget::item { padding: 8px; }
            DataHarvestPane QListWidget::item:selected { background-color: #555; }
            DataHarvestPane QTableWidget { background-color: #252525; border: 1px solid #555; }
            DataHarvestPane QHeaderView::section { background-color: #3c3c3c; border-bottom: 2px solid #555; }
        """

        themes = {
            "Light": """
                #SessionEntryWidget { background-color: rgba(240, 240, 240, 0.8); border: 1px solid #ccc; border-radius: 5px; }
                #SessionEntryWidget:hover { background-color: rgba(224, 224, 224, 0.9); }
                AnimatedSpinner { qproperty-penColor: #111; }
                #DisclaimerScreen { background-color: #fcfcfc; color: #111; }
                #TitleLabel { font-family: "Segoe UI Black", "Segoe UI"; font-size: 64pt; font-weight: 900; }
                #WelcomeSubLabelTop { font-size: 12pt; color: #555; }
                #WelcomeSubLabelBottom { font-size: 12pt; color: #555; padding-top: 10px; padding-bottom: 25px; }
                #WelcomeScreen QPushButton { font-size: 21pt; padding: 18px 36px; font-weight: bold; }
                #LoginScreen QLineEdit, #CreateScreen QLineEdit { font-size: 16pt; padding: 12px; }
                #LoginScreen QPushButton, #CreateScreen QPushButton { font-size: 16pt; padding: 12px; }
                #LoginScreen QCheckBox { font-size: 11pt; }
                #SubtleButton { font-size: 11pt; border: none; color: #555; background-color: transparent; } #SubtleButton:hover { color: #111; }
                QLineEdit::placeholder, QTextEdit::placeholder { color: #777777; }
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #fcfcfc; color: #111; }
                QGroupBox { background-color: #f0f0f0; border-color: #ccc; }
                QGroupBox::title { background-color: #f0f0f0; color: #111; border: 1px solid #ccc; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #fff; color: #111; border: 1px solid #ccc; border-radius: 4px; }
                QComboBox QAbstractItemView { background-color: #fff; color: #111; border: 1px solid #ccc; selection-background-color: #cde8f9; }
                QPushButton { background-color: #e1e1e1; color: #000; border: 1px solid #adadad; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #cacaca; } QPushButton:pressed { background-color: #b0b0b0; }
                QPushButton#InteractButton { background-color: #5bc0de; color: white; border: none; }
                QPushButton#InteractButton:hover { background-color: #31b0d5; }
                QCheckBox::indicator { border: 1px solid #adadad; background-color: #fff; } QCheckBox::indicator:checked { background-color: #555; image: url(none); }
                QLabel, QCheckBox { color: #111; background-color: transparent;}
                QTabBar::tab:disabled { color: #aaaaaa; background-color: #e8e8e8; }
                QTableWidget { background-color: #fff; alternate-background-color: #f5f5f5; color: #000; }
                QTableWidget::item { border-bottom: 1px solid #f0f0f0; }
                QTableWidget::item:hover { background-color: #e6f2fa; }
                QTableWidget::item:selected { background-color: #cde8f9; color: #000; }
                QHeaderView::section { background-color: #fff; border-bottom: 2px solid #ccc; color: #000; }
                h2 { color: #005a9e; }
                QSplitter::handle { background-color: #ccc; }
                QScrollBar:vertical { background: #f0f0f0; } QScrollBar::handle:vertical { background: #ccc; }
                QMenu::item:selected { background-color: #d4d4d4; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { background-color: #c82333; color: white; border-color: #bd2130; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #f0f0f0; color: #111; border: 1px solid #ccc; }
                QTabBar::tab:hover { background-color: #e0e0e0; }
                QTabBar::tab:selected { background-color: #ffffff; border: 1px solid #adadad; }
                QLabel#InactivityNoticeLabel { font-size: 9pt; color: #666; }
                #SplashScreen, #LoadingScreen { background-color: #fcfcfc; color: #111; }
                #LoadingScreen #TitleLabel { color: #111; }
                #LoadingStatusLabel { font-size: 14pt; color: #555; }
                DataHarvestPane QListWidget { background-color: #f0f0f0; border: 1px solid #ccc; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #cde8f9; color: #111; }
                DataHarvestPane QTableWidget { background-color: #ffffff; border: 1px solid #ccc; color: #111; }
                DataHarvestPane QHeaderView::section { background-color: #f0f0f0; border-bottom: 2px solid #ccc; color: #111; }
            """,
            "Cyber": """
                #SessionEntryWidget { background-color: rgba(26, 10, 56, 0.8); border: 1px solid #8A2BE2; border-radius: 5px; }
                #SessionEntryWidget:hover { background-color: rgba(43, 11, 90, 0.9); }
                AnimatedSpinner { qproperty-penColor: #9bf1ff; }
                #DisclaimerScreen { background-color: #0d0221; color: #9bf1ff; }
                #TitleLabel { font-family: "Lucida Console", Monaco, monospace; font-size: 64pt; font-weight: 900; }
                #WelcomeSubLabelTop { font-size: 12pt; color: #8A2BE2; }
                #WelcomeSubLabelBottom { font-size: 12pt; color: #8A2BE2; padding-top: 10px; padding-bottom: 25px; }
                #WelcomeScreen QPushButton { font-size: 21pt; padding: 18px 36px; font-weight: bold; }
                #LoginScreen QLineEdit, #CreateScreen QLineEdit { font-size: 16pt; padding: 12px; }
                #LoginScreen QPushButton, #CreateScreen QPushButton { font-size: 16pt; padding: 12px; }
                #LoginScreen QCheckBox { font-size: 11pt; }
                #SubtleButton { font-size: 11pt; border: none; color: #8A2BE2; background-color: transparent; } #SubtleButton:hover { color: #9bf1ff; }
                QLineEdit::placeholder, QTextEdit::placeholder { color: #6a5acd; }
                QMainWindow, QDialog, QStackedWidget > QWidget { font-family: "Lucida Console", Monaco, monospace; background-color: #0d0221; color: #9bf1ff; }
                QGroupBox { background-color: #1a0a38; border-color: #8A2BE2; }
                QGroupBox::title { background-color: #1a0a38; color: #ff00ff; border: 1px solid #8A2BE2; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #0d0221; color: #9bf1ff; border: 1px solid #8A2BE2; selection-background-color: #00aaff; border-radius: 4px; }
                QComboBox QAbstractItemView { background-color: #1a0a38; color: #9bf1ff; border: 1px solid #8A2BE2; selection-background-color: #4c2a9a; }
                QPushButton { background-color: #2b0b5a; border: 1px solid #ff00ff; color: #ff00ff; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #3c1a7a; } QPushButton:pressed { background-color: #4c2a9a; }
                QPushButton#InteractButton { background-color: #00f0ff; color: #0d0221; border: none; }
                QPushButton#InteractButton:hover { background-color: #61dafb; }
                QCheckBox::indicator { border: 1px solid #8A2BE2; background-color: #0d0221; } QCheckBox::indicator:checked { background-color: #ff00ff; image: url(none); }
                QLabel, QCheckBox { color: #9bf1ff; background-color: transparent;}
                QTabBar::tab:disabled { color: #5f8f9f; background-color: #16082f; }
                QTableWidget { background-color: #1a0a38; alternate-background-color: #1f0c4a; }
                QTableWidget::item { border-bottom: 1px solid #2b0b5a; }
                QTableWidget::item:hover { background-color: #2b0b5a; }
                QTableWidget::item:selected { background-color: #4c2a9a; color: #9bf1ff; }
                QHeaderView::section { background-color: #0d0221; border-bottom: 2px solid #ff00ff; color: #9bf1ff; }
                h2 { color: #00f0ff; }
                QSplitter::handle { background-color: #8A2BE2; }
                QScrollBar:vertical { background: #1a0a38; } QScrollBar::handle:vertical { background: #8A2BE2; }
                QMenu::item:selected { background-color: #3c1a7a; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { background-color: #e11d48; color: white; border-color: #ff00ff; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #1a0a38; color: #9bf1ff; border: 1px solid #8A2BE2; }
                QTabBar::tab:hover { background-color: #2b0b5a; }
                QTabBar::tab:selected { background-color: #3c1a7a; border: 1px solid #ff00ff; }
                QLabel#InactivityNoticeLabel { font-size: 9pt; color: #6a5acd; }
                #SplashScreen, #LoadingScreen { background-color: #0d0221; color: #9bf1ff; }
                #LoadingScreen #TitleLabel { color: #9bf1ff; }
                #LoadingStatusLabel { font-size: 14pt; color: #8A2BE2; }
                DataHarvestPane QListWidget { background-color: #1a0a38; border: 1px solid #8A2BE2; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #4c2a9a; }
                DataHarvestPane QTableWidget { background-color: #0d0221; border: 1px solid #8A2BE2; }
                DataHarvestPane QHeaderView::section { background-color: #1a0a38; border-bottom: 2px solid #ff00ff; }
            """,
            "Matrix": """
                #SessionEntryWidget { background-color: rgba(5, 26, 5, 0.8); border: 1px solid #008F11; border-radius: 0px; }
                #SessionEntryWidget:hover { background-color: rgba(10, 42, 10, 0.9); }
                AnimatedSpinner { qproperty-penColor: #39ff14; }
                #DisclaimerScreen { background-color: #000000; color: #39ff14; }
                #TitleLabel { font-family: "Courier New", monospace; font-size: 64pt; font-weight: 900; }
                #WelcomeSubLabelTop { font-size: 12pt; color: #008F11; }
                #WelcomeSubLabelBottom { font-size: 12pt; color: #008F11; padding-top: 10px; padding-bottom: 25px; }
                #WelcomeScreen QPushButton { font-size: 21pt; padding: 18px 36px; font-weight: bold; }
                #LoginScreen QLineEdit, #CreateScreen QLineEdit { font-size: 16pt; padding: 12px; }
                #LoginScreen QPushButton, #CreateScreen QPushButton { font-size: 16pt; padding: 12px; }
                #LoginScreen QCheckBox { font-size: 11pt; }
                #SubtleButton { font-size: 11pt; border: none; color: #008F11; background-color: transparent; } #SubtleButton:hover { color: #39ff14; }
                QLineEdit::placeholder, QTextEdit::placeholder { color: #008F11; }
                QMainWindow, QDialog, QStackedWidget > QWidget { font-family: "Courier New", monospace; background-color: #000000; color: #39ff14; }
                QGroupBox { background-color: #051a05; border-color: #008F11; }
                QGroupBox::title { background-color: #051a05; color: #39ff14; border: 1px solid #008F11; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #000; color: #39ff14; border: 1px solid #008F11; selection-background-color: #39ff14; selection-color: black; border-radius: 0px; }
                QComboBox QAbstractItemView { background-color: #051a05; color: #39ff14; border: 1px solid #008F11; selection-background-color: #145414; }
                QPushButton { background-color: #0a2a0a; border: 1px solid #39ff14; color: #39ff14; padding: 5px; }
                QPushButton:hover { background-color: #0f3f0f; } QPushButton:pressed { background-color: #145414; }
                QPushButton#InteractButton { background-color: #39ff14; color: #000000; border: none; }
                QPushButton#InteractButton:hover { background-color: #9dff8a; }
                QCheckBox::indicator { border: 1px solid #39ff14; background-color: #000; } QCheckBox::indicator:checked { background-color: #39ff14; image: url(none); }
                QLabel, QCheckBox { color: #39ff14; background-color: transparent;}
                QTabBar::tab:disabled { color: #299f14; background-color: #031303; }
                QTableWidget { background-color: #051a05; alternate-background-color: #0a2a0a; }
                QTableWidget::item { border-bottom: 1px solid #0f3f0f; }
                QTableWidget::item:hover { background-color: #0f3f0f; }
                QTableWidget::item:selected { background-color: #145414; color: #39ff14; }
                QHeaderView::section { background-color: #000; border-bottom: 2px solid #39ff14; }
                h2 { color: #9dff8a; }
                QSplitter::handle { background-color: #008F11; }
                QScrollBar:vertical { background: #051a05; } QScrollBar::handle:vertical { background: #39ff14; }
                QMenu::item:selected { background-color: #0f3f0f; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { background-color: #8b0000; color: #39ff14; border-color: #39ff14; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: #000; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: #000; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: black; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: black; }
                QTabBar::tab { background-color: #051a05; color: #39ff14; border: 1px solid #008F11; }
                QTabBar::tab:hover { background-color: #0a2a0a; }
                QTabBar::tab:selected { background-color: #0f3f0f; border: 1px solid #39ff14; }
                QLabel#InactivityNoticeLabel { font-size: 9pt; color: #008F11; }
                #SplashScreen, #LoadingScreen { background-color: #000000; color: #39ff14; }
                #LoadingScreen #TitleLabel { color: #39ff14; }
                #LoadingStatusLabel { font-size: 14pt; color: #008F11; }
                DataHarvestPane QListWidget { background-color: #051a05; border: 1px solid #008F11; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #145414; }
                DataHarvestPane QTableWidget { background-color: #000000; border: 1px solid #008F11; }
                DataHarvestPane QHeaderView::section { background-color: #051a05; border-bottom: 2px solid #39ff14; }
            """,
            "Sunrise": """
                #SessionEntryWidget { background-color: rgba(255, 236, 179, 0.8); border: 1px solid #ffca28; border-radius: 5px; }
                #SessionEntryWidget:hover { background-color: rgba(255, 224, 178, 0.9); }
                AnimatedSpinner { qproperty-penColor: #4e342e; }
                #DisclaimerScreen { background-color: #fff8e1; color: #4e342e; }
                #TitleLabel { font-family: "Segoe UI Black", "Segoe UI"; font-size: 64pt; font-weight: 900; }
                #WelcomeSubLabelTop { font-size: 12pt; color: #d84315; }
                #WelcomeSubLabelBottom { font-size: 12pt; color: #d84315; padding-top: 10px; padding-bottom: 25px; }
                #WelcomeScreen QPushButton { font-size: 21pt; padding: 18px 36px; font-weight: bold; }
                #LoginScreen QLineEdit, #CreateScreen QLineEdit { font-size: 16pt; padding: 12px; }
                #LoginScreen QPushButton, #CreateScreen QPushButton { font-size: 16pt; padding: 12px; }
                #LoginScreen QCheckBox { font-size: 11pt; }
                #SubtleButton { font-size: 11pt; border: none; color: #bf360c; background-color: transparent; } #SubtleButton:hover { color: #d84315; }
                QLineEdit::placeholder, QTextEdit::placeholder { color: #a1887f; }
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #fff8e1; color: #4e342e; }
                QGroupBox { background-color: #ffecb3; border-color: #ffca28; }
                QGroupBox::title { background-color: #ffecb3; color: #bf360c; border: 1px solid #ffca28; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #fff; color: #4e342e; border: 1px solid #ffca28; border-radius: 4px; }
                QComboBox QAbstractItemView { background-color: #ffecb3; color: #4e342e; border: 1px solid #ffca28; selection-background-color: #ffcc80; }
                QPushButton { background-color: #ffb74d; color: #4e342e; border: 1px solid #ffa726; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #ffa726; } QPushButton:pressed { background-color: #ff9800; }
                QPushButton#InteractButton { background-color: #ff9800; color: #4e342e; border: none; }
                QPushButton#InteractButton:hover { background-color: #fb8c00; }
                QCheckBox::indicator { border: 1px solid #ffca28; background-color: #fff; } QCheckBox::indicator:checked { background-color: #bf360c; image: url(none); }
                QLabel, QCheckBox { color: #4e342e; background-color: transparent;}
                QTabBar::tab:disabled { color: #ab8e79; background-color: #f7e7c5; }
                QTableWidget { background-color: #fff; alternate-background-color: #fff8e1; color: #4e342e; }
                QTableWidget::item { border-bottom: 1px solid #ffecb3; }
                QTableWidget::item:hover { background-color: #ffecb3; }
                QTableWidget::item:selected { background-color: #ffcc80; color: #4e342e; }
                QHeaderView::section { background-color: #fff8e1; border-bottom: 2px solid #bf360c; color: #4e342e; }
                h2 { color: #d84315; }
                QSplitter::handle { background-color: #ffca28; }
                QScrollBar:vertical { background: #ffecb3; } QScrollBar::handle:vertical { background: #ffca28; }
                QMenu::item:selected { background-color: #ffb74d; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { background-color: #e53935; color: white; border-color: #d32f2f; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #ffecb3; color: #4e342e; border: 1px solid #ffca28; }
                QTabBar::tab:hover { background-color: #ffb74d; }
                QTabBar::tab:selected { background-color: #ffa726; border: 1px solid #bf360c; }
                QLabel#InactivityNoticeLabel { font-size: 9pt; color: #a1887f; }
                #SplashScreen, #LoadingScreen { background-color: #fff8e1; color: #4e342e; }
                #LoadingScreen #TitleLabel { color: #4e342e; }
                #LoadingStatusLabel { font-size: 14pt; color: #d84315; }
                DataHarvestPane QListWidget { background-color: #ffecb3; border: 1px solid #ffca28; color: #4e342e; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #ffcc80; }
                DataHarvestPane QTableWidget { background-color: #fff; border: 1px solid #ffca28; color: #4e342e; }
                DataHarvestPane QHeaderView::section { background-color: #ffecb3; border-bottom: 2px solid #bf360c; color: #4e342e; }
            """,
            "Sunset": """
                #SessionEntryWidget { background-color: rgba(60, 58, 82, 0.8); border: 1px solid #ff8c42; border-radius: 5px; }
                #SessionEntryWidget:hover { background-color: rgba(74, 72, 97, 0.9); }
                AnimatedSpinner { qproperty-penColor: #fff2cc; }
                #DisclaimerScreen { background-color: #1a182f; color: #fff2cc; }
                #TitleLabel { font-family: "Segoe UI Black", "Segoe UI"; font-size: 64pt; font-weight: 900; }
                #WelcomeSubLabelTop { font-size: 12pt; color: #ff8c42; }
                #WelcomeSubLabelBottom { font-size: 12pt; color: #ff8c42; padding-top: 10px; padding-bottom: 25px; }
                #WelcomeScreen QPushButton { font-size: 21pt; padding: 18px 36px; font-weight: bold; }
                #LoginScreen QLineEdit, #CreateScreen QLineEdit { font-size: 16pt; padding: 12px; }
                #LoginScreen QPushButton, #CreateScreen QPushButton { font-size: 16pt; padding: 12px; }
                #LoginScreen QCheckBox { font-size: 11pt; }
                #SubtleButton { font-size: 11pt; border: none; color: #ff8c42; background-color: transparent; } #SubtleButton:hover { color: #ff5e57; }
                QLineEdit::placeholder, QTextEdit::placeholder { color: #ab927a; }
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #1a182f; color: #fff2cc; }
                QGroupBox { background-color: #3c3a52; border-color: #ff8c42; }
                QGroupBox::title { background-color: #3c3a52; color: #ff8c42; border: 1px solid #ff8c42; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #1a182f; color: #fff2cc; border: 1px solid #ff8c42; selection-background-color: #ff5e57; border-radius: 4px; }
                QComboBox QAbstractItemView { background-color: #3c3a52; color: #fff2cc; border: 1px solid #ff8c42; selection-background-color: #ff5e57; }
                QPushButton { background-color: #ff5e57; color: #ffffff; border: 1px solid #ff8c42; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #ff7b72; } QPushButton:pressed { background-color: #e64a19; }
                QPushButton#InteractButton { background-color: #ff8c42; color: #1a182f; border: none; }
                QPushButton#InteractButton:hover { background-color: #ffab70; }
                QCheckBox::indicator { border: 1px solid #ff8c42; background-color: #1a182f; } QCheckBox::indicator:checked { background-color: #ff8c42; image: url(none); }
                QLabel, QCheckBox { color: #fff2cc; background-color: transparent;}
                QTabBar::tab:disabled { color: #a99f86; background-color: #312f45; }
                QTableWidget { background-color: #3c3a52; alternate-background-color: #4a4861; }
                QTableWidget::item { border-bottom: 1px solid #5a5870; }
                QTableWidget::item:hover { background-color: #4a4861; }
                QTableWidget::item:selected { background-color: #ff5e57; color: #fff; }
                QHeaderView::section { background-color: #1a182f; border-bottom: 2px solid #ff5e57; color: #ff8c42; }
                h2 { color: #ff8c42; }
                QSplitter::handle { background-color: #ff8c42; }
                QScrollBar:vertical { background: #3c3a52; } QScrollBar::handle:vertical { background: #ff8c42; }
                QMenu::item:selected { background-color: #ff5e57; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { background-color: #c70039; color: white; border-color: #ff5e57; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #3c3a52; color: #fff2cc; border: 1px solid #ff8c42; }
                QTabBar::tab:hover { background-color: #4a4861; }
                QTabBar::tab:selected { background-color: #ff5e57; border: 1px solid #ff8c42; color: white; }
                QLabel#InactivityNoticeLabel { font-size: 9pt; color: #ab927a; }
                #SplashScreen, #LoadingScreen { background-color: #1a182f; color: #fff2cc; }
                #LoadingScreen #TitleLabel { color: #fff2cc; }
                #LoadingStatusLabel { font-size: 14pt; color: #ff8c42; }
                DataHarvestPane QListWidget { background-color: #3c3a52; border: 1px solid #ff8c42; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #ff5e57; }
                DataHarvestPane QTableWidget { background-color: #1a182f; border: 1px solid #ff8c42; }
                DataHarvestPane QHeaderView::section { background-color: #3c3a52; border-bottom: 2px solid #ff5e57; }
            """,
            "Jungle": """
                #SessionEntryWidget { background-color: rgba(43, 65, 54, 0.8); border: 1px solid #a3b18a; border-radius: 5px; }
                #SessionEntryWidget:hover { background-color: rgba(58, 90, 64, 0.9); }
                AnimatedSpinner { qproperty-penColor: #dad7cd; }
                #DisclaimerScreen { background-color: #344e41; color: #dad7cd; }
                #TitleLabel { font-family: "Segoe UI Black", "Segoe UI"; font-size: 64pt; font-weight: 900; }
                #WelcomeSubLabelTop { font-size: 12pt; color: #a3b18a; }
                #WelcomeSubLabelBottom { font-size: 12pt; color: #a3b18a; padding-top: 10px; padding-bottom: 25px; }
                #WelcomeScreen QPushButton { font-size: 21pt; padding: 18px 36px; font-weight: bold; }
                #LoginScreen QLineEdit, #CreateScreen QLineEdit { font-size: 16pt; padding: 12px; }
                #LoginScreen QPushButton, #CreateScreen QPushButton { font-size: 16pt; padding: 12px; }
                #LoginScreen QCheckBox { font-size: 11pt; }
                #SubtleButton { font-size: 11pt; border: none; color: #a3b18a; background-color: transparent; } #SubtleButton:hover { color: #dad7cd; }
                QLineEdit::placeholder, QTextEdit::placeholder { color: #8f997a; }
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #344e41; color: #dad7cd; }
                QGroupBox { background-color: #2b4136; border-color: #a3b18a; }
                QGroupBox::title { background-color: #2b4136; color: #dad7cd; border: 1px solid #a3b18a; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #3a5a40; color: #dad7cd; border: 1px solid #588157; selection-background-color: #a3b18a; selection-color: #2b4136; border-radius: 4px; }
                QComboBox QAbstractItemView { background-color: #2b4136; color: #dad7cd; border: 1px solid #588157; selection-background-color: #588157; }
                QPushButton { background-color: #588157; color: #ffffff; border: 1px solid #a3b18a; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #6a996a; } QPushButton:pressed { background-color: #4a714a; }
                QPushButton#InteractButton { background-color: #a3b18a; color: #2b4136; border: none; }
                QPushButton#InteractButton:hover { background-color: #b3c19a; }
                QCheckBox::indicator { border: 1px solid #a3b18a; background-color: #3a5a40; } QCheckBox::indicator:checked { background-color: #a3b18a; image: url(none); }
                QLabel, QCheckBox { color: #dad7cd; background-color: transparent;}
                QTabBar::tab:disabled { color: #8e8b86; background-color: #314838; }
                QTableWidget { background-color: #3a5a40; alternate-background-color: #3f684c; }
                QTableWidget::item { border-bottom: 1px solid #4a714a; }
                QTableWidget::item:hover { background-color: #4a714a; }
                QTableWidget::item:selected { background-color: #588157; color: #fff; }
                QHeaderView::section { background-color: #344e41; border-bottom: 2px solid #a3b18a; }
                h2 { color: #cde2b4; }
                QSplitter::handle { background-color: #a3b18a; }
                QScrollBar:vertical { background: #2b4136; } QScrollBar::handle:vertical { background: #a3b18a; }
                QMenu::item:selected { background-color: #588157; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { background-color: #c1440e; color: white; border-color: #a3b18a; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #3a5a40; color: #dad7cd; border: 1px solid #588157; }
                QTabBar::tab:hover { background-color: #4a714a; }
                QTabBar::tab:selected { background-color: #588157; border: 1px solid #a3b18a; color: white; }
                QLabel#InactivityNoticeLabel { font-size: 9pt; color: #a3b18a; }
                #SplashScreen, #LoadingScreen { background-color: #344e41; color: #dad7cd; }
                #LoadingScreen #TitleLabel { color: #dad7cd; }
                #LoadingStatusLabel { font-size: 14pt; color: #a3b18a; }
                DataHarvestPane QListWidget { background-color: #2b4136; border: 1px solid #588157; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #588157; }
                DataHarvestPane QTableWidget { background-color: #3a5a40; border: 1px solid #588157; }
                DataHarvestPane QHeaderView::section { background-color: #2b4136; border-bottom: 2px solid #a3b18a; }
            """,
            "Ocean": """
                #SessionEntryWidget { background-color: rgba(4, 28, 50, 0.8); border: 1px solid #04294b; border-radius: 5px; }
                #SessionEntryWidget:hover { background-color: rgba(0, 116, 217, 0.9); }
                AnimatedSpinner { qproperty-penColor: #e0ffff; }
                #DisclaimerScreen { background-color: #020f1c; color: #e0ffff; }
                #TitleLabel { font-family: "Segoe UI Black", "Segoe UI"; font-size: 64pt; font-weight: 900; }
                #WelcomeSubLabelTop { font-size: 12pt; color: #61dafb; }
                #WelcomeSubLabelBottom { font-size: 12pt; color: #61dafb; padding-top: 10px; padding-bottom: 25px; }
                #WelcomeScreen QPushButton { font-size: 21pt; padding: 18px 36px; font-weight: bold; }
                #LoginScreen QLineEdit, #CreateScreen QLineEdit { font-size: 16pt; padding: 12px; }
                #LoginScreen QPushButton, #CreateScreen QPushButton { font-size: 16pt; padding: 12px; }
                #LoginScreen QCheckBox { font-size: 11pt; }
                #SubtleButton { font-size: 11pt; border: none; color: #61dafb; background-color: transparent; } #SubtleButton:hover { color: #e0ffff; }
                QLineEdit::placeholder, QTextEdit::placeholder { color: #4f8a9e; }
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #020f1c; color: #e0ffff; }
                QGroupBox { background-color: #041c32; border-color: #04294b; }
                QGroupBox::title { background-color: #041c32; color: #61dafb; border: 1px solid #04294b; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #020f1c; color: #e0ffff; border: 1px solid #04294b; border-radius: 4px; }
                QComboBox QAbstractItemView { background-color: #041c32; color: #e0ffff; border: 1px solid #04294b; selection-background-color: #0074d9; }
                QPushButton { background-color: #04294b; color: #e0ffff; border: 1px solid #61dafb; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #0074d9; } QPushButton:pressed { background-color: #0060c0; }
                QPushButton#InteractButton { background-color: #0074d9; color: white; border: none; }
                QPushButton#InteractButton:hover { background-color: #0084e9; }
                QCheckBox::indicator { border: 1px solid #61dafb; background-color: #020f1c; } QCheckBox::indicator:checked { background-color: #61dafb; image: url(none); }
                QLabel, QCheckBox { color: #e0ffff; background-color: transparent;}
                QTabBar::tab:disabled { color: #7fbfdf; background-color: #031525; }
                QTableWidget { background-color: #041c32; alternate-background-color: #04233f; }
                QTableWidget::item { border-bottom: 1px solid #04294b; }
                QTableWidget::item:hover { background-color: #04294b; }
                QTableWidget::item:selected { background-color: #0074d9; color: #e0ffff; }
                QHeaderView::section { background-color: #020f1c; border-bottom: 2px solid #61dafb; }
                h2 { color: #bde0ff; }
                QSplitter::handle { background-color: #61dafb; }
                QScrollBar:vertical { background: #041c32; } QScrollBar::handle:vertical { background: #61dafb; }
                QMenu::item:selected { background-color: #0074d9; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { background-color: #FF4136; color: white; border-color: #61dafb; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #041c32; color: #e0ffff; border: 1px solid #04294b; }
                QTabBar::tab:hover { background-color: #04294b; }
                QTabBar::tab:selected { background-color: #0074d9; border: 1px solid #61dafb; color: white; }
                QLabel#InactivityNoticeLabel { font-size: 9pt; color: #4f8a9e; }
                #SplashScreen, #LoadingScreen { background-color: #020f1c; color: #e0ffff; }
                #LoadingScreen #TitleLabel { color: #e0ffff; }
                #LoadingStatusLabel { font-size: 14pt; color: #61dafb; }
                DataHarvestPane QListWidget { background-color: #041c32; border: 1px solid #04294b; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #0074d9; }
                DataHarvestPane QTableWidget { background-color: #020f1c; border: 1px solid #04294b; }
                DataHarvestPane QHeaderView::section { background-color: #041c32; border-bottom: 2px solid #61dafb; }
            """,
            "Galaxy": """
                #SessionEntryWidget { background-color: rgba(30, 31, 41, 0.8); border: 1px solid #bd93f9; border-radius: 5px; }
                #SessionEntryWidget:hover { background-color: rgba(52, 55, 70, 0.9); }
                AnimatedSpinner { qproperty-penColor: #f8f8f2; }
                #DisclaimerScreen { background-color: #282a36; color: #f8f8f2; }
                #TitleLabel { font-family: "Segoe UI Black", "Segoe UI"; font-size: 64pt; font-weight: 900; }
                #WelcomeSubLabelTop { font-size: 12pt; color: #ff79c6; }
                #WelcomeSubLabelBottom { font-size: 12pt; color: #ff79c6; padding-top: 10px; padding-bottom: 25px; }
                #WelcomeScreen QPushButton { font-size: 21pt; padding: 18px 36px; font-weight: bold; }
                #LoginScreen QLineEdit, #CreateScreen QLineEdit { font-size: 16pt; padding: 12px; }
                #LoginScreen QPushButton, #CreateScreen QPushButton { font-size: 16pt; padding: 12px; }
                #LoginScreen QCheckBox { font-size: 11pt; }
                #SubtleButton { font-size: 11pt; border: none; color: #bd93f9; background-color: transparent; } #SubtleButton:hover { color: #f8f8f2; }
                QLineEdit::placeholder, QTextEdit::placeholder { color: #9370db; }
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #282a36; color: #f8f8f2; }
                QGroupBox { background-color: #1e1f29; border-color: #bd93f9; }
                QGroupBox::title { background-color: #1e1f29; color: #ff79c6; border: 1px solid #bd93f9; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #21222c; color: #f8f8f2; border: 1px solid #6272a4; selection-background-color: #44475a; border-radius: 4px; }
                QComboBox QAbstractItemView { background-color: #1e1f29; color: #f8f8f2; border: 1px solid #6272a4; selection-background-color: #44475a; }
                QPushButton { background-color: #44475a; border: 1px solid #bd93f9; color: #f8f8f2; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #5a5c72; } QPushButton:pressed { background-color: #343746; }
                QPushButton#InteractButton { background-color: #bd93f9; color: #f8f8f2; border: none; }
                QPushButton#InteractButton:hover { background-color: #cf93f9; }
                QCheckBox::indicator { border: 1px solid #bd93f9; background-color: #21222c; } QCheckBox::indicator:checked { background-color: #bd93f9; image: url(none); }
                QLabel, QCheckBox { color: #f8f8f2; background-color: transparent;}
                QTabBar::tab:disabled { color: #a8a8a2; background-color: #20212a; }
                QTableWidget { background-color: #1e1f29; alternate-background-color: #21222c; }
                QTableWidget::item { border-bottom: 1px solid #44475a; }
                QTableWidget::item:hover { background-color: #44475a; }
                QTableWidget::item:selected { background-color: #5a5c72; color: #f8f8f2; }
                QHeaderView::section { background-color: #282a36; border-bottom: 2px solid #bd93f9; }
                h2 { color: #8be9fd; }
                QSplitter::handle { background-color: #bd93f9; }
                QScrollBar:vertical { background: #1e1f29; } QScrollBar::handle:vertical { background: #bd93f9; }
                QMenu::item:selected { background-color: #44475a; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { background-color: #ff5555; color: #f8f8f2; border-color: #bd93f9; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #21222c; color: #f8f8f2; border: 1px solid #6272a4; }
                QTabBar::tab:hover { background-color: #343746; }
                QTabBar::tab:selected { background-color: #44475a; border: 1px solid #bd93f9; color: white; }
                QLabel#InactivityNoticeLabel { font-size: 9pt; color: #9370db; }
                #SplashScreen, #LoadingScreen { background-color: #282a36; color: #f8f8f2; }
                #LoadingScreen #TitleLabel { color: #f8f8f2; }
                #LoadingStatusLabel { font-size: 14pt; color: #ff79c6; }
                DataHarvestPane QListWidget { background-color: #1e1f29; border: 1px solid #6272a4; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #44475a; }
                DataHarvestPane QTableWidget { background-color: #21222c; border: 1px solid #6272a4; }
                DataHarvestPane QHeaderView::section { background-color: #1e1f29; border-bottom: 2px solid #bd93f9; }
            """,
            "Candy": """
                #SessionEntryWidget { background-color: rgba(247, 228, 243, 0.8); border: 1px solid #c9a7c7; border-radius: 5px; }
                #SessionEntryWidget:hover { background-color: rgba(241, 218, 236, 0.9); }
                AnimatedSpinner { qproperty-penColor: #5d5d5d; }
                #DisclaimerScreen { background-color: #fdf6f6; color: #5d5d5d; }
                #TitleLabel { font-family: "Segoe UI Black", "Segoe UI"; font-size: 64pt; font-weight: 900; }
                #WelcomeSubLabelTop { font-size: 12pt; color: #8c728a; }
                #WelcomeSubLabelBottom { font-size: 12pt; color: #8c728a; padding-top: 10px; padding-bottom: 25px; }
                #WelcomeScreen QPushButton { font-size: 21pt; padding: 18px 36px; font-weight: bold; }
                #LoginScreen QLineEdit, #CreateScreen QLineEdit { font-size: 16pt; padding: 12px; }
                #LoginScreen QPushButton, #CreateScreen QPushButton { font-size: 16pt; padding: 12px; }
                #LoginScreen QCheckBox { font-size: 11pt; }
                #SubtleButton { font-size: 11pt; border: none; color: #8c728a; background-color: transparent; } #SubtleButton:hover { color: #c2185b; }
                QLineEdit::placeholder, QTextEdit::placeholder { color: #a1887f; }
                QMainWindow, QDialog, QStackedWidget > QWidget { background-color: #fdf6f6; color: #5d5d5d; }
                QGroupBox { background-color: #f7e4f3; border-color: #c9a7c7; }
                QGroupBox::title { background-color: #f7e4f3; color: #8c728a; border: 1px solid #c9a7c7; }
                QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateTimeEdit { background-color: #fff; color: #555; border: 1px solid #a3d9e8; selection-background-color: #ffe0b2; border-radius: 4px; }
                QComboBox QAbstractItemView { background-color: #f7e4f3; color: #5d5d5d; border: 1px solid #c9a7c7; selection-background-color: #b3e5fc; }
                QPushButton { background-color: #c8e6c9; color: #385b38; border: 1px solid #a4d4a5; padding: 5px; border-radius: 3px; }
                QPushButton:hover { background-color: #b7e0b8; } QPushButton:pressed { background-color: #a6d9a7; }
                QPushButton#InteractButton { background-color: #b3e5fc; color: #555; border: none; }
                QPushButton#InteractButton:hover { background-color: #a3d9e8; }
                QCheckBox::indicator { border: 1px solid #c9a7c7; background-color: #fff; } QCheckBox::indicator:checked { background-color: #a3d9a8; image: url(none); }
                QLabel, QCheckBox { color: #5d5d5d; background-color: transparent;}
                QTabBar::tab:disabled { color: #b5aab3; background-color: #f6eaf5; }
                QTableWidget { background-color: #fff; alternate-background-color: #f1f8e9; color: #444; }
                QTableWidget::item { border-bottom: 1px solid #e0e0e0; }
                QTableWidget::item:hover { background-color: #f7e4f3; }
                QTableWidget::item:selected { background-color: #b3e5fc; color: #555; }
                QHeaderView::section { background-color: #fdf6f6; border-bottom: 2px solid #c8e6c9; color: #6c6643; }
                h2 { color: #c2185b; }
                QSplitter::handle { background-color: #c9a7c7; }
                QScrollBar:vertical { background: #f7e4f3; } QScrollBar::handle:vertical { background: #c9a7c7; }
                QMenu::item:selected { background-color: #b3e5fc; }
                QPushButton#SanitizeButton, QPushButton#StopBuildButton, QPushButton#DeleteAccountButton { background-color: #ffcdd2; color: #b71c1c; border-color: #ef9a9a; }
                QPushButton#StatusButton[status="online"] { background-color: #28a745; color: white; border: none; }
                QPushButton#StatusButton[status="offline"] { background-color: #dc3545; color: white; border: none; }
                QLabel#HeaderStatusLabel[status="online"] { background-color: #28a745; color: white; }
                QLabel#HeaderStatusLabel[status="offline"] { background-color: #dc3545; color: white; }
                QTabBar::tab { background-color: #f7e4f3; color: #5d5d5d; border: 1px solid #c9a7c7; }
                QTabBar::tab:hover { background-color: #f1daec; }
                QTabBar::tab:selected { background-color: #ffffff; border: 1px solid #c9a7c7; }
                QLabel#InactivityNoticeLabel { font-size: 9pt; color: #8c728a; }
                #SplashScreen, #LoadingScreen { background-color: #fdf6f6; color: #5d5d5d; }
                #LoadingScreen #TitleLabel { color: #5d5d5d; }
                #LoadingStatusLabel { font-size: 14pt; color: #c2185b; }
                DataHarvestPane QListWidget { background-color: #f7e4f3; border: 1px solid #c9a7c7; color: #5d5d5d; }
                DataHarvestPane QListWidget::item { padding: 8px; }
                DataHarvestPane QListWidget::item:selected { background-color: #b3e5fc; }
                DataHarvestPane QTableWidget { background-color: #ffffff; border: 1px solid #a3d9e8; color: #5d5d5d; }
                DataHarvestPane QHeaderView::section { background-color: #f7e4f3; border-bottom: 2px solid #c9a7c7; color: #5d5d5d; }
            """
        }
        
        themes["Dark (Default)"] = dark_theme
        return base_style + themes.get(theme_name, dark_theme)