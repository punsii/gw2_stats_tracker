import queue
import sys
import threading
from time import sleep

import pandas as pd
import requests
import streamlit as st
from requests.adapters import HTTPAdapter, Retry
from streamlit.runtime.scriptrunner import add_script_run_ctx

from process_logs import filter_log_data, transform_log

WORKER_COUNT = 4
# try to find a good balance...
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


@st.cache_data(max_entries=1000, show_spinner=False)
def _fetch_log_data(log_id: str, _session: requests.Session):
    try:
        data_response = _session.get(f"{BASE_URL}/getJson?id={log_id}")
        data_response.raise_for_status()
        return transform_log(filter_log_data(data_response.json()), log_id)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_log_list(userToken: str):
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


def fetch_logs(log_list):
    log_count = len(log_list)
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


if __name__ == "__main__":
    # log_list = [fetch_log_list(sys.argv[1])[0]]
    log_id = fetch_log_list(sys.argv[1])[0]
    data_response = requests.get(f"{BASE_URL}/getJson?id={log_id}")
    data_response.raise_for_status()
    d = data_response.json()
    import json

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)
