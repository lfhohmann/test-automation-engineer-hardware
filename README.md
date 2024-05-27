# Test Automation Engineer - Hardware

## Premisses

### DAQ

The chosen DAQ is the [`NI USB-6001`](https://www.ni.com/pt-br/shop/model/usb-6001.html), it has the following specs:
* 8 analog input channels with 14bits resolution.
* 2 analog output channels with 14bits resolution.
* 13 digital I/O ports.
* 20 Ks/s sampling rate.
* 32 bits counter with maximum frequency of 5 MHz.

### Tests

* DAQ Sampling rate
    * Test the DAQ device itself to make sure it is within specs before testing with the actual input signal.
        * Simulate regular operation *(20khz)*.
        * Inject random delays in between samples to simulate sampling rates bellow the specifications.
* Input signal
    * Check for signal integrity, measure the delay between each transition from high to low.
        * Simulate regular operation *(0.5hz)*.
        * Inject random delays in between transitions to simulate jitter in the signal.
        * Inject noise into the signal, transitioning from high to low or low to high ramdonly during the sampling duration.
        * Inject random noise for single samples to check if the tests are quick enough to detect it.
