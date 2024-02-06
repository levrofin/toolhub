import os
import pathlib

API = "crunchbase"
# TODO: use package resources.
SCHEMA_PATH = pathlib.Path(
    os.path.join(os.path.dirname(__file__), "crunchbase_v4.json")
)
BASE_URL = "https://api.crunchbase.com/api/v4"
