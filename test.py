import unittest

from mock_nidaqmx import DAQ


class TestDaq(unittest.TestCase):
    """
    Sample test for the daq class
    """

    def test_read(self) -> None:
        # Init the device
        device = DAQ()

        # Perform read
        state = device.read_digital("Dev1/0")

        # Check if the result is valid
        self.assertIn(state, [0, 1])


if __name__ == "__main__":
    unittest.main()
