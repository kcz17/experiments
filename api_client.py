import backoff
import requests as requests

from config import Config

DIMMING_MODE_DISABLED = "Disabled"
DIMMING_MODE_DIMMING = "Dimming"
DIMMING_MODE_PROFILING = "DimmingWithProfiling"
DIMMING_MODE_ONLINE_TRAINING = "DimmingWithOnlineTraining"

DEFAULT_COMPONENT_WEIGHTINGS = [
    {"Path": "/recommender", "Probability": 0.015263},
    {"Path": "/news", "Probability": 0},
    {"Path": "/cart", "Probability": 1},
]


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
    return requests.put(
        f"http://{config.KUBEDIM_HOST}:{config.CARTS_RESEEDER_PORT}/db/{rows}"
    )


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=3,
)
def set_dimming_mode(config: Config, mode: str):
    return requests.post(
        f"http://{config.KUBEDIM_HOST}:{config.ADMIN_PORT}/mode", json={"Mode": mode}
    )


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=3,
)
def set_component_weightings(config: Config, weightings):
    if weightings is None:
        weightings = DEFAULT_COMPONENT_WEIGHTINGS
    return requests.post(
        f"http://{config.KUBEDIM_HOST}:{config.ADMIN_PORT}/probabilities",
        json=weightings,
    )


@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.Timeout, requests.exceptions.ConnectionError),
    max_tries=3,
)
def clear_component_weightings(config: Config):
    return requests.delete(
        f"http://{config.KUBEDIM_HOST}:{config.ADMIN_PORT}/probabilities"
    )
