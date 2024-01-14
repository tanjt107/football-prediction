import google.cloud.logging


def setup_logging():
    google.cloud.logging.Client().setup_logging()
