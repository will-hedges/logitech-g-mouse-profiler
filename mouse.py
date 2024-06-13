#!/usr/bin/env python3
# mouse.py - a Python class representing a Logitech G mouse

from pathlib import Path
import pickle
import re
import subprocess


def get_bash_stdout(cmd_str):
    """
    Runs a bash command and returns the decoded standard output
        Params:
            cmd_str (str): a bash command, ex. "ratbagctl list"
        Returns:
            rbc_out (str): the decoded standard output (stdout) of cmd_str
    """
    cmd_lst = [c.strip() for c in cmd_str.split(" ")]
    rbc_out = subprocess.run(cmd_lst, stdout=subprocess.PIPE).stdout.decode()
    return rbc_out


def get_mouse_alias_and_model():
    """
    Parses the ratbagctl short name of the connected mouse and the mouse model
        Returns:
            (alias, model)
            alias (str): the ratbagctl name of the mouse, ex. "sleeping-puppy"
            model (str): the model short name/number of the mouse, ex. "G403"
    """
    rbc_out = get_bash_stdout("ratbagctl list")
    mouse_re = re.compile(r"([a-z-]+):.*(G\d{3}|G Pro).*")
    mouse_mo = mouse_re.match(rbc_out)
    alias = mouse_mo.group(1).lower()
    model = mouse_mo.group(2).lower()
    return (alias, model)


def get_button_count(alias):
    """
    Gets the number of buttons on the connected mouse
        Params:
            alias (str): the ratbagctl short name of the connected mouse
        Returns:
            btn_ct (int): the number of buttons the mouse has
    """
    btn_ct = int(get_bash_stdout(f"ratbagctl {alias} button count"))
    return btn_ct


def get_all_shell_scripts_in(fp):
    """
    Creates a list of all the the .sh scripts within a folder

        Params:
            fp (Path): the Path of the mouse model
        Returns:
            profiles (list(Path)): a list of all Paths in fp with the .sh ext
    """
    profile_glob = sorted(fp.glob("*.sh"))
    profiles = [Path(profile) for profile in profile_glob]
    return profiles


def generate_default_sh(script_path, profile_dict):
    """
    Generates the text/string for the default.sh mouse profile and writes to file
        Params:
            script_path (Path): the Path to default.sh for the mouse model
            profile_dict (dict): a dict containing the profile key-value pairs
    """
    # create 'default.sh' with touch
    # generate the actual profile script with read_active_profile
    # write the script to file
    # give the new .sh file a+x permissions
    # subprocess.run(["chmod", "a+x", current_profile])
    # return the fp
    return


# NOTE json may be a better option for serialization here, as you could go
#   in and edit it manually rather than relying on pickle and rb/wb
def load_pickled_profile(fp):
    """
    Pulls in the path of the last set profile from the pickle file
        or creates a pickle file if it does not already exist

        Params:
            fp (Path): the Path of the mouse model directory
        Returns:
            current_profile (Path): TODO
    """

    pickle_path = Path(fp / f"{fp.name}.pickle")
    try:
        with open(pickle_path, "rb") as pf:
            current_profile = pickle.load(pf)
    except (FileNotFoundError, EOFError):
        pickle_path.touch()
        current_profile = Path(fp / "default.sh")
        current_profile.touch()
        # TODO should make the default.sh here

    return current_profile


def save_pickled_profile(pickle_fp, profile_fp):
    """
    Saves the path of the currently set profile .sh to pickle file
        Params:
            pickle_fp (Path): the Path to the pickle file
            profile_fp (Path): the Path to the profile shell script
    """
    with open(pickle_fp, "wb") as pf:
        pickle.dump(profile_fp, pf)
    return


class Mouse:
    """
    A class to represent a Logitech G mouse

        Attrs:
            alias (str): the ratbagctl short name of the mouse
            model (str): the Logitech model name/number of the mouse
            button_count (int): the number of buttons the mouse has
            folder (Path): the dir containing profile scripts and pickle file for the mouse
            profiles (list): a list of Path objects of all the local mouse profile scripts

        Methods:
            read_active_profile TODO
            cycle_profile TODO
    """

    def __init__(self):
        self.alias, self.model = get_mouse_alias_and_model()
        self.button_count = get_button_count(self.alias)
        self.folder = Path(__file__).parent / "models" / self.model
        # if the model's folder doesn't exist, create it
        self.folder.mkdir(parents=True, exist_ok=True)
        # self.current_profile = load_pickled_profile(self.folder)
        self.profiles = get_all_shell_scripts_in(self.folder)
        return

    def read_active_profile(self):
        """
        Creates a dictionary from the current mouse settings

            Returns:
                mouse_profile (dict) TODO
        """
        report_rate = int(get_bash_stdout(f"ratbagctl {self.alias} rate get"))

        resolutions = []
        res_idx = 0
        res_re = re.compile(r"\d:\s(\d{,5})dpi.*")
        while True:
            res_out = get_bash_stdout(
                f"ratbagctl {self.alias} resolution {res_idx} get"
            )
            res_mo = res_re.match(res_out)
            if res_mo:
                resolutions.append(res_mo.group(1))
                res_idx += 1
            else:
                break

        buttons = []
        btn_re = re.compile(r".*'(.*)'.*")
        for i in range(self.button_count):
            btn_out = get_bash_stdout(f"ratbagctl {self.alias} button {i} get").strip()
            btn_mo = btn_re.match(btn_out)
            buttons.append(
                btn_mo.group(1)
                .replace("↕", "KEY_")
                .replace("↓", "+KEY_")
                .replace("↑", "-KEY_")
            )

        leds = []
        led_idx = 0
        led_re = re.compile(
            r"LED: (\d), depth: rgb, mode: (on|off|cycle|breathing), color: (\w{6})|, duration: (\d{,5}), brightness: (\d{,3})"
        )
        while True:
            led_out = get_bash_stdout(f"ratbagctl {self.alias} led {led_idx} get")
            led_mo = led_re.match(led_out)
            if led_mo:
                leds.append(led_mo.groups())
                led_idx += 1
            else:
                break

        mouse_profile = {
            "report_rate": report_rate,
            "resolutions": resolutions,
            "buttons": buttons,
            "leds": leds,
        }

        return mouse_profile

    def cycle_profile(self):
        """
        Cycles through and runs the "next" indexed profile shell script
            then saves the current profile to the pickle file
        """
        current_profile = load_pickled_profile(self.folder)
        current_idx = self.profiles.index(current_profile)
        try:
            current_profile = self.profiles[current_idx + 1]
        except IndexError:
            current_profile = self.profiles[0]
        self.current_profile = current_profile
        # run the new profile script with subprocess
        subprocess.run(["sh", current_profile])
        # write out the new profile to pickle
        pickle_fp = Path(self.folder / f"{self.model}.pickle")
        save_pickled_profile(pickle_fp, current_profile)
        return
