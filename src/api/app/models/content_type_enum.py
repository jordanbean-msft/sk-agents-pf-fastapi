from enum import StrEnum, auto


class ContentTypeEnum(StrEnum):
    MARKDOWN = auto()
    FILE = auto()


__all__ = ["ContentTypeEnum"]
