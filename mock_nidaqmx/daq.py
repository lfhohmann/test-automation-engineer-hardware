import random
from typing import Self

from .utils import unflatten_channel_string


class Channel:
    def __init__(self, name) -> None:
        self.name = name

    @property
    def value(self) -> None:
        raise NotImplementedError()

    def __repr__(self) -> str:
        return f"Channel({self.name})"

    def __str__(self) -> str:
        return self.__repr__()


class DIChannel(Channel):
    def __init__(self, name) -> None:
        super().__init__(name)

    @property
    def value(self) -> int:
        return random.choice([0, 1])


class AIChannel(Channel):
    def __init__(self, name) -> None:
        super().__init__(name)

    @property
    def value(self) -> float:
        return ((random.randint(0, 2**14) / 2**14) * 10) - 5


class AIChannelCollection:
    def __init__(self, task) -> None:
        self.task = task

    def add_ai_voltage_chan(self, channels) -> None:
        channels = unflatten_channel_string(channels)

        for channel in channels:
            self.task.channels.append(AIChannel(channel))


class DIChannelCollection:
    def __init__(self, task) -> None:
        self.task = task

    def add_di_chan(self, channels) -> None:
        channels = unflatten_channel_string(channels)

        for channel in channels:
            self.task.channels.append(DIChannel(channel))


class DAQ:
    class Task:
        def __init__(self) -> None:
            self.channels: list[Channel] = []
            self.ai_channels = AIChannelCollection(self)
            self.di_channels = DIChannelCollection(self)

        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args, **kwargs) -> None:
            self.channels = []

        def read(self, number_of_samples_per_channel=1) -> list[list[float | bool]]:
            return [[channel.value for _ in range(number_of_samples_per_channel)] for channel in self.channels]

    def __init__(self, name: str = "Dev1") -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"DAQ {self.name}"

    def __str__(self) -> str:
        return self.__repr__()
