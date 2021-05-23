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


recommenderWeighting = 0.015263
newsWeighting = 0
cartWeighting = 1


class SensitivityTestingExperiment(Experiment):

    iterationErrorsQueue = queue.Queue(maxsize=1)

    def __init__(
        self,
        config: Config,
        num_users: int,
    ):
        super().__init__()
        self.config = config
        self.num_users = num_users

    def run(self):
        k6_env = os.environ.copy()

        # Ensure sessions are reused between VU iterations.
        k6_env["K6_NO_COOKIES_RESET"] = "true"
        k6_env["K6_HOST"] = self.config.KUBEDIM_HOST
        k6_env["K6_PORT"] = self.config.DIMMER_PORT

        component_weightings = self.__generate_component_weightings()
        iterationBar = bar.ProgressBar(redirect_stdout=True)
        for i in iterationBar(range(len(component_weightings))):
            weightings = component_weightings[i]
            iterationBar.update(force=True)
            thread = threading.Thread(target=self.__run, args=(k6_env, weightings))
            thread.daemon = True
            thread.start()

            while thread.is_alive():
                time.sleep(0.25)
                iterationBar.update(force=True)

            if self.iterationErrorsQueue.qsize() > 0:
                print("Stopping early due to error")
                exit()

        print("Complete!")

    def __generate_component_weightings(self):
        default_weightings = [
            [
                {"Path": "/recommender", "Probability": recommenderWeighting},
                {"Path": "/news", "Probability": newsWeighting},
                {"Path": "/cart", "Probability": cartWeighting},
            ]
        ]

        recommender_weightings = [
            [
                {"Path": "/recommender", "Probability": weighting / 100.0},
                {"Path": "/news", "Probability": newsWeighting},
                {"Path": "/cart", "Probability": cartWeighting},
            ]
            for weighting in range(0, 101, 5)
        ]

        news_weightings = [
            [
                {"Path": "/recommender", "Probability": recommenderWeighting},
                {"Path": "/news", "Probability": weighting / 100.0},
                {"Path": "/cart", "Probability": cartWeighting},
            ]
            for weighting in range(0, 101, 5)
        ]

        cart_weightings = [
            [
                {"Path": "/recommender", "Probability": recommenderWeighting},
                {"Path": "/news", "Probability": newsWeighting},
                {"Path": "/cart", "Probability": weighting / 100.0},
            ]
            for weighting in range(0, 101, 5)
        ]

        return (
            default_weightings
            + recommender_weightings
            + news_weightings
            + cart_weightings
        )

    def __run(self, k6_env, weightings):
        try:
            if not api_client.empty_cart(self.config).ok:
                raise RuntimeError(f"unable to empty cart")
            if not api_client.seed_cart(self.config, 200000).ok:
                raise RuntimeError(f"unable to seed cart")
            if not api_client.set_dimming_mode(
                self.config, api_client.DIMMING_MODE_DIMMING
            ).ok:
                raise RuntimeError(f"unable to set dimming mode")

            if not api_client.set_component_weightings(self.config, weightings).ok:
                raise RuntimeError(f"unable to set component weightings")

            output_path = generate_output_path(suffix="k6")

            k6_env["MAX_VUS"] = str(self.num_users)
            k6_env["RAMP_UP_TIME"] = "10s"
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
                raise RuntimeError(f"unable to run k6, stderr =\n\t{k6_process.stderr}")

            time.sleep(10)
        except Exception as e:
            print(e)
            self.iterationErrorsQueue.put(1)
            exit()
