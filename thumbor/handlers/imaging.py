#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com thumbor@googlegroups.com

from six.moves.urllib.parse import quote, unquote

from thumbor.handlers import ContextHandler
from thumbor.context import RequestParameters
import tornado.gen as gen
import tornado.web


class ImagingHandler(ContextHandler):

    def compute_etag(self):
        if self.context.config.ENABLE_ETAGS:
            return super(ImagingHandler, self).compute_etag()
        else:
            return None

    @gen.coroutine  # NOQA
    def check_image(self, kw):
        if self.context.config.MAX_ID_LENGTH > 0:
            # Check if an image with an uuid exists in storage
            image_key = kw['image'][:self.context.config.MAX_ID_LENGTH]
            exists = yield gen.maybe_future(self.context.modules.storage.exists(image_key))
            if exists:
                kw['image'] = image_key

        url = self.request.path

        kw['image'] = quote(kw['image'].encode('utf-8'))
        if not self.validate(kw['image']):
            raise tornado.web.HTTPError(400, 'No original image was specified in the given URL')

        kw['request'] = self.request
        self.context.request = RequestParameters(**kw)

        has_none = not self.context.request.unsafe and not self.context.request.hash
        has_both = self.context.request.unsafe and self.context.request.hash

        if has_none or has_both:
            raise tornado.web.HTTPError(400, 'URL does not have hash or unsafe, or has both: %s' % url)

        if self.context.request.unsafe and not self.context.config.ALLOW_UNSAFE_URL:
            raise tornado.web.HTTPError(400, 'URL has unsafe but unsafe is not allowed by the config: %s' % url)

        if self.context.config.USE_BLACKLIST:
            blacklist = yield self.get_blacklist_contents()
            if self.context.request.image_url in blacklist:
                raise tornado.web.HTTPError(
                    400,
                    'Source image url has been blacklisted: %s' % self.context.request.image_url
                )

        url_signature = self.context.request.hash
        if url_signature:
            signer = self.context.modules.url_signer(self.context.server.security_key)

            try:
                quoted_hash = quote(self.context.request.hash)
            except KeyError:
                raise tornado.web.HTTPError(400, 'Invalid hash: %s' % self.context.request.hash)

            url_to_validate = url.replace('/%s/' % self.context.request.hash, '') \
                .replace('/%s/' % quoted_hash, '')

            valid = signer.validate(unquote(url_signature), url_to_validate)

            if not valid and self.context.config.STORES_CRYPTO_KEY_FOR_EACH_IMAGE:
                # Retrieves security key for this image if it has been seen before
                security_key = yield gen.maybe_future(self.context.modules.storage.get_crypto(self.context.request.image_url))
                if security_key is not None:
                    signer = self.context.modules.url_signer(security_key)
                    valid = signer.validate(url_signature, url_to_validate)

            if not valid:
                raise tornado.web.HTTPError(500, 'Malformed URL')

        yield self.execute_image_operations()

    @gen.coroutine
    def get(self, **kw):
        yield self.check_image(kw)

    @gen.coroutine
    def head(self, **kw):
        yield self.check_image(kw)
