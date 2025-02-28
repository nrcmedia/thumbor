#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from thumbor.loaders import http_loader
from tornado.concurrent import return_future


def _normalize_url(url):
    url = http_loader.quote_url(url)
    # NRC hotfix for not properly encoded urls with spaces in them
    url = url.replace(' ', '%20')
    # END hotfix
    # NRC hotfix for loading from Cloudflare proxy/mirror domains instead of S3
    url = url.replace('s3-eu-west-1.amazonaws.com/static.nrc.nl/', 'static.nrc.nl/')
    url = url.replace('s3-eu-west-1.amazonaws.com/nrchub/', 'r2hub.nrc.nl/')
    # END
    return url if url.startswith('http') else 'https://%s' % url


def validate(context, url):
    return http_loader.validate(context, url, normalize_url_func=_normalize_url)


def return_contents(response, url, callback, context):
    return http_loader.return_contents(response, url, callback, context)


@return_future
def load(context, url, callback):
    return http_loader.load_sync(context, url, callback, normalize_url_func=_normalize_url)


def encode(string):
    return http_loader.encode(string)
