import configparser
import os
from pathlib import Path


class ConfigHelper:
    def __init__(self, config_file="./config.ini"):
        root_dir = str(Path(__file__).parent.parent)
        config_path = os.path.join(root_dir, config_file)

        self.config = configparser.ConfigParser()
        self.config.read(config_path)

    def get_config(self, tag):
        return self.config[tag]

    def has_name(self, tag, name):
        return name in self.config[tag].keys()
