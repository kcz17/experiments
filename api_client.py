import backoff
import requests as requests

from config import Config

DIMMING_MODE_DISABLED = "disabled"
DIMMING_MODE_DIMMING = "dimming"


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=3,
)
def empty_cart(config: Config):
    return requests.delete(
        f"http://{config.KUBEDIM_HOST}:{config.CARTS_RESEEDER_PORT}/db"
    )


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=3,
)
def seed_cart(config: Config, rows: int):
    return requests.post(
        f"http://{config.KUBEDIM_HOST}:{config.CARTS_RESEEDER_PORT}/db/{rows}"
    )


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=3,
)
def set_dimming_mode(config: Config, mode: str):
    return requests.post(
        f"http://{config.KUBEDIM_HOST}:{config.ADMIN_PORT}/mode", data={"Mode": mode}
    )
