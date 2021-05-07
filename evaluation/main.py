import json
import os
import pathlib
import subprocess
from dataclasses import dataclass

import dotenv
import time

dotenv.load_dotenv()


@dataclass
class Config:
    KUBEDIM_HOST = os.getenv("KUBEDIM_HOST", "afcluster01.doc.ic.ac.uk")
    DIMMER_PORT = os.getenv("DIMMER_PORT", "30002")
    ADMIN_PORT = os.getenv("ADMIN_PORT", "30003")

    LOAD_TESTING_DIRECTORY = os.getenv("LOAD_TESTING_DIRECTORY", "../../load-testing")
    ABS_LOAD_TESTING_DIRECTORY = os.path.abspath(LOAD_TESTING_DIRECTORY)
    MAX_VUS = os.getenv("MAX_VUS", "1")
    RAMP_UP_TIME = os.getenv("RAMP_UP_TIME", "1s")
    CONSTANT_TIME = os.getenv("CONSTANT_TIME", "1s")


if __name__ == "__main__":
    config = Config()
    print("Check the following provided configuration values before proceeding:")
    print(f"\tKUBEDIM_HOST: {config.KUBEDIM_HOST}")
    print(f"\tDIMMER_PORT: {config.DIMMER_PORT}")
    print(f"\tADMIN_PORT: {config.ADMIN_PORT}")
    print(f"\tLOAD_TESTING_DIRECTORY: {config.LOAD_TESTING_DIRECTORY}")
    print(f"\t\twhich resolves to {config.ABS_LOAD_TESTING_DIRECTORY}")
    print(f"\tMAX_VUS: {config.MAX_VUS}")
    print(f"\tRAMP_UP_TIME: {config.RAMP_UP_TIME}")
    print(f"\tCONSTANT_TIME: {config.CONSTANT_TIME}")

    input("\nPress Enter to continue or Ctrl + C to exit...\n")

    if subprocess.call(["which", "k6"], stdout=subprocess.DEVNULL) != 0:
        print("The k6 binary is not installed. Please try again.")

    p = subprocess.Popen(
        ["/usr/bin/which", "npx"],
        cwd=config.LOAD_TESTING_DIRECTORY,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p.communicate()
    if p.returncode != 0:
        print(
            "The npx binary is not installed under the load testing directory. Please try again."
        )

    print("Building load testing tool...")
    webpackProcess = subprocess.run(
        ["npx", "webpack"], cwd=config.ABS_LOAD_TESTING_DIRECTORY, capture_output=True
    )
    if webpackProcess.returncode != 0:
        print(f"unable to run npx webpack, stderr =\n\t{webpackProcess.stderr}")

    print("Running k6...")
    k6Env = os.environ.copy()

    # Ensure sessions are reused between VU iterations.
    k6Env["K6_NO_COOKIES_RESET"] = "true"
    k6Env["K6_HOST"] = config.KUBEDIM_HOST
    k6Env["K6_PORT"] = config.DIMMER_PORT
    k6Env["MAX_VUS"] = config.MAX_VUS
    k6Env["RAMP_UP_TIME"] = config.RAMP_UP_TIME
    k6Env["CONSTANT_TIME"] = config.CONSTANT_TIME

    # Set a dynamic output path.
    outputPath = (
        str(pathlib.Path(__file__).parent.absolute()) + f"/out/{time.time()}.json"
    )
    k6Env["K6_OUTPUT_PATH"] = outputPath

    k6Process = subprocess.run(
        ["k6", "run", "dist/constantLoadExternallyOrchestrated.js"],
        env=k6Env,
        cwd=config.ABS_LOAD_TESTING_DIRECTORY,
        capture_output=True,
    )
    if k6Process.returncode != 0:
        print(f"unable to run k6, stderr =\n\t{k6Process.stderr}")

    with open(outputPath, "r") as outputFile:
        metrics = json.load(outputFile)
        print(metrics)
