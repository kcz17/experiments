import json
import os
import subprocess

import api_client
from config import Config
from helpers import generate_output_path


def dimmer_disabled_saturation(config: Config):
    k6_env = os.environ.copy()

    # Ensure sessions are reused between VU iterations.
    k6_env["K6_NO_COOKIES_RESET"] = "true"
    k6_env["K6_HOST"] = config.KUBEDIM_HOST
    k6_env["K6_PORT"] = config.DIMMER_PORT

    vu_metrics = {}

    for maxVUs in range(200, 351, 20):
        api_client.empty_cart(config)
        api_client.seed_cart(config, 200000)
        api_client.set_dimming_mode(config, api_client.DIMMING_MODE_DISABLED)

        output_path = generate_output_path(suffix="k6")

        k6_env["MAX_VUS"] = str(maxVUs)
        k6_env["RAMP_UP_TIME"] = "10s"
        k6_env["CONSTANT_TIME"] = "3m"
        k6_env["K6_OUTPUT_PATH"] = output_path

        k6_process = subprocess.run(
            ["k6", "run", "dist/constantLoadExternallyOrchestrated.js"],
            env=k6_env,
            cwd=config.ABS_LOAD_TESTING_DIRECTORY,
            capture_output=True,
        )

        if k6_process.returncode != 0:
            print(f"unable to run k6, stderr =\n\t{k6_process.stderr}")

        print(k6_process.stdout)
        with open(output_path, "r") as outputFile:
            metrics = json.load(outputFile)
            vu_metrics[maxVUs] = metrics["metrics"]["http_req_duration"]["values"]

    with open(generate_output_path(suffix="dimmer-disabled-saturation"), "w") as output_file:
        json.dump(vu_metrics, output_file)
