# Eyetracking_functions

# Install

## Requirements

### On Windows

1. __[Python 3.6](https://www.python.org/downloads/)__

    This program requires Python 3.6. It was tested on versions 3.6.5 and 3.6.7.

2. __[PIP](https://pypi.org/project/pip/)__

    Further dependencies will be handled by  Pipenv, which requires the PIP package manager of Python.
    To install pip:
```
apt install pip
```

3. __[PIPENV](https://docs.python-guide.org/dev/virtualenvs/)__

    Dependencies are handled Pipenv. To install Pipenv:
```
pip install pipenv
```

### On Ubuntu

1. __[Python 3.6](https://www.python.org/downloads/)__

    This program requires Python 3.6. It was tested on versions 3.6.5 and 3.6.7.

2. __[PIP](https://pypi.org/project/pip/)__
    On Ubuntu, there is a missing package for the gstreamer media player within the PyQt5 package.
    Thus, it is not possible to use Pipenv.
    All dependencies must therefore be installed using Pip.
```
apt install pip
```

3. __Python packages__
'''
pip install opencv-contrib-python
pip install attr
pip install sumtypes==0.1a4
pip install matplotlib
pip install opencv-contrib-python
'''

4. __PyQt5__
    First, install PyQt5 via Pip:
'''
pip install PyQt5
'''
Then (see https://github.com/pypa/packaging-problems/issues/211)
'''
apt install libqt5multimedia5-plugins
sudo rm /usr/local/lib/python3.6/dist-packages/PyQt5/Qt/plugins/mediaservice/libgstmediaplayer.so
sudo ln -s /usr/lib/x86_64-linux-gnu/qt5/plugins/mediaservice/libgstmediaplayer.so /usr/local/lib/python3.6/dist-packages/PyQt5/Qt/plugins/mediaservice/libgstmediaplayer.so
'''

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

### On Ubuntu
If the video does not play, and you get errors like
'''
gst_vaapi_window_reconfigure: assertion 'window != NULL' failed
gst_vaapi_window_get_size: assertion 'window != NULL' failed
'''
You can try to remove gstreamer1.0-vaapi:
'''
sudo apt purge gstreamer1.0-vaapi
'''
