import json
import os
import subprocess

import sys
from progressbar import progressbar

import api_client
from config import Config
from experiments.experiment import Experiment
from helpers import generate_output_path


class ConstantLoadExperiment(Experiment):
    def __init__(
        self,
        config: Config,
        num_users: int,
        duration: str,
        iterations: int,
        dimming_mode: str,
        use_component_weightings: bool = False,
    ):
        super().__init__()
        self.config = config
        self.num_users = num_users
        self.duration = duration
        self.iterations = iterations
        self.dimming_mode = dimming_mode
        self.use_component_weightings = use_component_weightings

    def run(self):
        k6_env = os.environ.copy()

        # Ensure sessions are reused between VU iterations.
        k6_env["K6_NO_COOKIES_RESET"] = "true"
        k6_env["K6_HOST"] = self.config.KUBEDIM_HOST
        k6_env["K6_PORT"] = self.config.DIMMER_PORT

        iteration_metrics = []

        for _ in progressbar(range(self.iterations), redirect_stdout=True):
            if not api_client.empty_cart(self.config).ok:
                print(f"unable to empty cart")
                exit()
            if not api_client.seed_cart(self.config, 200000).ok:
                print(f"unable to seed cart")
                exit()
            if not api_client.set_dimming_mode(self.config, self.dimming_mode).ok:
                print(f"unable to set dimming mode")
                exit()

            if self.use_component_weightings:
                if not api_client.set_component_weightings(self.config).ok:
                    print(f"unable to set component weightings")
                    exit()
            else:
                if not api_client.clear_component_weightings(self.config).ok:
                    print(f"unable to clear component weightings")
                    exit()

            output_path = generate_output_path(suffix="k6")

            k6_env["MAX_VUS"] = str(self.num_users)
            k6_env["RAMP_UP_TIME"] = "10s"
            k6_env["CONSTANT_TIME"] = self.duration
            k6_env["K6_OUTPUT_PATH"] = output_path

            k6_process = subprocess.Popen(
                ["k6", "run", "dist/constantLoad.js"],
                env=k6_env,
                cwd=self.config.ABS_LOAD_TESTING_DIRECTORY,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            while True:
                out = k6_process.stdout.read(1)
                if out == '' and k6_process.poll() is not None:
                    break
                if out != '':
                    sys.stdout.write(out)
                    sys.stdout.flush()

            if k6_process.returncode != 0:
                print(f"unable to run k6, stderr =\n\t{k6_process.stderr}")
                exit()

            # with open(output_path, "r") as output_file:
            #     metrics = json.load(output_file)
            #     iteration_metrics.append(metrics)

        # with open(generate_output_path(suffix="constant-load"), "w") as output_file:
        #     json.dump(iteration_metrics, output_file)
