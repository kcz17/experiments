import json
import os
import queue
import subprocess
import threading

import time
from progressbar import bar

import api_client
from config import Config
from experiments.experiment import Experiment
from helpers import generate_output_path


class FlashCrowdExperiment(Experiment):

    iterationErrorsQueue = queue.Queue(maxsize=1)

    def __init__(
        self,
        config: Config,
        iterations: int,
    ):
        super().__init__()
        self.config = config
        self.iterations = iterations

    def run(self):
        k6_env = os.environ.copy()

        # Ensure sessions are reused between VU iterations.
        k6_env["K6_NO_COOKIES_RESET"] = "true"
        k6_env["K6_HOST"] = self.config.KUBEDIM_HOST
        k6_env["K6_PORT"] = self.config.DIMMER_PORT

        iteration_metrics = []

        iterationBar = bar.ProgressBar(redirect_stdout=True)
        for _ in iterationBar(range(self.iterations)):
            iterationBar.update(force=True)
            thread = threading.Thread(
                target=self.__run, args=(k6_env, iteration_metrics)
            )
            thread.daemon = True
            thread.start()

            while thread.is_alive():
                time.sleep(0.25)
                iterationBar.update(force=True)

            if self.iterationErrorsQueue.qsize() > 0:
                print("Stopping early due to error")
                exit()

        with open(generate_output_path(suffix="constant-load"), "w") as output_file:
            json.dump(iteration_metrics, output_file)
        print("Complete:")
        print(iteration_metrics)

    def __run(self, k6_env, iteration_metrics):
        try:
            if not api_client.empty_cart(self.config).ok:
                raise RuntimeError(f"unable to empty cart")
            if not api_client.seed_cart(self.config, 200000).ok:
                raise RuntimeError(f"unable to seed cart")
            if not api_client.set_dimming_mode(
                self.config, api_client.DIMMING_MODE_DIMMING
            ).ok:
                raise RuntimeError(f"unable to set dimming mode")
            if not api_client.clear_component_weightings(self.config).ok:
                raise RuntimeError(f"unable to clear component weightings")

            output_path = generate_output_path(suffix="k6")

            k6_env["MIN_VUS"] = str(100)
            k6_env["MAX_VUS"] = str(280)
            k6_env["RAMP_TIME"] = "2m"
            k6_env["PEAK_TIME"] = "2m"
            k6_env["TROUGH_TIME"] = "2m"
            k6_env["K6_OUTPUT_PATH"] = output_path

            k6_process = subprocess.run(
                ["ulimit -n 8192; k6 run dist/flashCrowdExternallyOrchestrated.js"],
                env=k6_env,
                cwd=self.config.ABS_LOAD_TESTING_DIRECTORY,
                capture_output=True,
                shell=True,
            )

            if k6_process.returncode != 0:
                raise RuntimeError(f"unable to run k6, stderr =\n\t{k6_process.stderr}")

            with open(output_path, "r") as output_file:
                k6_metrics = json.load(output_file)

                metrics = {}
                if "attrition" in k6_metrics["metrics"]:
                    metrics["attrition"] = k6_metrics["metrics"]["attrition"]["values"][
                        "count"
                    ]
                if "items_checked_out" in k6_metrics["metrics"]:
                    metrics["items_checked_out"] = k6_metrics["metrics"][
                        "items_checked_out"
                    ]["values"]["count"]
                if "recommendations_checked_out" in k6_metrics["metrics"]:
                    metrics["recommendations_checked_out"] = k6_metrics["metrics"][
                        "recommendations_checked_out"
                    ]["values"]["count"]

                iteration_metrics.append(metrics)

            time.sleep(10)
        except Exception as e:
            print(e)
            self.iterationErrorsQueue.put(1)
            exit()
