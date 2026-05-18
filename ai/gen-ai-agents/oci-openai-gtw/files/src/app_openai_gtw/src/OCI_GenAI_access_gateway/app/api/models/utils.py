import logging
import json
from pydantic import BaseModel

logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)


def element_to_dict(element):
    if isinstance(element, dict):
        return element
    elif isinstance(element, BaseModel):
        return element.model_dump()
    else:
        return json.loads(str(element))