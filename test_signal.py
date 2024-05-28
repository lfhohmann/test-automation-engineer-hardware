import random
import time
import unittest
from datetime import datetime as dt
from unittest.mock import patch
from uuid import uuid4

import numpy as np

import db
from mock_nidaqmx import DAQ

TEST_DURATION = 11  # In seconds
MAX_JITTER = 10  # In ms
PERIOD = 2_000  # In ms

tests_uuid = uuid4().hex
tests_timestamp = dt.now()

print(f"UUID: {tests_uuid}, TIMESTAMP: {tests_timestamp}")


def base_test(test_case: unittest.TestCase, device: DAQ) -> None:
    """
    A base test to make the code cleaner and more reusable. It is used by alld
    tests in this file.
    """

    # Init the variables to track the sampling process.
    delays = np.array([])
    states = np.array([])
    samples_count = 0
    prev_state = None
    prev_time = None

    # Context manager to mimic the original 'nidaqmx' module.
    with device.Task() as task:

        # Configure the channel for the task to read.
        task.di_channels.add_di_chan("Dev1/0")

        # Wait for the first state transition.
        while True:
            # Perform a read.
            state = task.read()

            # Init the previous state if it's None.
            if prev_state is None:
                prev_state = state

            # Break on first state transition.
            if state != prev_state:
                prev_time = time.perf_counter()
                prev_state = state
                break

        # Perform reads.
        start = time.perf_counter()
        while True:
            # Store the current time to be constant for each iteration.
            now = time.perf_counter()

            # Perform a read and count sample as read.
            state = task.read()
            samples_count += 1

            # Limiting the sampling rate yields more reliable results.
            time.sleep(1 / 5_000_000)

            # Store delay time and state in list if state changed.
            if state != prev_state:
                delays = np.append(delays, (now - prev_time))
                states = np.append(states, state)
                prev_state = state
                prev_time = now

            # Break the loop if the test duration is reached.
            if (now - start) > TEST_DURATION:
                break

    # Store the end time of the iterations.
    end = now

    # Compute jitters from the delays. The first delay is discarded as it
    # did not start synchonized with the square wave.
    jitters = delays * 1000 - (PERIOD / 2)

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

    # Prepare log message with results and stats.
    log_message = f""
    log_message += f"\n{test_case.__class__.__name__}"
    log_message += f"\n\tMean: {jitters_mean:.3f}ms, Std: {jitters_std:.3f}ms, "
    log_message += f"Min: {jitters_min:.3f}ms, Max: {jitters_max:.3f}ms"
    log_message += f"\n\tSamples per second: {samples_per_second:,.0f}, "
    log_message += f"Transitions: {len(jitters)}, Failed: {failed_percent:.1f}%"

    # Init variable to store if test passed or failed.
    passed = False

    # Check if all jitters are less then 'MAX_JITTER'. If not, log which
    # transition failed and what was it's jitter.
    for i, jitter in enumerate(jitters):
        if abs(jitter) > MAX_JITTER:
            log_message += f"\n\t\tFAIL - Jitter of transition {i:03} is over {MAX_JITTER}ms: {jitter:8.3f}ms"

    # If no jitters failed, then log "PASS" and set passed variable to True.
    if failed_percent == 0:
        log_message += "\n\t\tPASS"
        passed = True

    # Print log message and wait a little to prevent Github Actions from
    # showing the messages out of order.
    print(f"{log_message}\n", flush=True)
    time.sleep(1)

    # Store results in the database
    test = db.Test(
        name=f"{test_case.__class__.__name__}",
        times=np.cumsum(delays),
        states=states,
        passed=passed,
        log=log_message,
        uuid=tests_uuid,
        timestamp=tests_timestamp,
    )
    test.save()

    # Assert that all jitters are less then 'MAX_JITTER'.
    for jitter in jitters:
        test_case.assertLessEqual(abs(jitter), MAX_JITTER)


class TestSignalJitter(unittest.TestCase):
    """
    Test if the signal jitter is within acceptable range.
    """

    def __init__(self, methodName: str = "runTest") -> None:
        """
        Init the class and it's parent.
        """

        # Init parent with the required arguments.
        super().__init__(methodName)

        # Global class variables to track the state changes
        self.next_state_change_time = time.perf_counter()
        self.current_state = 0

    def side_effect_read(self, *args: list, **kwargs: dict) -> int:
        """
        Patch the 'read_digital()' function of the DAQ class to generate a
        square wave of 0.5Hz and 50% duty cycle.

        Returns:
            int:

            A 1 or 0 value for HIGH and LOW respectively.
        """

        # Store the current time to be constant for each function call.
        now = time.perf_counter()

        # If it is time to change the state then do so and compute the time
        # for the next state change.
        if now > self.next_state_change_time:
            self.current_state = not self.current_state

            self.next_state_change_time = now + (PERIOD / 2 / 1000)

        return self.current_state

    def test_read(self) -> None:
        # Context manager to patch "read()" function of the DAQ.Task class.
        with patch.object(DAQ.Task, "read", side_effect=self.side_effect_read):

            # Init the device
            device = DAQ()

            # Run the base test with the patched device.
            base_test(self, device)


class TestSignalJitterNoise(unittest.TestCase):
    """
    Test if the signal jitter is within acceptable range. A random jitter noise
    is injected into the signal to simulate a test failure.
    """

    def __init__(self, methodName: str = "runTest") -> None:
        """
        Init the class and it's parent.
        """

        # Init parent with the required arguments.
        super().__init__(methodName)

        # Global class variables to track the state changes
        self.next_state_change_time = time.perf_counter()
        self.current_state = 0

    def side_effect_read(self, *args: list, **kwargs: dict) -> int:
        """
        Patch the 'read_digital()' function of the DAQ class to generate a
        square wave of 0.5Hz and 50% duty cycle. A jitter of +-(2 * MAX_JITTER)
        delay will be injected to simulate jitter in the signal.

        Returns:
            int:

            A 1 or 0 value for HIGH and LOW respectively.
        """

        # Store the current time to be constant for each function call.
        now = time.perf_counter()

        # If it is time to change the state then do so and compute the time
        # for the next state change.
        if now > self.next_state_change_time:
            self.current_state = not self.current_state

            self.next_state_change_time = now + (PERIOD / 2 / 1000)
            self.next_state_change_time += random.uniform(-MAX_JITTER * 2 / 1000, MAX_JITTER * 2 / 1000)

        return self.current_state

    def test_read(self) -> None:
        # Context manager to patch "read()" function of the DAQ.Task class.
        with patch.object(DAQ.Task, "read", side_effect=self.side_effect_read):

            # Init the device
            device = DAQ()

            # Run the base test with the patched device.
            base_test(self, device)


class TestSignalRandomness(unittest.TestCase):
    """
    Test if the signal jitter is within acceptable range. Some state changes
    are randomly injected into the signal to simulate a test failure.
    """

    def __init__(self, methodName: str = "runTest") -> None:
        """
        Init the class and it's parent.
        """

        # Init parent with the required arguments.
        super().__init__(methodName)

        # Global class variables to track the state changes
        self.next_state_change_time = time.perf_counter()
        self.current_state = 0

    def side_effect_read(self, *args: list, **kwargs: dict) -> int:
        """
        Patch the 'read_digital()' function of the DAQ class to generate a
        square wave of 0.5Hz and 50% duty cycle. Random state changes are
        injected into the signal.

        Returns:
            int:

            A 1 or 0 value for HIGH and LOW respectively.
        """

        # Store the current time to be constant for each function call.
        now = time.perf_counter()

        # Inject random state transitions.
        if random.random() < 0.000075:
            self.current_state = not self.current_state
            return self.current_state

        # If it is time to change the state then do so and compute the time
        # for the next state change.
        if now > self.next_state_change_time:
            self.current_state = not self.current_state

            self.next_state_change_time = now + (PERIOD / 2 / 1000)

        return self.current_state

    def test_read(self) -> None:
        # Context manager to patch "read()" function of the DAQ.Task class.
        with patch.object(DAQ.Task, "read", side_effect=self.side_effect_read):

            # Init the device
            device = DAQ()

            # Run the base test with the patched device.
            base_test(self, device)


class TestSignalSingleSampleNoise(unittest.TestCase):
    """
    Test if the signal jitter is within acceptable range. Random state changes
    are injected for a single sample of the signal to simulate a test failure.
    """

    def __init__(self, methodName: str = "runTest") -> None:
        """
        Init the class and it's parent.
        """

        # Init parent with the required arguments.
        super().__init__(methodName)

        # Global class variables to track the state changes
        self.next_state_change_time = time.perf_counter()
        self.current_state = 0
        self.is_random = True

    def side_effect_read(self, *args: list, **kwargs: dict) -> int:
        """
        Patch the 'read_digital()' function of the DAQ class to generate a
        square wave of 0.5Hz and 50% duty cycle. Random state changes are
        injected into the signal for a single sample to simulate a fluke.

        Returns:
            int:

            A 1 or 0 value for HIGH and LOW respectively.
        """

        # Store the current time to be constant for each function call.
        now = time.perf_counter()

        # If last change was randomly set, change states again.
        if self.is_random:
            self.current_state = not self.current_state
            self.is_random = False

            return self.current_state

        # Inject randomly a fluke in the signal.
        if random.random() < 0.000075:
            self.current_state = not self.current_state
            self.is_random = True

            return self.current_state

        # If it is time to change the state then do so and compute the time
        # for the next state change.
        if now > self.next_state_change_time:
            self.current_state = not self.current_state

            self.next_state_change_time = now + (PERIOD / 2 / 1000)

        return self.current_state

    def test_read(self) -> None:
        # Context manager to patch "read()" function of the DAQ.Task class.
        with patch.object(DAQ.Task, "read", side_effect=self.side_effect_read):

            # Init the device
            device = DAQ()

            # Run the base test with the patched device.
            base_test(self, device)


if __name__ == "__main__":
    unittest.main()
