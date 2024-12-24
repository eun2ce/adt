#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
deployment 모듈은 설정파일에 정의된 airtifacts를 배포하는 기능을 제공한다.
"""

import os
import time
from fabric.api import settings, local, env

from run import run, put
from itertools import izip_longest
import zookeeper

import config
from adt.application.config import config as conf


def copy_resource(test_conf, artifacts):
    """
    테스트에 필요한 data를 host vm의 test_dir경로로 복사한다.
    :param test_conf: it 환경
    :param artifacts:  chart정보
    :return:
    """
    resource_path = test_conf.get(conf.RESOURCES)
    test_dir = conf.TEST_DIR

    run("mkdir -p {}".format(test_dir))
    if config.is_exist(resource_path) is True:
        # resource 경로에 있는 내용과 설정 파일을 host vm으로 전달한다.
        put(resource_path, test_dir)

    for artifact in artifacts:
        # local chart 면 복사
        chart_path = artifact.get(conf.CHART)
        if config.is_exist(chart_path) is True:
            put(chart_path, test_dir)

        # local value면 복사
        value_path = artifact.get(conf.VALUES)
        if config.is_exist(value_path) is True:
            dir_path, basename = os.path.split(value_path)
            run("mkdir -p {}/{}".format(test_dir, dir_path))
            put(value_path, "{}/{}".format(test_dir, value_path))


def pre_action(deploy_conf):
    """
    배포전 action을 실행한다.
    :param deploy_conf:
    :return:
    """
    if deploy_conf is None:
        return

    pre_act = deploy_conf.get(conf.PRE_ACT)
    execute_actions(pre_act)


def post_action(deploy_conf):
    """
    배포후 action을 실행한다.
    :return:
    """
    if deploy_conf is None:
        return

    post_act = deploy_conf.get(conf.POST_ACT)
    execute_actions(post_act)


def execute_actions(actions):
    """
    action을 실행한다.
    :param actions: action의 배열
    :return:
    """
    if actions is None:
        return
    elif len(actions) == 0:
        return

    with settings(warn_only=True):
        for act in actions:
            run(act)


def deploy_ansible(artifact, host_env):
    """
    ansible 배포코드 실행
    :param conf_data:
    :param host_env:
    :return:
    """
    if artifact is None:
        return

    inventory = artifact.get(conf.INVENTORY)
    playbook = artifact.get(conf.PLAYBOOK)

    if (inventory is None) or (playbook is None):
        return

    if ":" in host_env.get(conf.HOST):
        host, port = host_env.get(conf.HOST).split(":")
    else:
        host = host_env.get(conf.HOST)
        port = 22

    # ansible 배포 시작
    local("ansible-playbook -i {} {}".format(inventory, playbook))


def deploy_helm(artifact_conf):
    if artifact_conf is None:
        print("artifact is None")
        return

    name = artifact_conf.get(conf.RELEASE_NAME)
    namespace = artifact_conf.get(conf.NAMESPACE)
    values = get_value(artifact_conf)
    chart = get_chart(artifact_conf)
    version = get_version(artifact_conf)

    ret = run("helm list -n {} ".format(namespace))
    while "refused" in ret:
        time.sleep(10)
        ret = run("helm list -n {} ".format(namespace))

    if name in ret:
        run(
            "helm upgrade {} {} --namespace {} -f {} {}".format(
                name, chart, namespace, values, version
            )
        )
    else:
        run(
            "helm install {} {} --namespace {} -f {} {}".format(
                name, chart, namespace, values, version
            )
        )

    run("helm history {} -n {}".format(name, namespace))


def rollback_artifact(artifact_conf):
    name = artifact_conf[conf.RELEASE_NAME]
    namespace = artifact_conf[conf.NAMESPACE]

    with settings(warn_only=True):
        run("helm rollback {} -n {}".format(name, namespace))
        run("helm history {} -n {}".format(name, namespace))


def get_value(artifact_conf):
    """
    참조할 value의 경로를 반환한다.

    :param artifact_conf:
    :return: value의 경로
    """
    value_conf = artifact_conf.get(conf.VALUES)
    if "abis" in value_conf:
        # abis 를 이용할 경우
        value = value_conf
    else:
        # local 경로인 경우
        if "localhost" in env.host_string:
            value = value_conf
        else:
            local_value = value_conf
            value = "{}/{}".format(conf.TEST_DIR, local_value)

    return value


def get_chart(artifact_conf):
    """
    참조할 chart의 경로를 반환한다.

    :param artifact_conf:
    :return: chart의 경로
    """
    # config 파일에 저장된 chart 경로
    chart_conf = artifact_conf.get(conf.CHART)

    if "helm" in artifact_conf[conf.CHART]:
        # helm repo 를 이용할 경우
        chart_path = chart_conf
    else:
        if "localhost" in env.host_string:
            chart_path = chart_conf
        else:
            # local chart의 경로인 경우
            local_chart = chart_conf
            basename = os.path.basename(local_chart)
            chart_path = "{}/{}".format(conf.TEST_DIR, basename)

    return chart_path


def get_version(artifact_conf):
    version = artifact_conf.get(conf.CHART_VER)
    print(version)
    if version:
        return "--version='{}'".format(version)
    else:
        return ""


def deploy_testpod(env="it"):
    """
    abis에서 경로를 받아 최신 test pod로 배포한다.
    :return:
    """

    if env in "staging":
        pod = conf.STAGING_TEST_POD_YAML
    elif env in "production":
        pod = conf.PRODUCTION_TEST_POD_YAML
    else:
        pod = conf.IT_TEST_POD_YAML

    run("kubectl apply -f {}".format(pod))
    run("rm -f ~/.ssh/known_hosts")
    time.sleep(10)


def destroy_testpod():
    run("kubectl delete -f {}".format(conf.IT_TEST_POD_YAML))


def wait_testpod():
    time.sleep(2)
    ret = run("kubectl get pod -A | grep testpod")
    cnt = 0
    while ("0/" in ret) or ("Terminating" in ret):
        ret = run("kubectl get pod -A | grep testpod")

        cnt += 1
        if cnt == 100:
            break
        print("wait for starting testpod {} seconds... ".format(cnt * 10))
        time.sleep(10)

    if cnt == 100:
        raise Exception("testpod is not start")


def get_deploy_version(namespace):
    """
    version정보를 가져온다.
    :param namespace: version을 확인하고 싶은 namespace
    :return: version

    example
    run: kubectl get cm -n liveml version -o jsonpath='{.data.version}'
    out: 1.0.0.1

    """
    get_version_str = (
        "kubectl get cm -n "
        + namespace
        + " "
        + conf.VERSION
        + " -o "
        + "jsonpath='{.data.version}'"
    )
    version = run(get_version_str)
    return version.strip()


def set_deploy_version(namespace, version):
    """
    새로운 버전 configmap을 배포한다.
    :param env:  버전을 배포할 환경 e.g.) staging, production
    :return:

    example
    run: kubectl apply -f [ version.yaml path ]
    out: configmap/version created
    out:
    """
    version_yaml = ""
    if namespace.upper() in "LIVEML":
        version_yaml = conf.LIVEML_VERSION_YAML

    if config.url_exists(version_yaml) is False:
        print("version.yaml file does not exist")
        return

    run("kubectl apply -f {}".format(version_yaml))

    zookeeper.zookeeper_set_ci_version(namespace, version)
    time.sleep(10)


def compare_version(old_version, new_version):
    left_vars = map(int, old_version.split("."))
    right_vars = map(int, new_version.split("."))
    for a, b in izip_longest(left_vars, right_vars, fillvalue=0):
        if a > b:
            return False
        elif a < b:
            return True
    return False


def check_version(namespace, new_version):
    """
    현재 버전과 배포할 버전을 비교한다.
    :param namespace: 버전을 확인할 namespace
    :param new_version: 배포할 버전
    :return: 배포할 버전이 최신인 경우 True
              기존 버전과 같거나 낮은 경우 False
    """
    old_version = get_deploy_version(namespace)

    return compare_version(old_version, new_version)
