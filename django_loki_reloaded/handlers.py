import logging
import sys
from threading import Thread

import requests


class LokiHandler(logging.Handler):
    def __init__(
        self,
        timeout=0.5,
        url="http://localhost:3100/loki/api/v1/push",
        source="Loki",
        src_host="localhost",
        auth=None,
        tags={},
        tz="UTC",
        mode="sync",
    ):
        super(LokiHandler, self).__init__()

        self._url = url
        self._tz = tz
        self._timeout = timeout
        self._source = source
        self._src_host = src_host
        self._auth = auth
        self._tags = tags
        self._mode = mode

    def emit(self, record):
        try:
            payload = self.formatter.format(record)

            _push_message(
                self._url, json=payload, timeout=self._timeout, auth=self._auth
            )
        except requests.exceptions.ReadTimeout:
            sys.stderr.write("Loki connection timed out\n")

    def setFormatter(self, fmt):
        fmt.tz = self._tz
        fmt.source = self._source
        fmt.src_host = self._src_host
        fmt.tags = self._tags

        self.formatter = fmt

    def _push_message(self, *args, **kwargs):
        if self._mode == "sync":
            return _push_message(*args, **kwargs)

        if self._mode == "thread":
            return Thread(target=_push_message, args=args, kwargs=kwargs).start()


def _push_message(*args, **kwargs):
    response = requests.post(*args, **kwargs)

    if response.status_code != 204:
        sys.stderr.write(
            f"Got status {response.status_code} from loki with message: {response.text}\n"
        )
