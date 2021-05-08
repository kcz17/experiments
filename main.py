import subprocess

from config import Config
from experiments import Experiment, DimmerDisabledSaturation

if __name__ == "__main__":
    config = Config()
    print("Check the following provided configuration values before proceeding:")
    print(f"\tKUBEDIM_HOST: {config.KUBEDIM_HOST}")
    print(f"\tDIMMER_PORT: {config.DIMMER_PORT}")
    print(f"\tADMIN_PORT: {config.ADMIN_PORT}")
    print(f"\tCARTS_RESEEDER_PORT: {config.CARTS_RESEEDER_PORT}")
    print(f"\tLOAD_TESTING_DIRECTORY: {config.LOAD_TESTING_DIRECTORY}")
    print(f"\t\twhich resolves to {config.ABS_LOAD_TESTING_DIRECTORY}")

    print(f"\nAvailable experiments:")
    print(f"\t[1] Gather data to infer saturation with dimmer is disabled")
    choice = input("\nEnter the number for the experiment you want to run: ")

    experiment = Experiment()
    if int(choice) == 1:
        experiment = DimmerDisabledSaturation(config)
    else:
        print("Invalid choice entered. Exiting.")
        exit()

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

    print("Running experiment...")
    experiment.run()
