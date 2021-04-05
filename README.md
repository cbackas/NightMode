# Nightmode 

This script establishes a web socket connection to home assistant and subscribes to receive notifications when the power state of the desktop monitor's smart plug changes. When monitors are powered off it disables all Logitech LEDs until the power on state notification is received.

### LogiPy patch
Currently its using a patched version of logipy (https://github.com/bsynchron/logiPy/tree/patch-1), which enables usage with the newest Logitech G Hub and its legacy SDK dll's
