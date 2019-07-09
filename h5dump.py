# perf script event handlers, generated by perf script -g python
# Licensed under the terms of the GNU GPL License version 2

# The common_* event handler fields are the most useful fields common to
# all events.  They don't necessarily correspond to the 'common_*' fields
# in the format files.  Those fields not available as handler params can
# be retrieved using Python functions of the form common_*(context).
# See the perf-trace-python Documentation for the list of available functions.

import os
import sys

import pandas as pd
import pandas.io.pytables as pt
import numpy as np

from perf_trace_context import * # noqa
from Core import *  # noqa
import logging

sys.path.append(os.environ['PERF_EXEC_PATH'] +
                '/scripts/python/Perf-Trace-Util/lib/Perf/Trace')

events = {}
filename = None

logger = logging.getLogger('h5dump')
logging.basicConfig(level=logging.INFO)


def getDtype(value):
    if isinstance(value, int):
        return np.dtype('<i8')
    elif isinstance(value, str):
        return np.dtype('|S16')
    return None


class Vector:

    def __init__(self, dtype):
        self._size = 0
        self._storage_size = 1
        self._storage = np.zeros(self._storage_size,
                                 dtype=dtype)

    def size(self):
        return self._size

    def data(self):
        return self._storage[:self._storage_size]

    def resize(self, new_storage_size=None):
        if new_storage_size is None:
            new_storage_size = 2*self._storage_size
        new_storage = np.zeros(new_storage_size,
                               dtype=self._storage.dtype)

        # copy existing data
        if new_storage_size > self._storage_size:
            new_storage[:self._storage_size] = self._storage
        else:
            new_storage = self._storage[:new_storage_size]

        self._storage_size = new_storage_size
        self._storage = new_storage

    def push_back(self, item):
        if self._size >= self._storage_size:
            self.resize()
        self._storage[self._size] = item
        self._size += 1


def trace_begin():
    global filename
    if len(sys.argv) < 2:
        logger.error("missing filename")
        sys.exit(1)
    filename = sys.argv[1]


def trace_end():

    logger.info('opening output file {}'.format(filename))
    store = pt.HDFStore(filename)

    for event_name, vd in events.items():

        logger.info("writing data for event '{}'".format(event_name))

        ad = {field: v.data() for field, v in vd.items()}

        secs = ad['common_s']
        nsecs = ad['common_ns']
        timestamp = secs.astype(np.float) + nsecs.astype(np.float) * 1E-9

        df = pd.DataFrame(ad,
                          index=timestamp)

        store[event_name] = df

    store.close()
    logger.info('done')


def event_to_vector_dict(event):
    vector_dict = {}
    for field, value in event.items():
        dtype = getDtype(value)
        if dtype is None:
            logger.warning("ignoring field '{}' with type {}"
                           .format(field, type(value)))
            continue
        logger.info("detected column '{}' with dtype {}".format(field, dtype))
        vector = Vector(dtype)
        vector.push_back(value)
        vector_dict[field] = vector
    return vector_dict


def trace_unhandled(event_name, context, event_fields_dict, perf_sample_dict):
    global events
    if event_name not in events:
        vector_dict = event_to_vector_dict(event_fields_dict)
        events[event_name] = vector_dict

    vector_dict = events[event_name]
    for field, vector in vector_dict.items():
        value = event_fields_dict[field]
        vector.push_back(value)


def print_header(event_name, cpu, secs, nsecs, pid, comm):
    print("%-20s %5u %05u.%09u %8u %-20s " %
          (event_name, cpu, secs, nsecs, pid, comm), end="")


def get_dict_as_string(a_dict, delimiter=' '):
    return delimiter.join(['%s=%s' % (k, str(v))
                          for k, v in sorted(a_dict.items())])
