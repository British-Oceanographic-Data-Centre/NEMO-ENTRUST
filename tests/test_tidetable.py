# Test with PyTest

import coast
import numpy as np
import xarray as xr
import datetime
import logging
import coast.general_utils as general_utils


#-----------------------------------------------------------------------------#
#%% day of the week function                                           #
#                                                                             #
def test_dayoweek():
    check1 = general_utils.dayoweek( np.datetime64('2020-10-16') ) == 'Fri'
    assert check1
