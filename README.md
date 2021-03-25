# Nightmode 

I keep my computer on at night. My monitor's power goes through a smart plug so they can be automatically turned off with the rest of the lights in the room via Home Assistant. Before this script I would have to manually turn off my Logitech keyboard's LED back light every night.

This script establishes a web socket connection to home assistant and subscribes to receive notifications when the power state of the desktop monitor's smart plug changes. When monitors are powered off it disables all Logitech LEDs until the power on state notification is received.