"""main.py provides a demo driver for using the Keystation32 class.

Copyright (C) 2018 Brad Null

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
"""
from keystation import Keystation32
import signal
import binascii

if __name__ == "__main__":

    # Keep doing stuff while this flag is enabled
    read_keys = True

    def signal_handler(signum, frame):
        """Handle incoming signals by turning read_keys to false.

        Args:
            signum (int): The signal that was just received
            frame (int): The frame for the signal
        """
        global read_keys
        read_keys = False
    # Install typical signal handlers so we stop as expected
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    def key_callback(note, vel):
        """Callback to use when a key is pressed on the keyboard

        Args:
            note (int): Integer indicating the key that was pressed
            vel (int): Velocity of the key being pressed
            """
        if vel == 0:
            print("Released", end='')
        else:
            print("Pressed", end='')
        print(" note", note, " at velocity", vel)

    def button_callback(button):
        """Callback to use when a button is pressed on the keyboard"""
        print("You pressed a button: ", binascii.hexlify(button))

    # Create the keyboard and lets go!
    keyboard = Keystation32()
    keyboard.add_button_callback(button_callback)
    keyboard.add_key_callback(key_callback)
    keyboard.open()
    while read_keys:
        pass
    keyboard.close()
