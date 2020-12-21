import os
import unittest
import numpy as np

# Do the read/write functions give the same data afterwards?
# Do the example configs in the repo actually parse through the configparser?
# etc.

from ..netcdf_read_write import read_netcdf4, read_netcdf3, write_netcdf4


class NetCDFTests(unittest.TestCase):

    def test_simple_netcdf3(self):
        # HACK because I can't understand why conda's 3.7 dosen't have importlib.resources
        filename = os.path.join(os.path.dirname(__file__), 'USGS_vel.nc3')
        lon, lat, z = read_netcdf3(filename)
        self.assertTrue(lon.any(), 'Could not read longitude of test file')
        self.assertTrue(lat.any(), 'Could not read latitude of test file')
        self.assertTrue(z.any(), 'Could not read z of test file')

    def test_simple_netcdf4(self):
        filename = os.path.join(os.path.dirname(__file__), 'USGS_vel.nc4')
        lon, lat, z = read_netcdf4(filename)
        self.assertTrue(lon.any(), 'Could not read longitude of test file')
        self.assertTrue(lat.any(), 'Could not read latitude of test file')
        self.assertTrue(z.any(), 'Could not read z of test file')

    def test_read_write_cycle(self):
        relpath_to_testfiles = 'read_write_insar_utilities/test/';
        filename = relpath_to_testfiles+'USGS_vel.nc4';
        new_filename = relpath_to_testfiles + 'written_test.nc';
        lon, lat, z = read_netcdf4(filename);
        write_netcdf4(lon, lat, z, new_filename);
        lon2, lat2, z2 = read_netcdf4(new_filename);
        self.assertTrue(np.allclose(lon, lon2));
        self.assertTrue(np.allclose(lat, lat2));
        self.assertTrue(np.allclose(z, z2));


if __name__ == '__main__':
    unittest.main()
