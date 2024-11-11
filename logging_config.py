import logging
from logging.handlers import RotatingFileHandler
import os

from flask import app


if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

app.logger.info('Main App startup')

# Get the current working directory
current_directory = os.getcwd()

# Print the current working directory
app.logger.info(f"Current Working Directory: {current_directory}")