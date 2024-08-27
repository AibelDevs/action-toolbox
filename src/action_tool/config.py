import logging


def get_logger():
    # Note to self! Without declaring basicConfig, the logger will not respond to any change in the logging level
    logging.basicConfig(format="[%(asctime)s: %(levelname)s/%(name)s] | %(message)s")
    _logger = logging.getLogger("action-tool")
    return _logger


logger = get_logger()
