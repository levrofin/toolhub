import os
import pathlib

API = "alpaca"
# TODO: use package resources.
SCHEMA_PATH = pathlib.Path(
    os.path.join(os.path.dirname(__file__), "alpaca.yaml")
)
REQUEST_BODY_DESCRIPTIONS_PATH = None
BASE_URL = 'https://paper-api.alpaca.markets'
