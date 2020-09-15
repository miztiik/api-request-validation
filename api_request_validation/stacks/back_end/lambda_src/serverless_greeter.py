# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
import random
import time
import fcntl


class GlobalArgs:
    """ Global statics """
    OWNER = "Mystique"
    ENVIRONMENT = "production"
    MODULE_NAME = "greeter_lambda"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    RANDOM_SLEEP_ENABLED = os.getenv("RANDOM_SLEEP_ENABLED", False)
    RANDOM_SLEEP_SECS = int(os.getenv("RANDOM_SLEEP_SECS", 2))
    ANDON_CORD_PULLED = os.getenv("ANDON_CORD_PULLED", False)


def set_logging(lv=GlobalArgs.LOG_LEVEL):
    """ Helper to enable logging """
    logging.basicConfig(level=lv)
    logger = logging.getLogger()
    logger.setLevel(lv)
    return logger


# Initial some defaults in global context to reduce lambda start time, when re-using container
logger = set_logging()


def random_sleep(max_seconds=10):
    if bool(random.getrandbits(1)):
        logger.info(f"sleep_start_time:{str(datetime.datetime.now())}")
        time.sleep(random.randint(0, max_seconds))
        logger.info(f"sleep_end_time:{str(datetime.datetime.now())}")


def lambda_handler(event, context):
    logger.info(f"rcvd_evnt:\n{event}")
    greet_msg = "Unknown `category` provided"
    # random_sleep(GlobalArgs.RANDOM_SLEEP_SECS)

    _d = {"pens": [{"sku": 1, "type": "gel", "status": "available", "price": 83}], "pencil": [{"sku": 2, "type": "microtip",
                                                                                               "status": "unavailable", "price": 19}], "eraser": [{"sku": 3, "type": "rubber", "status": "available", "price": 13}]}
    try:
        _c = event.get("category")
        if _c:
            greet_msg = _d[str(_c)]
    except Exception as e:
        logger.error(f"ERROR:{str(e)}")

    msg = {
        "statusCode": 200,
        "body": (
            f'{{"message": "{greet_msg}",'
            f'"lambda_version":"{context.function_version}",'
            f'"ts": "{str(datetime.datetime.now())}"'
            f'}}'
        )
    }

    return msg
