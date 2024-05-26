import random
import time
import unittest

from mock_nidaqmx import DAQ

TEST_DURATION = 11  # In seconds
MIN_SAMPLES_PER_SECOND = 100


class TestDaqSampling(unittest.TestCase):
    """
    Test the DAQ sampling rate, as in order to achieve a 10ms resolution, we
    need to sample at least 100Hz. This test differs from the other ones as
    we are not simulating a square wave output, we are only measuring how
    fast can the python script read from the DAQ.
    """

    def test_read(self) -> None:
        # Init the device
        device = DAQ()

        # Init the variables to track the sampling process.
        samples_count = 0

        # Context manager to mimic the original 'nidaqmx' module.
        with device.Task() as task:

            # Configure the channel for the task to read.
            task.di_channels.add_di_chan("Dev1/0")

            # Perform reads.
            start = time.perf_counter()
            while True:
                # Store the current time to be constant for each iteration.
                now = time.perf_counter()

                # Perform a read and count sample as read.
                task.read()
                samples_count += 1

                # Break the loop if the test duration is reached.
                if (now - start) > TEST_DURATION:
                    break

        # Store the end time of the iterations.
        end = now

        # Calculate the number of samples per second
        samples_per_second = samples_count / (end - start)

        # Print the results
        print(f"\n\n{self.__class__.__name__}.{self.test_read.__name__}()")
        print(f"\tSamples per second: {samples_per_second:,.0f}")

        # Print "FAIL" if the number of samples per second is less than the
        # minimum
        if samples_per_second < MIN_SAMPLES_PER_SECOND:
            print("\t\tFAIL")

        # Assert that the number of samples per second is greater than or equal
        # to the minimum
        self.assertGreaterEqual(samples_per_second, MIN_SAMPLES_PER_SECOND)


class TestDaqSamplingIrregular(unittest.TestCase):
    """
    Test the DAQ sampling rate with random delays injected between samples.
    This is done to simulate an irregular sampling rate that fails to meet the
    100hz requirement.
    """

    def test_read(self) -> None:
        # Init the device
        device = DAQ()

        # Init the variables to track the sampling process.
        samples_count = 0

        # Context manager to mimic the original 'nidaqmx' module.
        with device.Task() as task:

            # Configure the channel for the task to read.
            task.di_channels.add_di_chan("Dev1/0")

            # Perform reads.
            start = time.perf_counter()
            while True:
                # Store the current time to be constant for each iteration.
                now = time.perf_counter()

                # Perform a read, count sample as read and sleep random amount
                # of time.
                task.read()
                samples_count += 1
                time.sleep(random.random() * 0.05)

                # Break the loop if the test duration is reached.
                if (now - start) > TEST_DURATION:
                    break

        # Store the end time of the iterations.
        end = now

        # Calculate the number of samples per second
        samples_per_second = samples_count / (end - start)

        # Print the results
        print(f"\n\n{self.__class__.__name__}.{self.test_read.__name__}()")
        print(f"\tSamples per second: {samples_per_second:,.0f}")

        # Print "FAIL" if the number of samples per second is less than the
        # minimum
        if samples_per_second < MIN_SAMPLES_PER_SECOND:
            print("\t\tFAIL")

        # Assert that the number of samples per second is greater than or equal
        # to the minimum
        self.assertGreaterEqual(samples_per_second, MIN_SAMPLES_PER_SECOND)


if __name__ == "__main__":
    unittest.main()
