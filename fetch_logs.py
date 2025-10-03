import logging
import queue
import sys
import threading
from time import sleep

import pandas as pd
import requests
import streamlit as st
from requests.adapters import HTTPAdapter, Retry
from streamlit.runtime.scriptrunner import add_script_run_ctx

from process_logs import (BOON_KEYS, RENAMED_KEYS, FightInvalidException,
                          filter_log_data, transform_log)

WORKER_COUNT = 4
# XXX try to find a good balance...
# from os import sched_getaffinity
# WORKER_COUNT = len(sched_getaffinity(0))
# import os
# os.write(1, f"{WORKER_COUNT=}\n".encode())
# Measured on wifi with 8 cores/16 threads
# 2 -> 67
# 4 -> 62
# 8 -> 59
# 16 -> 57
# 32 -> 62

BASE_URL = "https://dps.report"

# These keys are needed but should not be selectable
_HIDDEN_KEYS = [
    "id",
    "timeStart",
    "profession",
    "name",
    "profession+name",
    "spec_color",
    "account",
]

_KEY_CATEGORIES = {
    "Default": [
        RENAMED_KEYS["dps"],
        RENAMED_KEYS["downContribution"],
        RENAMED_KEYS["healing"],
        RENAMED_KEYS["barrier"],
        RENAMED_KEYS["boonStrips"],
        RENAMED_KEYS["boonStripDownContribution"],
        RENAMED_KEYS["appliedCrowdControl"],
        RENAMED_KEYS["appliedCrowdControlDownContribution"],
        RENAMED_KEYS["condiCleanse"],
        RENAMED_KEYS["avgActiveBoons"],
        RENAMED_KEYS["avgActiveConditions"],
        RENAMED_KEYS["distToCom"],
        RENAMED_KEYS["swapCount"],
        RENAMED_KEYS["skillCastUptime"],
        RENAMED_KEYS["percentageAlive"],
    ],
    "Offense": [
        RENAMED_KEYS["dps"],
        RENAMED_KEYS["downContribution"],
        RENAMED_KEYS["condiDps"],
        RENAMED_KEYS["powerDps"],
        RENAMED_KEYS["criticalDmg"],
        RENAMED_KEYS["boonStrips"],
        RENAMED_KEYS["boonStripDownContribution"],
        RENAMED_KEYS["killed"],
        RENAMED_KEYS["downed"],
        RENAMED_KEYS["interrupts"],
        RENAMED_KEYS["appliedCrowdControl"],
        RENAMED_KEYS["appliedCrowdControlDownContribution"],
        RENAMED_KEYS["appliedCrowdControlDuration"],
        RENAMED_KEYS["appliedCrowdControlDurationDownContribution"],
        RENAMED_KEYS["missed"],
        RENAMED_KEYS["criticalRate"],
        RENAMED_KEYS["glanceRate"],
        RENAMED_KEYS["flankingRate"],
    ],
    "Defense": [
        RENAMED_KEYS["healing"],
        RENAMED_KEYS["barrier"],
        RENAMED_KEYS["downedHealing"],
        RENAMED_KEYS["resurrects"],
        RENAMED_KEYS["resurrectTime"],
        RENAMED_KEYS["condiCleanse"],
        RENAMED_KEYS["condiCleanseSelf"],
        RENAMED_KEYS["stunBreak"],
        RENAMED_KEYS["removedStunDuration"],
        RENAMED_KEYS["evaded"],
        RENAMED_KEYS["blocked"],
        RENAMED_KEYS["invulned"],
    ],
    # These are keys that someone might be intetested in
    # but which just clutter the application most of the time.
    "Miscellaneous": [
        RENAMED_KEYS["distToCom"],
        RENAMED_KEYS["skillCastUptime"],
        RENAMED_KEYS["skillCastUptimeNoAA"],  # --> 'skillCastUptime' should be enough
        RENAMED_KEYS["swapCount"],
        RENAMED_KEYS["totalDamageCount"],  # --> 'dps' should be enough
        RENAMED_KEYS["removedStunDuration"],
        # RENAMED_KEYS["boonStripDownContributionTime"],
        RENAMED_KEYS["appliedCrowdControlDuration"],
        RENAMED_KEYS["appliedCrowdControlDurationDownContribution"],
    ],
    "Unlabeled": [],
}


@st.cache_data(max_entries=500, show_spinner=False)
def _fetch_log_data(log_id: str, _session: requests.Session):
    try:
        data_response = _session.get(f"{BASE_URL}/getJson?id={log_id}")
        data_response.raise_for_status()
    except Exception:
        logging.exception(f"Could not download log {log_id}.")
        return pd.DataFrame()
    try:
        return transform_log(filter_log_data(data_response.json()), log_id)
    except FightInvalidException as e:
        logging.warning(e)
        return pd.DataFrame()


@st.cache_data(ttl=300)
def _fetch_log_list(userToken: str):
    response = requests.get(f"{BASE_URL}/getUploads?userToken={userToken}")
    response.raise_for_status()
    json = response.json()
    max_pages = json["pages"]
    uploads = json["uploads"]
    for page in range(1, 5):
        if page > max_pages:
            break
        response = requests.get(
            f"{BASE_URL}/getUploads?userToken={userToken}&page={page+1}"
        )
        response.raise_for_status()
        uploads.extend(response.json()["uploads"])
    return [upload["id"] for upload in uploads]


def _fetch_log_worker(task_queue):
    with requests.Session() as session:
        session.mount(
            BASE_URL, HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1))
        )

        while True:
            try:
                [log_buffer, index, log_id] = task_queue.get(timeout=3)
            except queue.Empty:
                return
            log_buffer[index] = _fetch_log_data(log_id, session)
            task_queue.task_done()


def _fetch_logs(log_list):
    log_count = len(log_list)
    st.write("")
    st.write("")
    progress_bar = st.progress(0)

    log_buffer = [pd.DataFrame()] * log_count
    thread_list = []

    # Create threads
    task_queue = queue.Queue()
    for _ in range(WORKER_COUNT):
        thread = threading.Thread(
            target=_fetch_log_worker, daemon=True, args=[task_queue]
        )
        thread = add_script_run_ctx(thread)
        thread_list.append(thread)
        thread.start()

    # Distribute to workers
    for index, log_id in enumerate(log_list):
        task_queue.put([log_buffer, index, log_id])
    while not task_queue.empty():
        progress_bar.progress((log_count - task_queue.qsize()) / log_count)
        sleep(1)
    progress_bar.progress(100)
    progress_bar.empty()

    # Wait for results
    with st.spinner(text="One more second..."):
        task_queue.join()

    # Merge buffer to a single Dataframe
    df = pd.DataFrame()
    for index, log in enumerate(log_buffer):
        if not log.empty:
            df = pd.concat([df, log])

    df = df.sort_values("timeStart").reset_index(drop=True)
    return df


@st.cache_data(max_entries=6, ttl=310)
def fetch_data(userToken: str, stat_category: str):
    log_list = _fetch_log_list(userToken)
    # log_list = log_list[:10]  # XXX for testing
    df = _fetch_logs(log_list)

    # create inputs
    unlabeled_keys = [
        key
        for key in list(df)
        if key not in _HIDDEN_KEYS
        and key not in _KEY_CATEGORIES["Default"]
        and key not in _KEY_CATEGORIES["Offense"]
        and key not in _KEY_CATEGORIES["Defense"]
        and key not in BOON_KEYS
        and key not in _KEY_CATEGORIES["Miscellaneous"]
    ]

    result_keys = _HIDDEN_KEYS.copy()
    match stat_category:
        case "Default":
            result_keys += _KEY_CATEGORIES["Default"]
        case "Offense":
            result_keys += _KEY_CATEGORIES["Offense"]
        case "Defense":
            result_keys += _KEY_CATEGORIES["Defense"]
        case "Boons":
            result_keys += BOON_KEYS
        case "Miscellaneous":
            result_keys += _KEY_CATEGORIES["Miscellaneous"]
        case "Unlabeled":
            result_keys += unlabeled_keys

    return df[result_keys]


if __name__ == "__main__":
    import json

    user_token = sys.argv[1]

    # log_list = _fetch_log_list(user_token)[11:14]
    # for log_id in log_list:
    #     log = requests.get(f"{BASE_URL}/getJson?id={log_id}").json()
    #     print(transform_log(filter_log_data(log), log_id))

    log_ids = _fetch_log_list(user_token)
    for log_id in log_ids[0:]:
        data_response = requests.get(f"{BASE_URL}/getJson?id={log_id}")
        data_response.raise_for_status()
        d = data_response.json()

        try:
            transform_log(filter_log_data(d), log_id)

        except FightInvalidException as e:
            print(f"{e=} - {type(e)=}")
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=4)
            sys.exit()
        except Exception as e:
            print(e)
            print(type(e))
            with open("data.json", "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=4)
            sys.exit()
