'''
This is a demonstration script for using the TIDEGAUGE object in the COAsT
package. This object has strict data formatting requirements, which are
outlined in TIDEGAUGE.py.
'''

# Begin by importing coast and other packages
import coast
import datetime
import numpy as np
import matplotlib.pyplot as plt

# And by defining some file paths
fn_nemo_dat  = './example_files/COAsT_example_NEMO_data.nc'
fn_nemo_dom  = './example_files/COAsT_example_NEMO_domain.nc'
fn_tidegauge = './example_files/tide_gauges/lowestoft-p024-uk-bodc'
fn_tidegauge_mult = './example_files/tide_gauges/l*'

# We need to load in a NEMO object for doing NEMO things.
nemo = coast.NEMO(fn_nemo_dat, fn_nemo_dom, grid_ref='t-grid')

# And now we can load in our ALTIMETRY data. By default, TIDEGAUGE is set up
# to read in GESLA ASCII files. However, if no path is supplied, then the
# object's dataset will be initialised as None. Custom data can then be loaded
# if desired, as long as it follows the data formatting for TIDEGAUGE. Here
# we load data between two specified dates:
date0 = datetime.datetime(2007,1,10)
date1 = datetime.datetime(2007,1,16)
tidegauge = coast.TIDEGAUGE(fn_tidegauge, date_start = date0, date_end = date1)

# Before comparing our observations to the model, we will interpolate a model
# variable to the same time and geographical space as the tidegauge. This is
# done using the obs_operator() method:
tidegauge.obs_operator(nemo, mod_var_name='ssh', time_interp='nearest')

# Doing this has created a new interpolated variable called interp_ssh and
# saved it back into our TIDEGAUGE object. Take a look at tidegauge.dataset
# to see for yourself.
#
# Next we will compare this interpolated variable to an observed variable
# using some basic metrics. The basic_stats() routine can be used for this,
# which calculates some simple metrics including differences, RMSE and
# correlations. NOTE: This may not be a wise choice of variables.
stats = tidegauge.basic_stats('interp_ssh', 'sea_level')

# Take a look inside stats.dataset to see all of the new variables. When using
# basic stats, the returned object is also an TIDEGAUGE object, so all of the
# same methods can be applied. Alternatively, if you want to save the new
# metrics to the original altimetry object, set create_new_object = False.
#
# Now we will do a more complex comparison using the Continuous Ranked
# Probability Score (CRPS). For this, we need to hand over the model object,
# a model variable and an observed variable. We also give it a neighbourhood
# radius in km (nh_radius). This may take a minute to run.
crps = tidegauge.crps(nemo, model_var_name = 'ssh', obs_var_name = 'sea_level',
                      nh_radius = 20)

# Again, take a look inside crps.dataset to see some new variables. Similarly
# to basic_stats, create_new_object can be set to false to save output to
# the original tidegauge object.
#
# TIDEGAUGE has ready made quick plotting routines for viewing time series
# and tide gauge location. To look at the tide gauge location:
fig, ax = tidegauge.plot_on_map()

# Or to look at a time series of the sea_level variable:
fig, ax = tidegauge.plot_timeseries('sea_level')

# Note that start and end dates can also be specified for plot_timeseries().
#
# As stats and crps are also TIDEGAUGE objects, the same time series plotting
# functionality can be used:
crps.plot_timeseries('crps')
stats.plot_timeseries('absolute_error')

# Lets do some analysis on just the data in TIDEGAUGE. We can attempt to remove
# the tidal signal using a Doodson x0 filter. To do this, we must first
# resample the data to an hourly frequency. TIDEGAUGE.resample_mean() can do
# just this using averaging.
tidegauge.resample_mean('sea_level', '1H')

# Here we have resampled the 'sea_level' object. Now, in tidegauge.dataset
# there is a new variable sea_level_1H, along a new dimension time_1H. 1H
# can be subsitituted for other strings (e.g. 1D = 1 day) or using timedelta
# object.
#
# Now, we can apply the doodson x0 filter to the new variable:
tidegauge.apply_doodson_x0_filter('sea_level_1H')

# The new variable tidegauge.sea_level_1H_dx0 contains the filtered data.
# Now lets do another time series plot, but this time looking at the three
# variables sea_level, sea_level_1H and sea_level_1H_dx0. We can do this
# by providing a list of variable names:
f,a = tidegauge.plot_timeseries(['sea_level', 'sea_level_1H', 'sea_level_1H_dx0'])

# Each TIDEGAUGE object only holds data for a single tidegauge. There is some
# functionality for dealing with multiple gauges in COAsT. To load multiple
# GESLA tidegauge files, we use the static method create_multiple_tidegauge().
# This routine takes a list of files or a wildcard string and loads them all
# into a list of TIDEGAUGE objects.
from coast.TIDEGAUGE import TIDEGAUGE
date0 = datetime.datetime(2007,1,10)
date1 = datetime.datetime(2007,1,12)
tidegauge_list = TIDEGAUGE.create_multiple_tidegauge(fn_tidegauge_mult,
                                                           date0,date1)

# Now that we have tidegauge_list, we can plot the locations of all tide gauges
# as follows:
fig, ax = TIDEGAUGE.plot_on_map_multiple(tidegauge_list)

# To do analysis on multiple gauges, a simple looping script can be setup.
# For example, to obtain basic stats:
for tg in tidegauge_list:
    tg.obs_operator(nemo, 'ssh')
    tg.basic_stats('interp_ssh', 'sea_level', create_new_object=False)

# And now some of these new values can be plotted on a map, again using
# plot_on_map_multiple:
fig, ax = TIDEGAUGE.plot_on_map_multiple(tidegauge_list, color_var_str='rmse')


#%% Alternatively load in data obtained using the Environment Agency (England)
#  API. These are only accessible for the last 28 days. This does not require
# an API key.
#  Details of available tidal stations are recovered with:
#  https://environment.data.gov.uk/flood-monitoring/id/stations?type=TideGauge
# Recover the "stationReference" for the gauge of interest and pass as
# stationId:str. The default gauge is Liverpool: stationId="E70124"
 # Construct a recent 10 days period and extract these data
date_start = np.datetime64('now')-np.timedelta64(20,'D')
date_end = np.datetime64('now')-np.timedelta64(10,'D')
eg = coast.TIDEGAUGE()
# Extract the data between explicit dates
eg.dataset = eg.read_EA_API_to_xarray(date_start=date_start, date_end=date_end )
eg.plot_timeseries()

# Alternatively extract the data for the last ndays, here for a specific
# (the default) station.
eg.dataset = eg.read_EA_API_to_xarray(ndays=1, stationId="E70124")
eg.plot_timeseries()

#%%  Additionally, alternative data streams can be read in and similarly
# processed. For example the BODC processed data from the UK Tidegauge network.
# Data name: UK Tide Gauge Network, processed data.
# Source: https://www.bodc.ac.uk/

#%% Tide table extrema can be extracted from the timeseries
#        Finds high and low water for a given variable.
#        Returns in a new TIDEGAUGE object with similar data format to
#        a TIDETABLE.
# There are two methods for extracting extrema. A neightbour comparison method, 
# (method="comp") and a cubic spline fitting method (method="cubic")

# Load and plot BODC processed data
fn_bodc = 'example_files/tide_gauges/LIV2010.txt'

# Set the start and end dates
date_start = np.datetime64('2020-10-13 20:00')
date_end = np.datetime64('2020-10-13 21:00')

# Initiate a TIDEGAUGE object, if a filename is passed it assumes it is a GESLA
# type object
del tg
tg = coast.TIDEGAUGE()
tg.dataset = tg.read_bodc_to_xarray(fn_bodc, date_start, date_end)

# Use comparison of neighbourhood method (method="comp" is assumed)
extrema_comp = tg.find_high_and_low_water('sea_level', method="comp")

# Use cubic spline fitting method
extrema_cubc = tg.find_high_and_low_water('sea_level', method="cubic")

# Plot to show the difference between maxima find methods for high tide example.
plt.figure()
plt.plot(tg.dataset.time, tg.dataset.sea_level, 'k')
plt.scatter(extrema_comp.dataset.time_highs.values, extrema_comp.dataset.sea_level_highs, marker='o', c='g')
plt.scatter(extrema_cubc.dataset.time_highs.values, extrema_cubc.dataset.sea_level_highs, marker='+', c='g')
plt.xlim([date_start, date_end])
plt.ylim([7.75, 8.0])
plt.legend(['Time Series','Maxima by comparison','Maxima by cubic spline'])
plt.title('Tide Gauge Optima at Gladstone')
plt.show()


