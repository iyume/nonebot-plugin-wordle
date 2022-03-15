import base64
from io import BytesIO

from PIL import Image


def im2base64(im: Image.Image) -> str:
    """Returns `base64://encoded_data`."""
    buffer = BytesIO()
    im.save(buffer, format="PNG")
    return f"base64://{base64.b64encode(buffer.getvalue()).decode()}"
