import random


class DAQ:
    """
    This class emulates a DAQ device virtually, returning random values for I/O
    operations.
    """

    # Class constants
    adc_resolution = 14
    adc_range = 10

    def __init__(self, name: str = "Dev1") -> None:
        self.name = name

    def read_analog(self, channel: str) -> float:
        """
        Emulate a random value for a 14bit ADC reading.

        Args:
            channel: The name of the channel to be read (It is here only to
            simulate the behavior of the original Python library).
        Returns:
            float:

            The 14bit value scaled to a range between -5.0 and +5.0 volts.

        """

        value = random.randint(0, 2**self.adc_resolution)
        value /= 2**self.adc_resolution
        value *= self.adc_range
        value -= self.adc_range / 2

        return value

    def read_digital(self, channel: str) -> int:
        """
        Emulate a random value for a digital reading.

        Args:
            channel: The name of the channel to be read (It is here only to
            simulate the behavior of the original Python library).
        Returns:
            int:

            An integer that can be 0 (low) or 1 (high)

        """
        return random.choice([0, 1])

    def __repr__(self) -> str:
        return f"DAQ {self.name}"

    def __str__(self) -> str:
        return self.__repr__()
