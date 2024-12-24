#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
application config value
"""

import os
import re

import requests
import yaml


class config:
    SERVICE_NAME = "adt"

    CONFIG = "config"
    CONFIG_PATH = "config_path"

    # host
    HOST_ENV = "host_env"
    REMOTE_HOST_ENV = "remote_host_env"
    USER = "user"
    PASSWORD = "password"
    HOST = "host"

    DEPLOY = "deploy"
    PRE_ACT = "pre_action"
    POST_ACT = "post_action"


def load_yaml(yaml_file):
    if os.path.exists(yaml_file):
        conf_data = yaml.safe_load(open(yaml_file).read())
    elif bool(re.search(r"https?", yaml_file)):
        #  parsing remote yaml
        yaml_request = requests.get(yaml_file)
        yaml_request.encoding = None
        conf_data = yaml.safe_load(yaml_request.text)
    else:
        raise Exception("adt::config : (Exception) config file not exist")
    return conf_data


def is_exist(path):
    if (path) is None or (not os.path.exists(path)):
        return False
    return True


def url_exists(location):
    try:
        r = requests.get(location)
        if r.status_code == 200:
            return True
        else:
            print(
                f"adt::config : response status code is not 200 (actual_status_code: {r.status_code})"
            )
            return False
    except ConnectionError:
        print(
            f"adt::config : (ConnectionError) site does not exist (location: {location})"
        )
        return False


def is_host(conf_data):
    test_data = conf_data[config.CONFIG][config.TEST]

    env = test_data.get(config.DRIVER_TYPE, "pod")

    if env in "host":
        return True
    else:
        return False
