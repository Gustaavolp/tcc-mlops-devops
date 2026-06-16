import re
import logging
import traceback

# Logging configuration
logging.basicConfig(level = logging.INFO, format = "%(asctime)s - %(message)s")

class Utils:

    def __init__(self):

        super().__init__()

        pass

    @classmethod
    def log_errors(cls, func):
        """
        Decorator to log errors with cleaned traceback information.
        Args:
            func (function): The function to be decorated.
        Returns:
            function: The wrapped function with error logging.
        """

        def wrapper(*args, **kwargs):

            try:

                return func(*args, **kwargs)

            except Exception as e:

                tb = traceback.format_exc()

                tb_cleaned = re.sub(r'File ".*[\\/](.*\.py)", line (\d+)', r'File "\1", line \2', tb)
                logging.error(f"Error in {func.__name__}:\n{tb_cleaned}")

                raise

        return wrapper
