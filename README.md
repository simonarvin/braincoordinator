# Brain Coordinator [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0) [![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/simonarvin/braincoordinator/issues) ![version](https://img.shields.io/badge/version-0.1--beta-brightgreen) ![beta](https://img.shields.io/badge/-beta-orange)

<p align="center">
<img src="https://raw.githubusercontent.com/simonarvin/braincoordinator/main/braincoordinator/graphics/logo.svg" width = "500">
</p>

Brain Coordinator is a Python 3-based stereotaxic coordinator compatible with any stereotaxic atlas. This software is actively maintained: Users are encouraged to contribute to its development.

## Features ##
- [x] **Easily coordinate your surgerical procedures**, with an angle or not.
- [x] Compatible with **any stereotaxic atlas**.
- [x] **Correct** bregma/lambda discrepancies.
- [x] **Avoid** sensitive structures.
- [x] Vary your path of entry to **reduce confounders**.
- [x] **Actively maintained**.

## Overview ##
- [Getting started](#getting-started)
- [Bringing data to the lab](#bringing-data-to-the-lab)
- [How it works](#how-it-works)
- [Authors](#authors)


## Getting started ##

### Installation ###

Download Brain Coordinator by cloning the repository:
```
git clone https://github.com/simonarvin/braincoordinator.git
```

You may want to use a Conda or Python virtual environment when installing `braincoordinator`, to avoid mixing up with your system dependencies.

<p align="right">
    <img src="https://raw.githubusercontent.com/simonarvin/braincoordinator/main/braincoordinator/graphics/terminal_readme.svg" align="right" height="200">
</p>

Using pip and a virtual environment:

```python -m venv venv```

```source venv/bin/activate```

```(venv) pip install .```

> Remember to ```cd [path]``` to your braincoordinator directory.

Then, initiate ```braincoordinator``` by running

```braincoordinator```

> Write ```braincoordinator --help``` for instructions.

### Add an atlas ###

To see a list of all available atlases, run

```braincoordinator --get list```

To download and install an atlas, run

```braincoordinator --get [atlas_id]```

> e.g., ```braincoordinator --get mouse_allen``` to add the mouse brain atlas from Allen Institute.

Finally, to test your new atlas, run

```braincoordinator --animal [atlas_id]```

### Controls ###
Brain Coordinator is based on simple keyboard commands and mouse clicks.
- <kbd>A</kbd>/<kbd>S</kbd>: previous/next coronal slice.
- <kbd>Z</kbd>/<kbd>X</kbd>: previous/next sagittal slice.
- <kbd>D</kbd>: place marker at mouse location.
- <kbd>F</kbd>: remove most recent marker.
- <kbd>P</kbd>: save data-file.

Click and drag to move markers.

<p align="right">
    <img src="https://raw.githubusercontent.com/simonarvin/braincoordinator/main/braincoordinator/graphics/crunch.svg" align="right" height="300">
</p>

### Bringing data to the lab ###
Coming soon.
Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum

## Known issues ##
None yet.

## License ##
This project is licensed under the MIT License. Note that the software is provided "as is", without warranty of any kind, express or implied.

<p align="right">
    <img src="https://github.com/simonarvin/eyeloop/blob/master/misc/imgs/constant.svg?raw=true" align="right" height="180">
    </p>

## Authors ##

**Lead Developer:**
Simon Arvin, sarv@dandrite.au.dk

