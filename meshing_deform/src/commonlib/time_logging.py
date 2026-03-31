import logging
import time

def setup_logger(logfile):
    logger = logging.getLogger("time")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(logfile, mode="a")
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# helper function for logging
def timed(logger, message, func, *args, **kwargs):
    start = time.perf_counter()
    result = func(*args, **kwargs)
    end = time.perf_counter()
    logger.info(f"{message} : {end - start:.3f} sec")
    return result