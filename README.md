# VHI Parser

## Brief
Vegetation Health Index - represents the overall health of vegetation.

This parser gets VHI data from star.nesdis.noaa.gov and plots graphs based on time series in different regions of Ukraine.

## Screenshots

### Regions comparison + extremum points
![compare](https://user-images.githubusercontent.com/17964131/161959393-dacd10ae-53c7-4bde-bdc6-d8f493a119da.png)

### Dark theme + drought graph
![dark](https://user-images.githubusercontent.com/17964131/161959544-1a3abc09-3349-4dba-bd24-a6f9050beab7.png)

## Installation and running
Python 3.7 or higher is required

### Install Python dependencies
- Fedora
```
$ sudo dnf install python3-matplotlib-gtk3 lxml python3-gobject python3-pandas python3-requests python3-wheel
```

- Others (in virtualenv)

Make sure python-gobject and python-virtualenv are installed in your system.

Activate virtualenv with:
```
$ source venv.sh
```

Then install dependencies:

```
$ pip install -r requirements.txt
```

### Run
```
$ python3 app.py
```
