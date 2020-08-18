import logging

logger = logging.getLogger(__name__)
logger.setLevel('ERROR')
logger_handler = logging.FileHandler('logs.log')
logger_handler.setLevel('DEBUG')
loger_formater = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger_handler.setFormatter(loger_formater)
logger.addHandler(logger_handler)

print(logger.level)

logger.info('jdkfjdkjfkdfjkdjf')