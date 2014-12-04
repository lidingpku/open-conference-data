import json
import os
import sys
import re
import logging
import datetime


def path_sibling(name_sibling=None, file_home=__file__):
    if name_sibling:
        return os.path.join(path_sibling(file_home=file_home), name_sibling)
    else:
        return os.path.dirname(os.path.abspath(file_home))

def config_load(name_config='config.json', file_home=__file__):
    # load config file
    filename = path_sibling(name_sibling=name_config, file_home=file_home)

    with open(filename) as f:
        config = json.load(f)

    return config


def logger_add(obj):
    obj.logger= logging.getLogger(obj.__class__.__name__)

def logger_init(config):
    option ={}
    option["format"] = '[%(levelname)s][%(name)s][%(funcName)s][%(asctime)s]%(message)s'
    option["level"] = logging.INFO

    if 'logfile' in config and config["logfile"]:
        # "use file logging"
        hdlr = logging.FileHandler(config["logfile"])
        formatter = logging.Formatter(option["format"])
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(option["level"])
        __getlogger().info("init logging on file {}".format(config["logfile"]))
    else:
        logging.basicConfig(format=option["format"], level=option["level"])
        __getlogger().info("init logging on console")


def __getlogger():
    return logging.getLogger("mboxutil")

def main():
    config = config_load()
    logger_init(config)
    __getlogger().info( config )

if __name__ == "__main__":
    main()
