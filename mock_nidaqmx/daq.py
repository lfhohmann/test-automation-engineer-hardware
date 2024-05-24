import random
from typing import Self

from .utils import unflatten_channel_string


class Channel:
    """
    Base class for all channels.
    """

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
    """
    Digital Input Channel, that generates a random value when queried.
    """

    def __init__(self, name) -> None:
        super().__init__(name)

    @property
    def value(self) -> int:
        """
        Emulate a random value for a digital reading.

        Returns:
            int:

            An integer that can be 0 (LOW) or 1 (HIGH)
        """

        return random.choice([0, 1])


class AIChannel(Channel):
    """
    Analog Input Channel, that generates a random value when queried.
    """

    def __init__(self, name) -> None:
        super().__init__(name)

    @property
    def value(self) -> float:
        """
        Emulate a random value for a 14bit ADC reading.

        Returns:
            float:

            The 14bit value scaled to a range between -5.0 and +5.0 volts.
        """

        return ((random.randint(0, 2**14) / 2**14) * 10) - 5


class AIChannelCollection:
    """
    Handles a collection of all Analog Input Channels.
    """

    def __init__(self, task) -> None:
        self.task = task

    def add_ai_voltage_chan(self, channels) -> None:
        """Add one or more Analog Input Channels to the collection."""

        # Extract all the channels from the input string.
        channels = unflatten_channel_string(channels)

        # Add each channel to the collection.
        for channel in channels:
            self.task.channels.append(AIChannel(channel))


class DIChannelCollection:
    """
    Handles a collection of all Digital Input Channels.
    """

    def __init__(self, task) -> None:
        self.task = task

    def add_di_chan(self, channels) -> None:
        """Add one or more Digital Input Channels to the collection."""

        # Extract all the channels from the input string.
        channels = unflatten_channel_string(channels)

        # Add each channel to the collection.
        for channel in channels:
            self.task.channels.append(DIChannel(channel))


class DAQ:
    """
    Creates instances for the physical DAQ devices and their associated tasks.
    """

    class Task:
        def __init__(self) -> None:
            self.channels: list[Channel] = []
            self.ai_channels = AIChannelCollection(self)
            self.di_channels = DIChannelCollection(self)

        def __enter__(self) -> Self:
            """Context Manager to mimic the original 'nidaqmx' module."""

            return self

        def __exit__(self, *args, **kwargs) -> None:
            """Clear all channels when closing the Task."""

            self.channels = []

        def read(self, number_of_samples_per_channel=1) -> list[list[float | bool]]:
            """Read the specified number of samples for each channel."""

            return [[channel.value for _ in range(number_of_samples_per_channel)] for channel in self.channels]

    def __init__(self, name: str = "Dev1") -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"DAQ {self.name}"

    def __str__(self) -> str:
        return self.__repr__()
