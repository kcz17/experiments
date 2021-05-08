import os
from dataclasses import dataclass

import dotenv

dotenv.load_dotenv()


@dataclass
class Config:
    KUBEDIM_HOST = os.getenv("KUBEDIM_HOST", "155.198.198.11")
    DIMMER_PORT = os.getenv("DIMMER_PORT", "30002")
    ADMIN_PORT = os.getenv("ADMIN_PORT", "30003")
    CARTS_RESEEDER_PORT = os.getenv("CARTS_RESEEDER_PORT", "30004")

    LOAD_TESTING_DIRECTORY = os.getenv("LOAD_TESTING_DIRECTORY", "../load-testing")
    ABS_LOAD_TESTING_DIRECTORY = os.path.abspath(LOAD_TESTING_DIRECTORY)
