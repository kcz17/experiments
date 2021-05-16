import subprocess

import api_client
from config import Config
from experiments.constant_load_experiment import ConstantLoadExperiment
from experiments.experiment import Experiment
from experiments.flash_crowd_experiment import FlashCrowdExperiment
from experiments.saturation_experiment import SaturationExperiment

if __name__ == "__main__":
    config = Config()
    print("Check the following provided environment variables before proceeding:")
    print(f"\tKUBEDIM_HOST: {config.KUBEDIM_HOST}")
    print(f"\tDIMMER_PORT: {config.DIMMER_PORT}")
    print(f"\tADMIN_PORT: {config.ADMIN_PORT}")
    print(f"\tCARTS_RESEEDER_PORT: {config.CARTS_RESEEDER_PORT}")
    print(f"\tLOAD_TESTING_DIRECTORY: {config.LOAD_TESTING_DIRECTORY}")
    print(f"\t\twhich resolves to {config.ABS_LOAD_TESTING_DIRECTORY}")

    print(f"\nAvailable experiments:")
    print(f"\t[1] Gather data to infer saturation with dimmer is disabled")
    print(f"\t[2] Gather data to infer saturation with baseline dimming")
    print(f"\t[3] Constant load, no dimming, 280 users, 30 mins, no repeats")
    print(f"\t[4] Constant load, baseline dimming, 280 users, 30 mins, no repeats")
    print(f"\t[5] Flash crowd, baseline dimming, 280 users, 18 mins, no repeats")
    print(f"\t[6] Constant load, no dimming, 280 users, 30 mins, 5 repeats")
    print(f"\t[7] Constant load, baseline dimming, 280 users, 30 mins, 5 repeats")
    print(
        f"\t[8] Constant load, dimming with component weightings, 280 users, 30 mins, 5 repeats"
    )
    print(
        f"\t[9] Constant load, dimming with profiling, no component weightings set, 280 users, 30 mins, 5 repeats"
    )
    print(
        f"\t[10] Constant load, dimming with profiling, component weightings set, 280 users, 30 mins, 5 repeats"
    )
    print(f"\t[11] Profiling edge case, all low")
    print(f"\t[12] Profiling edge case, all high")
    choice = input("\nEnter the number for the experiment you want to run: ")

    experiment = Experiment()
    if int(choice) == 1:
        experiment = SaturationExperiment(config, is_dimming_enabled=False)
    elif int(choice) == 2:
        experiment = SaturationExperiment(config, is_dimming_enabled=True)
    elif int(choice) == 3:
        experiment = ConstantLoadExperiment(
            config,
            num_users=280,
            duration="30m",
            iterations=1,
            dimming_mode=api_client.DIMMING_MODE_DISABLED,
        )
    elif int(choice) == 4:
        experiment = ConstantLoadExperiment(
            config,
            num_users=280,
            duration="30m",
            iterations=1,
            dimming_mode=api_client.DIMMING_MODE_DIMMING,
        )
    elif int(choice) == 5:
        experiment = FlashCrowdExperiment(
            config,
            iterations=1,
        )
    elif int(choice) == 6:
        experiment = ConstantLoadExperiment(
            config,
            num_users=280,
            duration="30m",
            iterations=5,
            dimming_mode=api_client.DIMMING_MODE_DISABLED,
        )
    elif int(choice) == 7:
        experiment = ConstantLoadExperiment(
            config,
            num_users=280,
            duration="30m",
            iterations=5,
            dimming_mode=api_client.DIMMING_MODE_DIMMING,
        )
    elif int(choice) == 8:
        experiment = ConstantLoadExperiment(
            config,
            num_users=280,
            duration="30m",
            iterations=5,
            dimming_mode=api_client.DIMMING_MODE_DIMMING,
            use_component_weightings=True,
        )
    elif int(choice) == 9:
        experiment = ConstantLoadExperiment(
            config,
            num_users=280,
            duration="30m",
            iterations=5,
            dimming_mode=api_client.DIMMING_MODE_PROFILING,
        )
    elif int(choice) == 10:
        experiment = ConstantLoadExperiment(
            config,
            num_users=280,
            duration="30m",
            iterations=5,
            dimming_mode=api_client.DIMMING_MODE_PROFILING,
            use_component_weightings=True,
        )
    elif int(choice) == 11:
        experiment = ConstantLoadExperiment(
            config,
            num_users=280,
            duration="30m",
            iterations=1,
            dimming_mode=api_client.DIMMING_MODE_PROFILING,
            override_all_scenarios="browsing",
        )
    elif int(choice) == 12:
        experiment = ConstantLoadExperiment(
            config,
            num_users=280,
            duration="30m",
            iterations=1,
            dimming_mode=api_client.DIMMING_MODE_PROFILING,
            override_all_scenarios="buying",
        )
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
