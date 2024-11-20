import subprocess
import sys


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def check_and_install_packages(requirements_file):
    with open(requirements_file, "r") as file:
        required_packages = file.read().splitlines()

    installed_any = False
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"{package} not found. Installing...")
            install(package)
            installed_any = True

    if installed_any:
        print("#" * 100)
        print("All requirements added")
        print("#" * 100)
    else:
        print("#" * 100)
        print("Nothing to add - you're all good")
        print("#" * 100)


if __name__ == "__main__":
    requirements_file = "requirements.txt"
    check_and_install_packages(requirements_file)
