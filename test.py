import math
import time
import unittest
from unittest.mock import patch

from mock_nidaqmx import DAQ

TEST_DURATION = 11  # In seconds
MAX_JITTER = 10  # In ms
PERIOD = 2_000  # In ms


class TestSignalJitter(unittest.TestCase):
    """
    Test that the signal jitter is within acceptable range.
    """

    @staticmethod
    def side_effect_read_digital(*args: list, **kwargs: dict) -> int:
        """
        Patch the 'read_digital()' function of the DAQ class to generate a
        square wave of 0.5Hz and 50% duty cycle.

        Returns:
            int:

            A 1 or 0 value for HIGH and LOW respectively.
        """

        return math.floor(time.perf_counter() % 2)

    @patch.object(DAQ, "read_digital", side_effect=side_effect_read_digital)
    def test_read(self, *args: list, **kwargs: dict) -> None:

        # Init the device
        device = DAQ()

        # Init the variables to track the sampling process
        start = time.perf_counter()
        prev_state = None
        prev_time = start
        delays = []

        while True:
            # Store the current time to be constant for each iteration
            now = time.perf_counter()

            # Perform read
            state = device.read_digital("Dev1/0")

            # Init the previous state if it's None
            if prev_state is None:
                prev_state = state

            # Store delay time in list if state changed
            if state != prev_state:
                delays.append(now - prev_time)
                prev_state = state
                prev_time = now

            # Break the loop if the test duration is reached
            if (now - start) > TEST_DURATION:
                break

        # Iterate over each delay and check if it's less then 'MAX_JITTER'.
        # The first delay is discarded as it did not start synchonized with
        # the square wave.
        for delay in delays[1:]:

            # Calculate the jitter
            jitter = (delay * 1000) - (PERIOD / 2)

            # Assert that the jitter is less then 'MAX_JITTER'
            self.assertLessEqual(abs(jitter), MAX_JITTER)


if __name__ == "__main__":
    unittest.main()
