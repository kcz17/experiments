import json
import os
import subprocess

import time
from progressbar import progressbar

import api_client
from config import Config
from experiments.experiment import Experiment
from helpers import generate_output_path


class SaturationExperiment(Experiment):
    def __init__(self, config: Config, is_dimming_enabled: bool):
        super().__init__()
        self.config = config
        self.is_dimming_enabled = is_dimming_enabled
        self.dimming_mode = (
            api_client.DIMMING_MODE_DIMMING
            if is_dimming_enabled
            else api_client.DIMMING_MODE_DISABLED
        )

    def run(self):
        k6_env = os.environ.copy()

        # Ensure sessions are reused between VU iterations.
        k6_env["K6_NO_COOKIES_RESET"] = "true"
        k6_env["K6_HOST"] = self.config.KUBEDIM_HOST
        k6_env["K6_PORT"] = self.config.DIMMER_PORT

        vu_metrics = {}

        for max_vus in progressbar(range(200, 400, 10), redirect_stdout=True):
            print(f"\tStarting iteration with VUs = {max_vus}")
            if not api_client.empty_cart(self.config).ok:
                print(f"unable to empty cart")
                exit()
            if not api_client.seed_cart(self.config, 200000).ok:
                print(f"unable to seed cart")
                exit()
            if not api_client.set_dimming_mode(self.config, self.dimming_mode).ok:
                print(f"unable to set dimming mode")
                exit()
            if self.is_dimming_enabled:
                # We do not want to run baseline dimming with component
                # weightings enabled.
                if not api_client.clear_component_weightings(self.config).ok:
                    print(f"unable to clear component weightings")
                    exit()

            output_path = generate_output_path(suffix="k6")

            k6_env["MAX_VUS"] = str(max_vus)
            k6_env["RAMP_UP_TIME"] = "20s"
            k6_env["CONSTANT_TIME"] = "4m"
            k6_env["K6_OUTPUT_PATH"] = output_path

            k6_process = subprocess.run(
                ["ulimit -n 8192; k6 run dist/constantLoadExternallyOrchestrated.js"],
                env=k6_env,
                cwd=self.config.ABS_LOAD_TESTING_DIRECTORY,
                capture_output=True,
                shell=True,
            )

            if k6_process.returncode != 0:
                print(f"unable to run k6, stderr =\n\t{k6_process.stderr}")
                exit()

            with open(output_path, "r") as output_file:
                metrics = json.load(output_file)
                vu_metrics[max_vus] = metrics["metrics"]["http_req_duration"]["values"]

            time.sleep(10)

        with open(
            generate_output_path(suffix="dimmer-disabled-saturation"), "w"
        ) as output_file:
            json.dump(vu_metrics, output_file)

        print("Complete")
