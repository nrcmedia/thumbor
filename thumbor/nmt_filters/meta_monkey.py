import json

from PIL import Image

from thumbor.nmt_filters.lib.colorthief import ColorThief
from thumbor.engines.json_engine import JSONEngine
from thumbor.filters import BaseFilter

""" 
Ceci n'est pas une filter 

This file patches the `JSONEngine.read` method to include color information
when the meta endpoint is called.

Example: 
- http://localhost:8888/unsafe/meta/static.nrc.nl/wp-content/uploads/2019/01/web-1501buiafdjpg.jpg
- http://localhost:8888/unsafe/meta/static.nrc.nl/wp-content/uploads/2019/01/web-1501buiafdjpg.jpg?callback=handleMeta

It is implemented as a filter as these can be configured in config `FILTERS` and are
conveniently imported at server startup in thumbor.server.main by `get_importer`

To enable add 'thumbor.nmt_filters.meta_monkey' at the top of `FILTERS` in the thumbor config file
"""


class Filter(BaseFilter):
    pass


def get_matrix(matrix_image):
    image = matrix_image.convert("RGBA")
    width, height = image.size
    pixels = image.getdata()
    pixel_count = width * height
    matrix = []
    for i in range(0, pixel_count):
        r, g, b, a = pixels[i]
        matrix.append([r, g, b])
    return matrix


def monkey_read(self, extension, quality):
    target_width, target_height = self.get_target_dimensions()
    thumbor_json = {
        "thumbor": {
            "source": {
                "url": self.path,
                "frameCount": self.get_frame_count(),
                "width": self.source_width,
                "height": self.source_height,
            },
            "operations": self.operations,
            "target": {"width": target_width, "height": target_height},
        }
    }

    if self.focal_points:
        thumbor_json["thumbor"]["focal_points"] = self.focal_points

    # use a resampled image for performance
    palette_ct = ColorThief(self.image.resize((320, 240), Image.NEAREST))
    matrix_image = self.image.resize((2, 2), Image.NEAREST)

    thumbor_json["colors"] = dict(
        # the dominant color:
        dominant=palette_ct.get_color(),
        # a palette of the most dominant colors:
        palette=palette_ct.get_palette(),
        # a 4x4 matrix of the dominant color in each quadrant of the image:
        matrix=(get_matrix(matrix_image)),
    )
    thumbor_json = json.dumps(thumbor_json)

    if self.callback_name:
        return "%s(%s);" % (self.callback_name, thumbor_json)

    return thumbor_json


JSONEngine.read = monkey_read
