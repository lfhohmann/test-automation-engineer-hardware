# Test Automation Engineer - Hardware

## Premisses

### DAQ Specs

The chosen DAQ is the [`NI USB-6001`](https://www.ni.com/pt-br/shop/model/usb-6001.html), it has the bellow specs:
* 8 analog input channels with 14bits resolution.
* 2 analog output channels with 14bits resolution.
* 13 digital I/O ports.
* 20 Ks/s sampling rate.
* 32 bits counter with maximum frequency of 5 MHz.

## Tests

The scripts will perform the following tests:

* DAQ Sampling rate
    * Test the DAQ device itself to make sure it is within specs before testing with the actual input signal.
        * Simulate regular operation.
        * Inject random delays in between samples to simulate sampling rates bellow the specifications.
* Input signal
    * Check for signal integrity, measure the delay between each transition from high to low and vice versa.
        * Simulate regular operation *(0.5hz)*.
        * Inject random delays in between transitions to simulate jitter in the signal.
        * Inject noise into the signal, transitioning states randomly during the sampling duration.
        * Inject random noise for single samples to check if the tests are quick enough to detect it.

The `mock_nidaqmx.py` module was created to emulate the original `nidaqmx` module as close as possible, in order to do so, multiple classes were created, the `Task` class is a context manager to mimic the original module behavior. The `read` function returns random values for both Analog and Digital inputs.

*It was considered to simply patch the original `nidaqmx` module instead of creating a mocking one, but doing so would require patching too many functions and methods.*

In order to measure jitters as low as ±10ms, we need to have a sampling rate of 100Hz or higher, if the script fails to poll at a frequency of at least 100hz the test results of the square wave signal won't have enough resolution. The `test_daq.py` script performs 2 sampling rate tests:
*   Regular operation *(polling the DAQ as fast as possible)*.
*   Irregular operation *(random delays are injected between samples to simulate a test failure)*.

After evaluating the limitations of polling rate of the combination of the DAQ device, we can simulate and test the square wave signal. Those tests are performed by the `test_signal.py` script, it has a `base_test` function that is used for every test. The function performs the following tasks:
*   Receives the `test_case` and the patched DAQ `device` instances *(more information about the patched device bellow)*.
*   Inits the context manager for the devices read task.
*   Sets up the devices channels.
*   Waits for the first state transition to start sampling the signal.
*   Samples the signal during the specified `TEST_DURATION` and stores in a list the time delta between each sample.
*   Computes stats of the signal jitter, like mean, standard deviation, minimum and maximum values.
*   Computes the percentage of signal transitions that failed the limit of ±10ms window and the average number of samples per second.
*   Shows log messages in the console of which signal transitions failed and by how much.
*   Stores the results in a mongoDB database for further analysis if necessary *(more information about it bellow)*.
*   Asserts using the `unittest` python module if the jitters meet the maximum value of ±10ms requirement.

In order to achieve better performance, the `base_test` function uses the `time.perf_counter()` insted of `time.time()` function as it is more reliable, it also uses numpy instead of lists for storing the jitters values and lastly it sleeps for 0.2us between samples, as according to the tests performed it improves reliability and repeatability *(running the tests without this delay did yield different results when running it locally versus on the Github Actions servers)*.

There is a test case for each of the tests described above in the `Input signal` section, each case has a different `side_effect_read` function that is used to patch the DAQ `device` instance in order to simulate different types of signals and jitters, because the device needs to be patched, it is instantiated inside a context manager of the test case instead of the `base_test` function. As mentioned, all test cases utilize the `base_test` function to keep the tests identical and consistant.

A streamlit app [[`link for the app`]](https://test-automation-engineer-hardware-data.streamlit.app/) was developed to visually inspect the signals, this makes it easier to detect anomalies and patterns. As mentioned above, the results of each test are stored in a mongoDB server, those results store the delays between each sample, the log messages, the test name and an uuid and timestamp of each script execution. The user can sort the tests by timestamp, retrieve the desired one by name and view the waveform on an interactive plotly graph.

## Notes
* The repository is divided into `master`, `dev` and other branches that were used to develop specific features. All the final code was merged into the `master` branch.
* The MongoDB instance is hosted on a MongoDB Atlas free tier server.
* The Streamlit app is hosted on Streamlit Cloud.
* The MondoDB `host`, `user` and `password` values are stored as environment variables and managed with Github Secrets and Streamlit Secrets.

## Observations
* Executing the DAQ Tests to check sampling rate, show that the Python Interpreter is more than capable of simulating the sampling rate of 20ks/s *(both locally as in Github Actions servers)*.
* The Python Interpreter is also capable of generating the signal waveform with accuracies better than the necessary ±10ms window, but it was not able to reach the full 20ks/s sampling rate specified by the [`NI USB-6001`](https://www.ni.com/pt-br/shop/model/usb-6001.html) DAQ datasheet *(Neither locally nor on Github Actions servers)*.

## Possible future improvements

* Implement authentication to the streamlit app.
* Add more graphs to the streamlit app.
    * DAQ tests values.
    * Number of tests passed over time.
    * Stats values over time.
* Store whether the tests were ran locally or on Github Actions servers.