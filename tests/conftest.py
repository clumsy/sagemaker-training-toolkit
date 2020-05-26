# Copyright 2017-2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import json
import os

import boto3
import pytest
import tests.integ
from botocore.config import Config

from sagemaker import Session, utils
from sagemaker.chainer import Chainer
from sagemaker.local import LocalSession
from sagemaker.mxnet import MXNet
from sagemaker.pytorch import PyTorch
from sagemaker.rl import RLEstimator
from sagemaker.sklearn.defaults import SKLEARN_VERSION
from sagemaker.tensorflow import TensorFlow
from sagemaker.tensorflow.defaults import LATEST_VERSION, LATEST_SERVING_VERSION

DEFAULT_REGION = "us-west-2"
CUSTOM_BUCKET_NAME_PREFIX = "sagemaker-custom-bucket"

NO_M4_REGIONS = [
    "eu-west-3",
    "eu-north-1",
    "ap-east-1",
    "ap-northeast-1",  # it has m4.xl, but not enough in all AZs
    "sa-east-1",
    "me-south-1",
]

NO_T2_REGIONS = ["eu-north-1", "ap-east-1", "me-south-1"]


def pytest_addoption(parser):
    parser.addoption("--sagemaker-client-config", action="store", default=None)
    parser.addoption("--sagemaker-runtime-config", action="store", default=None)
    parser.addoption("--boto-config", action="store", default=None)
    parser.addoption("--chainer-full-version", action="store", default=Chainer.LATEST_VERSION)
    parser.addoption("--mxnet-full-version", action="store", default=MXNet.LATEST_VERSION)
    parser.addoption("--ei-mxnet-full-version", action="store", default="1.5.1")
    parser.addoption("--pytorch-full-version", action="store", default=PyTorch.LATEST_VERSION)
    parser.addoption(
        "--rl-coach-mxnet-full-version",
        action="store",
        default=RLEstimator.COACH_LATEST_VERSION_MXNET,
    )
    parser.addoption(
        "--rl-coach-tf-full-version", action="store", default=RLEstimator.COACH_LATEST_VERSION_TF
    )
    parser.addoption(
        "--rl-ray-full-version", action="store", default=RLEstimator.RAY_LATEST_VERSION
    )
    parser.addoption("--sklearn-full-version", action="store", default=SKLEARN_VERSION)
    parser.addoption("--tf-full-version", action="store")
    parser.addoption("--ei-tf-full-version", action="store")
    parser.addoption("--xgboost-full-version", action="store", default=SKLEARN_VERSION)


def pytest_configure(config):
    bc = config.getoption("--boto-config")
    parsed = json.loads(bc) if bc else {}
    region = parsed.get("region_name", boto3.session.Session().region_name)
    if region:
        os.environ["TEST_AWS_REGION_NAME"] = region


@pytest.fixture(scope="session")
def sagemaker_client_config(request):
    config = request.config.getoption("--sagemaker-client-config")
    return json.loads(config) if config else dict()


@pytest.fixture(scope="session")
def sagemaker_runtime_config(request):
    config = request.config.getoption("--sagemaker-runtime-config")
    return json.loads(config) if config else None


@pytest.fixture(scope="session")
def boto_session(request):
    config = request.config.getoption("--boto-config")
    if config:
        return boto3.Session(**json.loads(config))
    else:
        return boto3.Session(region_name=DEFAULT_REGION)


@pytest.fixture(scope="session")
def sagemaker_session(sagemaker_client_config, sagemaker_runtime_config, boto_session):
    sagemaker_client_config.setdefault("config", Config(retries=dict(max_attempts=10)))
    sagemaker_client = (
        boto_session.client("sagemaker", **sagemaker_client_config)
        if sagemaker_client_config
        else None
    )
    runtime_client = (
        boto_session.client("sagemaker-runtime", **sagemaker_runtime_config)
        if sagemaker_runtime_config
        else None
    )

    return Session(
        boto_session=boto_session,
        sagemaker_client=sagemaker_client,
        sagemaker_runtime_client=runtime_client,
    )


@pytest.fixture(scope="session")
def sagemaker_local_session(boto_session):
    return LocalSession(boto_session=boto_session)


@pytest.fixture(scope="module")
def custom_bucket_name(boto_session):
    region = boto_session.region_name
    account = boto_session.client(
        "sts", region_name=region, endpoint_url=utils.sts_regional_endpoint(region)
    ).get_caller_identity()["Account"]
    return "{}-{}-{}".format(CUSTOM_BUCKET_NAME_PREFIX, region, account)


@pytest.fixture(scope="module", params=["4.0", "4.0.0", "4.1", "4.1.0", "5.0", "5.0.0"])
def chainer_version(request):
    return request.param


# TODO: current version fixtures are legacy fixtures that aren't useful
# and no longer verify whether images are valid
@pytest.fixture(
    scope="module",
    params=[
        "0.12",
        "0.12.1",
        "1.0",
        "1.0.0",
        "1.1",
        "1.1.0",
        "1.2",
        "1.2.1",
        "1.3",
        "1.3.0",
        "1.4",
        "1.4.0",
        "1.4.1",
    ],
)
def mxnet_version(request):
    return request.param


@pytest.fixture(scope="module", params=["0.4", "0.4.0", "1.0", "1.0.0"])
def pytorch_version(request):
    return request.param


@pytest.fixture(scope="module", params=["0.20.0"])
def sklearn_version(request):
    return request.param


@pytest.fixture(scope="module", params=["0.90-1"])
def xgboost_version(request):
    return request.param


@pytest.fixture(
    scope="module",
    params=[
        "1.4",
        "1.4.1",
        "1.5",
        "1.5.0",
        "1.6",
        "1.6.0",
        "1.7",
        "1.7.0",
        "1.8",
        "1.8.0",
        "1.9",
        "1.9.0",
        "1.10",
        "1.10.0",
        "1.11",
        "1.11.0",
        "1.12",
        "1.12.0",
    ],
)
def tf_version(request):
    return request.param


@pytest.fixture(scope="module", params=["0.10.1", "0.10.1", "0.11", "0.11.0", "0.11.1"])
def rl_coach_tf_version(request):
    return request.param


@pytest.fixture(scope="module", params=["0.11", "0.11.0"])
def rl_coach_mxnet_version(request):
    return request.param


@pytest.fixture(scope="module", params=["0.5", "0.5.3", "0.6", "0.6.5"])
def rl_ray_version(request):
    return request.param


@pytest.fixture(scope="module")
def chainer_full_version(request):
    return request.config.getoption("--chainer-full-version")


@pytest.fixture(scope="module")
def mxnet_full_version(request):
    return request.config.getoption("--mxnet-full-version")


@pytest.fixture(scope="module")
def ei_mxnet_full_version(request):
    return request.config.getoption("--ei-mxnet-full-version")


@pytest.fixture(scope="module")
def pytorch_full_version(request):
    return request.config.getoption("--pytorch-full-version")


@pytest.fixture(scope="module")
def rl_coach_mxnet_full_version(request):
    return request.config.getoption("--rl-coach-mxnet-full-version")


@pytest.fixture(scope="module")
def rl_coach_tf_full_version(request):
    return request.config.getoption("--rl-coach-tf-full-version")


@pytest.fixture(scope="module")
def rl_ray_full_version(request):
    return request.config.getoption("--rl-ray-full-version")


@pytest.fixture(scope="module")
def sklearn_full_version(request):
    return request.config.getoption("--sklearn-full-version")


@pytest.fixture(scope="module", params=[TensorFlow._LATEST_1X_VERSION, LATEST_VERSION])
def tf_full_version(request):
    tf_version = request.config.getoption("--tf-full-version")
    if tf_version is None:
        return request.param
    else:
        return tf_version


@pytest.fixture(scope="module", params=["1.15.0", "2.0.0"])
def ei_tf_full_version(request):
    tf_ei_version = request.config.getoption("--ei-tf-full-version")
    if tf_ei_version is None:
        return request.param
    else:
        tf_ei_version


@pytest.fixture(scope="session")
def cpu_instance_type(sagemaker_session, request):
    region = sagemaker_session.boto_session.region_name
    if region in NO_M4_REGIONS:
        return "ml.m5.xlarge"
    else:
        return "ml.m4.xlarge"


@pytest.fixture(scope="session")
def inf_instance_type(sagemaker_session, request):
    return "ml.inf1.xlarge"


@pytest.fixture(scope="session")
def ec2_instance_type(cpu_instance_type):
    return cpu_instance_type[3:]


@pytest.fixture(scope="session")
def alternative_cpu_instance_type(sagemaker_session, request):
    region = sagemaker_session.boto_session.region_name
    if region in NO_T2_REGIONS:
        # T3 is not supported by hosting yet
        return "ml.c5.xlarge"
    else:
        return "ml.t2.medium"


@pytest.fixture(scope="session")
def cpu_instance_family(cpu_instance_type):
    return "_".join(cpu_instance_type.split(".")[0:2])


@pytest.fixture(scope="session")
def inf_instance_family(inf_instance_type):
    return "_".join(inf_instance_type.split(".")[0:2])


def pytest_generate_tests(metafunc):
    if "instance_type" in metafunc.fixturenames:
        boto_config = metafunc.config.getoption("--boto-config")
        parsed_config = json.loads(boto_config) if boto_config else {}
        region = parsed_config.get("region_name", DEFAULT_REGION)
        cpu_instance_type = "ml.m5.xlarge" if region in NO_M4_REGIONS else "ml.m4.xlarge"

        params = [cpu_instance_type]
        if not (
            region in tests.integ.HOSTING_NO_P2_REGIONS
            or region in tests.integ.TRAINING_NO_P2_REGIONS
        ):
            params.append("ml.p2.xlarge")
        metafunc.parametrize("instance_type", params, scope="session")


@pytest.fixture(scope="module")
def xgboost_full_version(request):
    return request.config.getoption("--xgboost-full-version")


@pytest.fixture(scope="module")
def tf_serving_version(tf_full_version):
    if tf_full_version == LATEST_VERSION:
        return LATEST_SERVING_VERSION
    return tf_full_version