import json

from PIL import Image

from nmt_filters.lib.colorthief import ColorThief
from thumbor.engines.json_engine import JSONEngine
from thumbor.filters import BaseFilter

""" 
Ceci n'est pas une filter 

This file patches the `JSONEngine.read` method to include color information
when the meta endpoint is called.

Example: http://localhost:8888/unsafe/meta/https://images.nrc.nl/qNGHVRrH63Npu-vdTUplQxGm8P8=/320x192/smart/filters:no_upscale()/s3/static.nrc.nl/wp-content/uploads/2019/01/web-1501buiafdjpg.jpg

It is implemented as a filter as these can be configured in config `FILTERS` and are
conveniently imported at server startup in thumbor.server.main by `get_importer`

To enable add 'nmt_filters.meta_monkey' at the top of `FILTERS` in the thumbor config file
"""


class Filter(BaseFilter):
    pass


def monkey_read(self, extension, quality):
    target_width, target_height = self.get_target_dimensions()
    thumbor_json = {
        "thumbor": {
            "source": {
                "url": self.path,
                "width": self.width,
                "height": self.height,
                "frameCount": self.get_frame_count(),
            },
            "operations": self.operations,
            "target": {"width": target_width, "height": target_height},
        }
    }

    if self.focal_points:
        thumbor_json["thumbor"]["focal_points"] = self.focal_points

    # use a resampled image for performance
    thumbnail_image = self.image.resize((320, 240), Image.NEAREST)

    ct = ColorThief(thumbnail_image)
    thumbor_json["colors"] = dict(dominant=ct.get_color(), palette=ct.get_palette())
    thumbor_json = json.dumps(thumbor_json)

    if self.callback_name:
        return "%s(%s);" % (self.callback_name, thumbor_json)

    return thumbor_json


JSONEngine.read = monkey_read
