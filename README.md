# Eyetracking_functions

# Install

## Requirements

### On Debian

1. __[Python 3.6](https://www.python.org/downloads/)__

    This program requires Python 3.6. It was tested on versions 3.6.5 and 3.6.7.

2. __[PIP](https://pypi.org/project/pip/)__

    Further dependencies will be handled by the PIP package manager of Python.
    To install pip:
```
apt install pip
```

3. __Packages__

```

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
