#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

import os
import time
import threading
import newrelic.agent
from thumbor.metrics import BaseMetrics

import traceback


class Metrics(BaseMetrics):

    @classmethod
    def values(cls, config):
        if not hasattr(cls, "_values"):
            cls._values = dict()
            newrelic.agent.initialize(config.NEW_RELIC_CONFIG_FILE)
            cls._app = newrelic.agent.register_application()
            thread = threading.Thread(target=cls.report_values)
            thread.setDaemon(True)
            thread.start()
        return cls._values

    @staticmethod
    def name(metricname):
        return 'Custom/Thumbor/' + metricname.replace('.', '/').title()

    @classmethod
    def report_values(cls):
        count = 0

        while True:
            count += 1
            if count % 60 == 0:
                for metricname, value in cls._values.iteritems():
                    newrelic.agent.record_custom_metric(cls.name(metricname), value, cls._app)
                cls._values = dict()

            time.sleep(1.0)

    def incr(self, metricname, value=1):
        values = Metrics.values(self.config)

        if metricname in values:
            values[metricname] += value
        else:
            values[metricname] = value

    def timing(self, metricname, value):
        values = Metrics.values(self.config)

        if metricname in values:
            metric = values[metricname]
        else:
            metric = {
                'count': 0.0,
                'total': 0.0,
                'min': 0.0,
                'max': 0.0,
                'sum_of_squares': 0.0,
            }
            values[metricname] = metric

        metric['total'] += value
        metric['min'] = metric['count'] and min(metric['min'], value) or value
        metric['max'] = max(metric['max'], value)
        metric['sum_of_squares'] += value ** 2
        metric['count'] += 1
