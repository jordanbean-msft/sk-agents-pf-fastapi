from enum import StrEnum, auto
from semantic_kernel.kernel_pydantic import KernelBaseModel

class ContentTypeEnum(StrEnum):
    MARKDOWN = auto()
    # DATAFRAME = auto()
    # EXCEPTION = auto()
    # MATPLOTLIB = auto()
    # IMAGE = auto()
    FILE = auto()

__all__ = ["ContentTypeEnum"]