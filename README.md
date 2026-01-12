# KDE Wallpaper Updater

This is a script meant to automate the process of getting a new default wallpaper in KDE Plasma.


## How to use it

Open a terminal window and run the following commands:

```
# Enter the repo
cd  [path to this repo on your local machine]

# Create a new virtual environment in the current directory named "venv"
python -m venv venv

# Activate the "venv" virtual environment
source venv/bin/activate

# Install necessary Python modules into the virtual environment
pip install gitpython pillow

# Run it and follow the prompts
python3 ./updater.py

# Leave the virtual environment
deactivate
```


## Assets

This repository features assets for the light, dark and twilight global themes as well as the SDDM login screen.

These are overlaid ontop of the new wallpaper, and updated.

In order to create the original images, they were produced on a fresh user, with the browser and some extra tray icons removed (notifications, contacts, update). The time was set between screenshots for consistency between them. Each window (panel, Kickoff, Dolphin, Dolphin's About KDE) were individually screenshot by Spectacle and combined, with light/dark themes selected, and combined in Pinta with regard for pixel accuracy.

The login screen is more difficult, using `sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/breeze`. With GammaRay, the time can be fixed and other users removed, or the user name and icon changed to match. In order to get transparency, the wallpaper image was made not visible and the window background colour set to transparent. This breaks rendering, but GammaRay can take a screenshot that is correct (it's hidden in the File menu up top). If it produces a screenshot with some corruption, visibilities can be toggled and multiple screenshots taken to stitch together. Finally, a transparent colour was filled in a layer beneath to slightly darken the wallpaper image that would be placed underneath.

If you choose to update these assets in the future, good luck!
