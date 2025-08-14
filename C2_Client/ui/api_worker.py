# C2_Client/ui/api_worker.py
from PyQt6.QtCore import QObject, pyqtSignal

class ApiWorker(QObject):
    """
    A worker object that runs a function from the ApiClient on a separate thread.
    This is essential to prevent the GUI from freezing during network requests.
    """
    finished = pyqtSignal(object)  # Emits the response object when done

    def __init__(self, api_client, function_name, *args, **kwargs):
        super().__init__()
        self.api_client = api_client
        self.function_name = function_name
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """Executes the API function and emits the result."""
        try:
            function_to_call = getattr(self.api_client, self.function_name)
            response = function_to_call(*self.args, **self.kwargs)
            self.finished.emit(response)
        except Exception as e:
            # Emit an error response if something unexpected happens
            self.finished.emit({"success": False, "error": f"Worker thread error: {e}"})