import dataclasses
import enum


@dataclasses.dataclass
class avatar_colors:
    head: int
    left_arm: int
    left_leg: int
    right_arm: int
    right_leg: int
    torso: int


@dataclasses.dataclass
class avatar_scales:
    height: float
    width: float
    head: float
    depth: float
    proportion: float
    body_type: float


class chat_style(enum.Enum):
    CLASSIC_CHAT = "Classic"
    BUBBLE_CHAT = "Bubble"
    CLASSIC_AND_BUBBLE_CHAT = "ClassicAndBubble"


class avatar_type(enum.Enum):
    R6 = "R6"
    R15 = "R15"