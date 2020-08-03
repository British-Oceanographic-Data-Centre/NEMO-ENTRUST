from .COAsT import COAsT
import xarray as xr
import numpy as np
# from dask import delayed, compute, visualize
# import graphviz
import matplotlib.pyplot as plt

class NEMO(COAsT):
    """
    Words to describe the NEMO class

    kwargs -- define addition keyworded arguemts for domain file. E.g. ln_sco=1
    if using s-scoord in an old domain file that does not carry this flag.
    """
    def __init__(self, fn_data=None, fn_domain=None, grid_ref='t-grid',
                 chunks: dict=None, multiple=False,
                 workers=2, threads=2, memory_limit_per_worker='2GB', **kwargs):
        self.dataset = xr.Dataset()
        self.grid_ref = grid_ref.lower()
        self.domain_loaded = False

        self.set_dimension_mapping()
        self.set_variable_mapping()
        if fn_data is not None:
            self.load(fn_data, chunks, multiple)
        self.set_dimension_names(self.dim_mapping)
        self.set_variable_names(self.var_mapping)

        if fn_domain is None:
            self.filename_domain = "" # empty store for domain fileanme
            pass
            #print("No NEMO domain specified, only limited functionality"+
            #      " will be available")
        else:
            self.filename_domain = fn_domain # store domain fileanme
            dataset_domain = self.load_domain(fn_domain, chunks)

            # Define extra domain attributes using kwargs dictionary
            ## This is a bit of a placeholder. Some domain/nemo files will have missing variables
            for key,value in kwargs.items():
                dataset_domain[key] = value

            if fn_data is not None:
                dataset_domain = self.trim_domain_size( dataset_domain )
            self.set_timezero_depths(dataset_domain) # THIS ADDS TO dataset_domain. Should it be 'return'ed (as in trim_domain_size) or is implicit OK?
            self.merge_domain_into_dataset(dataset_domain)

    def set_dimension_mapping(self):
        self.dim_mapping = {'time_counter':'t_dim', 'deptht':'z_dim',
                            'depthu':'z_dim', 'depthv':'z_dim',
                            'y':'y_dim', 'x':'x_dim'}
        self.dim_mapping_domain = {'t':'t_dim0', 'x':'x_dim', 'y':'y_dim',
                                   'z':'z_dim'}


    def set_variable_mapping(self):
        # Variable names remapped  within NEMO object
        self.var_mapping = {'time_counter':'time',
                            'votemper' : 'temperature',
                            'thetao' : 'temperature',
                            'temp' : 'temperature',
                            'so' : 'salinity'}
        # Variable names mapped from domain to NEMO object
        # NAMES NOT SET IN STONE.
        self.var_mapping_domain = {'time_counter' : 'time0',
                                   'glamt':'longitude', 'glamu':'longitude',
                                   'glamv':'longitude','glamf':'longitude',
                                   'gphit':'latitude', 'gphiu':'latitude',
                                   'gphiv':'latitude', 'gphif':'latitude',
                                   'e1t':'e1', 'e1u':'e1',
                                   'e1v':'e1', 'e1f':'e1',
                                   'e2t':'e2', 'e2u':'e2',
                                   'e2v':'e2', 'e2f':'e2',
                                   'ff_t':'ff', 'ff_f':'ff',
                                   'e3t_0':'e3_0', 'e3w_0':'e3_0',
                                   'e3u_0':'e3_0', 'e3v_0':'e3_0',
                                   'e3f_0':'e3_0',
                                   'tmask':'mask',
                                   'depthf_0':'depth_0',
                                   'depthu_0':'depth_0', 'depthv_0':'depth_0',
                                   'depthw_0':'depth_0', 'deptht_0':'depth_0'}

    def load_domain(self, fn_domain, chunks):
        ''' Loads domain file and renames dimensions with dim_mapping_domain'''
        # Load xarrat dataset
        dataset_domain = xr.open_dataset(fn_domain)
        self.domain_loaded = True
        # Rename dimensions
        for key, value in self.dim_mapping_domain.items():
            try:
                dataset_domain = dataset_domain.rename_dims({ key : value })
            except:
                print('pass: {}: {}', key, value)
                pass

        return dataset_domain

    def merge_domain_into_dataset(self, dataset_domain):
        ''' Merge domain dataset variables into self.dataset, using grid_ref'''
        # Define grid independent variables to pull across
        not_grid_vars = ['jpiglo', 'jpjglo','jpkglo','jperio',
                         'ln_zco', 'ln_zps', 'ln_sco', 'ln_isfcav']

        # Define grid specific variables to pull across
        if self.grid_ref == 'u-grid':
            grid_vars = ['glamu', 'gphiu', 'e1u', 'e2u', 'e3u_0', 'depthu_0'] #What about e3vw
        elif self.grid_ref == 'v-grid':
            grid_vars = ['glamv', 'gphiv', 'e1v', 'e2v', 'e3v_0', 'depthv_0']
        elif self.grid_ref == 't-grid':
            grid_vars = ['glamt', 'gphit', 'e1t', 'e2t', 'e3t_0', 'deptht_0', 'tmask']
        elif self.grid_ref == 'w-grid':
            grid_vars = ['glamt', 'gphit', 'e1t', 'e2t', 'e3w_0', 'depthw_0']
        elif self.grid_ref == 'f-grid':
            grid_vars = ['glamf', 'gphif', 'e1f', 'e2f', 'e3f_0', 'depthf_0']

        all_vars = grid_vars + not_grid_vars

        # Trim domain DataArray area if necessary.
        self.copy_domain_vars_to_dataset( dataset_domain, grid_vars )

        # Reset & set specified coordinates
        coord_vars = ['longitude', 'latitude', 'time', 'depth_0']
        self.dataset = self.dataset.reset_coords()
        for var in coord_vars:
            try:
                self.dataset = self.dataset.set_coords(var)
            except:
                pass

        # Delete specified variables
        # MIGHT NEEWD TO DELETE OTHEHR DEPTH VARS ON OTHER GRIDS?
        delete_vars = ['nav_lat', 'nav_lon', 'deptht']
        for var in delete_vars:
            try:
                self.dataset = self.dataset.drop(var)
            except:
                pass


    def __getitem__(self, name: str):
        return self.dataset[name]

    def set_grid_ref_attr(self):
        self.grid_ref_attr_mapping = {'temperature' : 't-grid',
                                'coast_name_for_u_velocity' : 'u-grid',
                                'coast_name_for_v_velocity' : 'v-grid',
                                'coast_name_for_w_velocity' : 'w-grid',
                                'coast_name_for_vorticity'  : 'f-grid' }
        #self.grid_ref_attr_mapping = None

    def get_contour_complex(self, var, points_x, points_y, points_z, tolerance: int = 0.2):
        smaller = self.dataset[var].sel(z=points_z, x=points_x, y=points_y, method='nearest', tolerance=tolerance)
        return smaller

    def set_timezero_depths(self, dataset_domain):

        """
        Calculates the depths at time zero (from the domain_cfg input file)
        for the appropriate grid.

        The depths are assigned to domain_dataset.depth_0

        """

        try:
            if self.grid_ref == 't-grid':
                e3w_0 = np.squeeze( dataset_domain.e3w_0.values )
                depth_0 = np.zeros_like( e3w_0 )
                depth_0[0,:,:] = 0.5 * e3w_0[0,:,:]
                depth_0[1:,:,:] = depth_0[0,:,:] + np.cumsum( e3w_0[1:,:,:], axis=0 )
            elif self.grid_ref == 'w-grid':
                e3t_0 = np.squeeze( dataset_domain.e3t_0.values )
                depth_0 = np.zeros_like( e3t_0 )
                depth_0[0,:,:] = 0.0
                depth_0[1:,:,:] = np.cumsum( e3t_0, axis=0 )[:-1,:,:]
            elif self.grid_ref == 'u-grid':
                e3w_0 = dataset_domain.e3w_0.values.squeeze()
                e3w_0_on_u = 0.5 * ( e3w_0[:,:,:-1] + e3w_0[:,:,1:] )
                depth_0 = np.zeros_like( e3w_0 )
                depth_0[0,:,:-1] = 0.5 * e3w_0_on_u[0,:,:]
                depth_0[1:,:,:-1] = depth_0[0,:,:-1] + np.cumsum( e3w_0_on_u[1:,:,:], axis=0 )
            elif self.grid_ref == 'v-grid':
                e3w_0 = dataset_domain.e3w_0.values.squeeze()
                e3w_0_on_v = 0.5 * ( e3w_0[:,:-1,:] + e3w_0[:,1:,:] )
                depth_0 = np.zeros_like( e3w_0 )
                depth_0[0,:-1,:] = 0.5 * e3w_0_on_v[0,:,:]
                depth_0[1:,:-1,:] = depth_0[0,:-1,:] + np.cumsum( e3w_0_on_v[1:,:,:], axis=0 )
            elif self.grid_ref == 'f-grid':
                e3w_0 = dataset_domain.e3w_0.values.squeeze()
                e3w_0_on_f = 0.25 * ( e3w_0[:,:-1,:-1] + e3w_0[:,1:,:-1] +
                                     e3w_0[:,:-1,:-1] + e3w_0[:,:-1,1:] )
                depth_0 = np.zeros_like( e3w_0 )
                depth_0[0,:-1,:-1] = 0.5 * e3w_0_on_f[0,:,:]
                depth_0[1:,:-1,:-1] = depth_0[0,:-1,:-1] + np.cumsum( e3w_0_on_f[1:,:,:], axis=0 )
            else:
                raise ValueError(str(self) + ": " + self.grid_ref + " depth calculation not implemented")
            # Write the depth_0 variable to the domain_dataset DataSet, with grid type
            dataset_domain[f"depth{self.grid_ref.replace('-grid','')}_0"] = xr.DataArray(depth_0,
                    dims=['z_dim', 'y_dim', 'x_dim'],
                    attrs={'units':'m',
                    'standard_name': 'Depth at time zero on the {}'.format(self.grid_ref)})
        except ValueError as err:
            print(err)

        return

    # Add subset method to NEMO class
    def subset_indices(self, start: tuple, end: tuple) -> tuple:
        """
        based on transect_indices, this method looks to return all indices between the given points.
        This results in a 'box' (Quadrilateral) of indices.
        consequently the returned lists may have different lengths.
        :param start: A lat/lon pair
        :param end: A lat/lon pair
        :return: list of y indices, list of x indices,
        """

        [j1, i1] = self.find_j_i(start[0], start[1])  # lat , lon
        [j2, i2] = self.find_j_i(end[0], end[1])  # lat , lon

        return list(np.arange(j1, j2+1)), list(np.arange(i1, i2+1))

    def find_j_i(self, lat: float, lon: float):
        """
        A routine to find the nearest y x coordinates for a given latitude and longitude
        Usage: [y,x] = find_j_i(49, -12)

        :param lat: latitude
        :param lon: longitude
        :return: the y and x coordinates for the NEMO object's grid_ref, i.e. t,u,v,f,w.
        """

        dist2 = xr.ufuncs.square(self.dataset.latitude - lat) + xr.ufuncs.square(self.dataset.longitude - lon)
        [y, x] = np.unravel_index(dist2.argmin(), dist2.shape)
        return [y, x]

    def find_j_i_domain(self, lat: float, lon: float, dataset_domain: xr.DataArray):
        """
        A routine to find the nearest y x coordinates for a given latitude and longitude
        Usage: [y,x] = find_j_i(49, -12, dataset_domain)

        :param lat: latitude
        :param lon: longitude
        :param grid_ref: the gphi/glam version a user wishes to search over
        :return: the y and x coordinates for the given grid_ref variable within the domain file
        """

        internal_lat = dataset_domain[f"gphi{self.grid_ref.replace('-grid','')}"]
        internal_lon = dataset_domain[f"glam{self.grid_ref.replace('-grid','')}"]
        dist2 = xr.ufuncs.square(internal_lat - lat) \
                + xr.ufuncs.square(internal_lon - lon)
        [_, y, x] = np.unravel_index(dist2.argmin(), dist2.shape)
        return [y, x]

    def transect_indices(self, start: tuple, end: tuple) -> tuple:
        """
        This method returns the indices of a simple straight line transect between two
        lat lon points defined on the NEMO object's grid_ref, i.e. t,u,v,f,w.

        :type start: tuple A lat/lon pair
        :type end: tuple A lat/lon pair
        :return: array of y indices, array of x indices, number of indices in transect
        """

        [j1, i1] = self.find_j_i(start[0], start[1])  # lat , lon
        [j2, i2] = self.find_j_i(end[0], end[1])  # lat , lon

        line_length = max(np.abs(j2 - j1), np.abs(i2 - i1)) + 1

        jj1 = [int(jj) for jj in np.round(np.linspace(j1, j2, num=line_length))]
        ii1 = [int(ii) for ii in np.round(np.linspace(i1, i2, num=line_length))]

        return jj1, ii1, line_length


    def trim_domain_size( self, dataset_domain ):
        """
        Trim the domain variables if the dataset object is a spatial subset
        """
        if (self.dataset['x_dim'].size != dataset_domain['x_dim'].size)  \
                or (self.dataset['y_dim'].size != dataset_domain['y_dim'].size):
            print('The domain  and dataset objects are different sizes:', \
                  ' [{},{}] cf [{},{}]. Trim domain.'.format(
                  dataset_domain['x_dim'].size, dataset_domain['y_dim'].size,
                  self.dataset['x_dim'].size, self.dataset['y_dim'].size ))

            # Find the corners of the cut out domain.
            [j0,i0] = self.find_j_i_domain( self.dataset.nav_lat[0,0],
                                    self.dataset.nav_lon[0,0], dataset_domain )
            [j1,i1] = self.find_j_i_domain( self.dataset.nav_lat[-1,-1],
                                    self.dataset.nav_lon[-1,-1], dataset_domain )

            dataset_subdomain = dataset_domain.isel(
                                        y_dim = slice(j0, j1 + 1),
                                        x_dim = slice(i0, i1 + 1) )
            return dataset_subdomain
        else:
            return dataset_domain

    def copy_domain_vars_to_dataset( self, dataset_domain, grid_vars ):
        """
        Map the domain coordand metric variables to the dataset object.
        Expects the source and target DataArrays to be same sizes.
        """
        for var in grid_vars:
            try:
                new_name = self.var_mapping_domain[var]
                self.dataset[new_name] = dataset_domain[var].squeeze()
                #print("map: {} --> {}".format( var, new_name))
            except:
                pass

    def differentiate(self, in_varstr, dim='z_dim', out_varstr=None, out_obj=None):
        """
        Derivatives are computed in x_dim, y_dim, z_dim (or i,j,k) directions
        wrt lambda, phi, or z coordinates (with scale factor in metres not degrees).

        Derivatives are calculated using the approach adopted in NEMO,
        specifically using the 1st order accurate central difference
        approximation. For reference see section 3.1.2 (sec. Discrete operators)
        of the NEMO v4 Handbook.

        Currently the method does not accomodate all possible eventualities. It
        covers:
        1) d(grid_t)/dz --> grid_w
        
        Returns  an object (with the appropriate target grid_ref) containing
        derivative (out_varstr) as xr.DataArray
        
        This is hardwired to expect:
        1) depth_0 and e3_0 fields exist
        2) xr.DataArrays are 4D
        3) self.filename_domain if out_obj not specified
        
        Example usage:
        --------------
        # Initialise DataArrays
        nemo_t = coast.NEMO( fn_data, fn_domain, grid_ref='t-grid' )
        # Compute dT/dz
        nemo_w_1 = nemo_t.differentiate( 'temperature', dim='z_dim' )
        
        # For f(z)=-z. Compute df/dz = -1. Surface value is set to zero
        nemo_t.dataset['depth4D'],_ = xr.broadcast( nemo_t.dataset['depth_0'], nemo_t.dataset['temperature'] )
        nemo_w_4 = nemo_t.differentiate( 'depth4D', dim='z_dim', out_varstr='dzdz' )
        
        Provide an existing target NEMO object and target variable name:
        nemo_w_1 = nemo_t.differentiate( 'temperature', dim='z_dim', out_varstr='dTdz', out_obj=nemo_w_1 )
        
        
        Parameters
        ----------
        in_varstr : str, name of variable to differentiate
        dim : str, dimension to operate over. E.g. {'z_dim', 'y_dim', 'x_dim', 't_dim'}
        out_varstr : str, (optional) name of the target xr.DataArray
        out_obj : exiting NEMO obj to store xr.DataArray (optional)

        """
        #import xarray as xr

        new_units = ""

        # Check in_varstr exists in self.
        if hasattr( self.dataset, in_varstr ):
            # self.dataset[in_varstr] exists

            var = self.dataset[in_varstr] # for convenience

            nt = var.sizes['t_dim']
            nz = var.sizes['z_dim']
            ny = var.sizes['y_dim']
            nx = var.sizes['x_dim']

            ## Compute d(t_grid)/dz --> w-grid
            # Check grid_ref and dir. Determine target grid_ref.
            if (self.grid_ref == 't-grid') and (dim == 'z_dim'):
                out_grid = 'w-grid'

                # If out_obj exists check grid_ref, else create out_obj.
                if (out_obj is None) or (out_obj.grid_ref != out_grid):
                    try:
                        out_obj = NEMO( fn_domain=self.filename_domain, grid_ref=out_grid )
                    except:
                        print('Failed to create target NEMO obj. Perhaps self.',
                                'filename_domain={} is empty?'
                                .format(self.filename_domain))
                    #print('make new target object (out_obj)')

                # Check is out_varstr is defined, else create it
                if out_varstr is None:
                    out_varstr = 'd' + in_varstr + '_dz'
                    #print('make new target variable name: out_str = {}'\
                    #      .format(out_varstr))

                # Create new DataArray with the same dimensions as the parent
                # Crucially have a coordinate value that is appropriate to the target location.
                blank = xr.zeros_like( var.isel(z_dim=[0]) ) # Using "z_dim=[0]" as a list preserves z-dimension
                blank.coords['depth_0'] -= blank.coords['depth_0'] # reset coord vals to zero
                # Add blank slice to the 'surface'. Concat over the 'dim' coords
                diff = xr.concat([blank, var.diff(dim)], dim)
                diff_ndim, e3w_ndim = xr.broadcast( diff, out_obj.dataset.e3_0.squeeze() )
                # Compute the derivative
                out_obj.dataset[out_varstr] = - diff_ndim / e3w_ndim

                # Assign attributes
                new_units = var.units+'/'+ out_obj.dataset.depth_0.units
                # Convert to a xr.DataArray and return
                out_obj.dataset[out_varstr].attrs = {
                                           'units': new_units,
                                           'standard_name': out_varstr}

                # Return in object.
                return out_obj

            else:
                print('Not ready for that combination of grid ({}) and ',\
                'derivative ({})'.format(self.grid_ref, dim))
                return None
        else:
            print('{} does not exist in self.dataset'.format(in_varstr))
            return None
