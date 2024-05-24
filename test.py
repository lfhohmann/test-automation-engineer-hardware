import math
import time
import unittest
from unittest.mock import patch

import numpy as np

from mock_nidaqmx import DAQ

TEST_DURATION = 6  # In seconds
MAX_JITTER = 10  # In ms
PERIOD = 2_000  # In ms


class TestSignalJitter(unittest.TestCase):
    """
    Test if the signal jitter is within acceptable range.
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

        # Init the variables to track the sampling process.
        start = time.perf_counter()
        delays = np.array([])
        prev_state = None
        prev_time = start
        samples_count = 0

        while True:
            # Store the current time to be constant for each iteration.
            now = time.perf_counter()

            # Perform read and count sample as read.
            state = device.read_digital("Dev1/0")
            samples_count += 1

            # Init the previous state if it's None.
            if prev_state is None:
                prev_state = state

            # Store delay time in list if state changed.
            if state != prev_state:
                delays = np.append(delays, (now - prev_time))
                prev_state = state
                prev_time = now

            # Break the loop if the test duration is reached.
            if (now - start) > TEST_DURATION:
                break

        # Store the end time of the iterations.
        end = now

        # Compute jitters from the delays. The first delay is discarded as it
        # did not start synchonized with the square wave.
        jitters = delays[1:] * 1000 - (PERIOD / 2)

        # Compute the percentage of failed samples, number of samples per
        # second. And mean, std, min and max of the absolute values of the
        # jitters.
        jitters_abs = np.abs(jitters)

        failed_percent = np.sum(jitters_abs > MAX_JITTER) / len(jitters) * 100
        samples_per_second = samples_count / (end - start)

        jitters_mean = jitters_abs.mean()
        jitters_std = jitters_abs.std()
        jitters_min = jitters_abs.min()
        jitters_max = jitters_abs.max()

        # Print results and stats.
        print(f"\n{self.__class__.__name__}")
        print(
            f"\tMean: {jitters_mean:.3f}ms, Std: {jitters_std:.3f}ms, Min: {jitters_min:.3f}ms, Max: {jitters_max:.3f}ms"
        )
        print(
            f"\tSamples per second: {samples_per_second:,.0f}, Transitions: {len(jitters)}, Failed: {failed_percent:.1f}%"
        )

        # Check if all jitters are less then 'MAX_JITTER'. If not, print which
        # transition failed and what was it's jitter.
        for i, jitter in enumerate(jitters):
            if abs(jitter) > MAX_JITTER:
                print(f"\t\tFAIL - Jitter of transition {i:03} is over {MAX_JITTER}ms: {jitter:8.3f}ms")

        # Assert that all jitters are less then 'MAX_JITTER'.
        for jitter in jitters:
            self.assertLessEqual(abs(jitter), MAX_JITTER)


if __name__ == "__main__":
    unittest.main()
