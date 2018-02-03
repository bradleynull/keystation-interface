# KeystationMini32 Interface

A simple Python class for interfacing with the USB M-Audio KeystationMini32. 
This will probably work for more classes of keyboards, but I just wanted it for
the 32 for now. Feel free to contribute!

## Setup

Just install the a virtual environment with the requirements file provided. 
You'll want to look at the 
[pyusb installation instructions](https://github.com/pyusb/pyusb) when 
installing. You should only need `libusb` up and running.

```bash
$ virtualenv ./venv
...
$ . ./venv/bin/activate
(venv) $ pip install -r ./requirements.txt
Collecting pyusb==1.0.2 (from -r ./requirements.txt (line 1))
Installing collected packages: pyusb
Successfully installed pyusb-1.0.2
```

## Usage
```python
import keystation

def button_callback(button):
    ...
    
def key_callback(note, velocity):
    ...

keyboard = keystation.Keystation32()
keyboard.add_button_callback(button_callback)
keyboard.add_key_callback(key_callback)
keyboard.open()

... wait forever or at least some amount of time

keyboard.close()
```

