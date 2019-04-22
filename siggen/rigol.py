""" Control script for the RIGOL DG1022 Function/Arbitrary Waveform Generator.
This control script should work for all RIGOL DG10xx models, but everything
was tested on the DG1022 available at the Science Center Physics Lab in room
102 and 106.

Documentation: A programming manual can be found at the following link
    http://int.rigol.com/File/UploadSpecific/20150909/DG1000%20Programming%20Guide.pdf

Troubleshooting:
    If pyvisa says "Found a device whose serial number cannot be read... try
    making sure your user has permissions to read usb

        ```
        sudo groupadd usbusers
        sudo usermod -a -G usbusers <USERNAME>
        ```    
    
    Also, you will have to add a USB rule.
       
        ```
        sudo vim /etc/udev/rules.d/99-com.rules
        ```
    
    Add this line to it, and save.
     
        ```
        SUBSYSTEM=="usb", MODE="0666", GROUP="usbusers"
        ```

    Then, restart the USB service, and everything should be working and you
    should be able to see the RIGOL signal generator inside the list of devices
    when searching for one using pyvisa.
"""
import visa
import time


class SignalGenerator(object):
    def __init__(self):
        # Try to connect to the first RIGOL siggen found.
        rm = visa.ResourceManager('@py')
        devices = rm.list_resources()
        devnames = []
        for d in devices:
            # RIGOL signal generators should have more than 8 colons and also
            # should be connected via USB, so we can filter using that.
            if d.count(':') >= 8 and 'USB' in d:
                devnames.append(d)

        if not devnames:
            print('Only found devices: %s' % str(devices))
            raise RuntimeError('Could not find a USB instrument, check connection')
        

        rigol_devname = None
        # Search through the filtered USB devices and make sure we're connecting
        # to a RIGOL signal generator, since we're also connecting to oscilloscopes
        # through USB.
        for d in devnames:
            potential_device = rm.get_instrument(d)
            potential_device.write("*IDN?")
            time.sleep(0.2)  # give the device a bit of time to respond
            test_id = potential_device.read()
            print("Checking out device with ID: %s" % test_id)

            if 'RIGOL' in test_id:
                rigol_devname = d
                self.device = potential_device
                self.name = test_id
                break
            else:
                print("This is not a signal generator")
                potential_device.close()

        if not rigol_devname:
            raise RuntimeError('Could not find a USB instrument, check connection')

    def set_frequency(self, frequency, amplitude=20, offset=0):
        """Set the frequency, voltage amplitude, and voltage offset of the
        function generator. Sends it out as a sine wave.
            Frequency: 0 to 20,000,000 Hz
            Amplitude (V): 0 to 20 V
            Offset: -10 to 10 V [default 0]
        """
        CMD = "APPLy:SINusoid"
        CMD += " {},{},{}".format(frequency, amplitude, offset)
        self.device.write(CMD)


if __name__ == '__main__':
    pass