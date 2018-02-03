"""keystation.py provides an interface to an M-Audio Keystation32 keyboard. You
can add callbacks to the interface in order to retrieve the keys and buttons
that were pressed.

Copyright (C) 2018  Brad Null

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Usage:
    import keystation

    def button_callback(button):
        ...
    def key_callback(note, velocity):
        ...

    keyboard = Keystation32()
    keyboard.add_button_callback(button_callback)
    keyboard.add_key_callback(key_callback)
    keyboard.open()

    ... wait forever or at least some amount of time

    keyboard.close()

Author: Brad Null
"""
import usb.core
import usb.util
import threading


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class UsbConnectionError(Error):
    """Exceptions raised for errors connecting to device.

    Attributes:
        message -- explanation of the connection error
    """
    def __init__(self, message):
        self.message = message


class Keystation32(object):
    """Class for interfacing with the M-Audio Keystation32 keyboard."""

    KEY_PREFIX = bytearray(b'\x09\x90')
    """First two bytes that indicate we got a key"""
    BUTTON_PREFIX = bytearray(b'\x0b\xb0')
    """First two bytes that indicate we got a button"""

    def __init__(self, vendor_id=0x0a4d, product_id=0x129d):
        """Constructor.

        Args:
            vendor_id (int): The vendor id of the keystation, default should
            be for the keystation32
            product_id (int): The product id of the keystation, default should
            be for the keystation32
        """
        # While this is set, keep reading stuff.
        self.__read_keys = True
        # Device file connection to USB device
        self.__device = None
        # The configuration information about the connected device
        self.__cfg = None
        # The interface to use when communicating with the device
        self.__interface = None
        # The final endpoint to use when reading from the device
        self.__endpoint = None
        # Vendor ID of the keyboard
        self.__vendor_id = vendor_id
        # Product ID of the keyboard
        self.__product_id = product_id
        # The thread that will continuously poll the keyboard
        self.__polling_thread = None
        # Callback that is called when a key is pressed
        self.__key_callback = None
        # Callback that is called when a button is pressed
        self.__button_callback = None


    def __del__(self):
        """Release the device when this object is deleted"""
        # Try to join again just in case the user didn't call close()
        self.close()
        # Let the OS take the interface back if it wants
        usb.util.release_interface(self.__device,
                                   self.__interface.bInterfaceNumber)

    def open(self):
        """Open the connection to the keyboard device.

        Raises:
            UsbConnectionError: Error connecting to keystation device.
        """
        # Find the device we were looking for; an M-Audio Keystation Mini32
        self.__device = usb.core.find(idVendor=self.__vendor_id,
                                      idProduct=self.__product_id)

        if self.__device is None:
            raise UsbConnectionError("Unable to find the M-Audio Keystation32.")

        # Set the active configuration. With no arguments, the first
        # configuration will be the active one
        self.__device.set_configuration()

        # Get the endpoint instance
        self.__cfg = self.__device.get_active_configuration()
        # Find the interface subclass of 0x3 which should be the keyboard and
        # buttons
        for self.__interface in self.__cfg:
            if self.__interface.bInterfaceSubClass == 3:
                break

        # Make sure that the kernel doesn't have ahold of the device, if it does
        # force it to hand it over!
        if self.__device.is_kernel_driver_active(
                self.__interface.bInterfaceNumber) is True:
            self.__device.detach_kernel_driver(
                self.__interface.bInterfaceNumber)
            usb.util.claim_interface(self.__device,
                                     self.__interface.bInterfaceNumber)

        # Find the endpoint for reading from the device
        self.__endpoint = usb.util.find_descriptor(
                self.__interface,
                custom_match=
                lambda e:
                usb.util.endpoint_direction(e.bEndpointAddress) ==
                usb.util.ENDPOINT_IN)

        if self.__endpoint is None:
            raise UsbConnectionError("Unable to connect to device endpoint for "
                                     "M-Audio Keystation32.")

        # Kick off the polling thread
        self.__polling_thread = threading.Thread(target=self.__poll)
        self.__polling_thread.start()

    def close(self):
        """Close the device when. Must be called to successfully stop polling
        """
        self.__read_keys = False
        self.__polling_thread.join(timeout=1000)

    def add_key_callback(self, callback):
        """Add a callback function to call when a key on the keyboard is
        pressed.

        Args:
            callback (func): The function that will be called when the key is
            pressed. Must be of the follwing form:

            def key_callback(note, vel):
                \"""Callback to use when a key is pressed on the keyboard

                Args:
                note (int): Integer indicating the key that was pressed
                vel (int): Velocity of the key being pressed
                \"""
        """
        self.__key_callback = callback

    def remove_key_callback(self):
        """Remove the currently set callback for key pressed."""
        self.__key_callback = None

    def add_button_callback(self, callback):
        """Add a callback function to call when a key on the keyboard is
        pressed.

        Args:
            callback (func): The function that will be called when the key is
            pressed. Must be of the follwing form:

            def key_callback(note, vel):
                \"""Callback to use when a key is pressed on the keyboard

                Args:
                note (int): Integer indicating the key that was pressed
                vel (int): Velocity of the key being pressed
                \"""
        """
        self.__button_callback = callback

    def remove_button_callback(self):
        """Remove the currently set callback for button pressed."""
        self.__button_callback = None

    def __poll(self):
        """Worker thread to continuously read input from the keyboard.

        Raises:
            USBError: Error in the pyusb library when communicating with device
        """

        # Keep reading until we are told to stop
        while self.__read_keys:
            try:
                # Read from the device, should only return 4 bytes
                ret = self.__device.read(self.__endpoint.bEndpointAddress,
                                         self.__endpoint.wMaxPacketSize)
                # Make sure we got the expected amount of data back
                if (len(ret) % 4) != 0:
                    print("WARNING! Received wrong amount of bytes:", len(ret))
                    continue

                # One message should be exactly 4 bytes
                for i in range(0, len(ret), 4):
                    # Determine if we saw a key or a button press
                    if ret[i:i+2] == self.KEY_PREFIX and \
                            self.__key_callback is not None:
                        self.__key_callback(ret[i+2], ret[i+3])
                    elif ret[i:i+2] == self.BUTTON_PREFIX and \
                            self.__button_callback is not None:
                        self.__button_callback(ret[i+2:i+4])

            except usb.core.USBError as usb_err:
                # Ignore timeout errors
                if usb_err.errno == 60:
                    continue
                else:
                    raise usb_err
