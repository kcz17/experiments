import pathlib
from datetime import datetime


def generate_output_path(suffix=""):
    now = datetime.now().strftime("%Y-%m-%d.%H%M%S.%f")
    path = str(pathlib.Path(__file__).parent.absolute()) + f"/out/{now}"
    if suffix != "":
        path += f".{suffix}"
    return path + ".json"
