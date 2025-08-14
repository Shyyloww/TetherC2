# C2_Client/ui/logging_handler.py
import logging
from PyQt6.QtCore import QObject, pyqtSignal

class QtLogHandler(QObject, logging.Handler):
    """
    A custom logging handler that emits a PyQt signal for each log record.
    """
    log_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)
        logging.Handler.__init__(self)

    def emit(self, record):
        """
        Formats the log record and emits it via a signal.
        """
        msg = self.format(record)
        self.log_signal.emit(msg)