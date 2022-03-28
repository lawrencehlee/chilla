import logging

logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    filename="Chilla.log", level=logging.INFO)


def log(message, level=logging.INFO):
    print(message)
    logging.log(level, message)
