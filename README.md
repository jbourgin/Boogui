# Eyetracking_functions

# Install

## Requirements

### On Debian

1. __[Python 3.6](https://www.python.org/downloads/)__

    This program requires Python 3.6. It was tested on versions 3.6.5 and 3.6.7.

2. __[PIP](https://pypi.org/project/pip/)__

    Further dependencies will be handled by the Pipenv, which requires the PIP package manager of Python.
    To install pip:
```
apt install pip
```

3. __[PIPENV](https://docs.python-guide.org/dev/virtualenvs/)__

    Dependencies are handled Pipenv. To install Pipenv:
```
pip install pipenv
```

4. __MISC__
For ubuntu: see https://github.com/pypa/packaging-problems/issues/211
apt install libqt5multimedia5-plugins
sudo rm /usr/local/lib/python3.6/dist-packages/PyQt5/Qt/plugins/mediaservice/libgstmediaplayer.so
sudo ln -s /usr/lib/x86_64-linux-gnu/qt5/plugins/mediaservice/libgstmediaplayer.so /usr/local/lib/python3.6/dist-packages/PyQt5/Qt/plugins/mediaservice/libgstmediaplayer.so

## Installation

Once the requirements are installed, the python environment is built by
```
pipenv install
```

# Usage

To launch the gui, type

```
make run
```
or
```
pipenv run python test_gui.py
```
