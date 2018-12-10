# Eyetracking_functions

# Install

## Requirements

1. __[Python 3](https://www.python.org/downloads/)__

    This program requires Python3. It was tested on versions 3.6.5 and 3.6.7.

2. __[Pipenv](https://pypi.org/project/pipenv/)__

    The library dependencies are handeld by `pipenv`.
    It is based on the `pip` package manager, which is installed by default with most Python distributions.
    To install `pipenv` form `pip`, type

```
pip install pipenv
```

## Installation

Download the program folder and type

```
pipenv install
```

1. For ubuntu: see https://github.com/pypa/packaging-problems/issues/211
apt install libqt5multimedia5-plugins
sudo rm /usr/local/lib/python3.6/dist-packages/PyQt5/Qt/plugins/mediaservice/libgstmediaplayer.so
sudo ln -s /usr/lib/x86_64-linux-gnu/qt5/plugins/mediaservice/libgstmediaplayer.so /usr/local/lib/python3.6/dist-packages/PyQt5/Qt/plugins/mediaservice/libgstmediaplayer.so

# Usage

To launch the gui, type

```
make run
```
