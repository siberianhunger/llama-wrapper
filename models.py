from enum import Enum


class Roles(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"
