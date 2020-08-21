# A few functions that help project into and out of LOS
# Mostly trig
# Example: 
# Dlos = [U_n sin(phi) - U_e cos(phi)]*sin(lamda) + U_u cos(lamda)
# [U_e, U_n, U_u] are the east, north, and up components of the deformation. 
# phi   = azimuth of satellite heading vector, positive clockwise from north.
# lamda = local incidence angle at the reflector.
# from Fialko et al., 2001. 

import numpy as np 
import numpy.linalg

def simple_project_ENU_to_LOS(U_e,U_n,U_u,flight_angle,incidence_angle):
	# Dlos = [U_n sin(phi) - U_e cos(phi)]*sin(lamda) + U_u cos(lamda)
	# [U_e, U_n, U_u] are the east, north, and up components of the deformation. 
	# phi   = azimuth of satellite heading vector, positive clockwise from north.
	# lamda = local incidence angle at the reflector (usually angle from the vertical).
	# Fialko 2001
	# Works for single values and for 1D arrays of all arguments

	if np.size(U_e)>1:  # processing a 1D array of values
		if np.size(flight_angle)==1:
			phi = [np.deg2rad(flight_angle) for x in U_e];  # bumping up the flight and incidence angles into 1D arrays
			lamda = [np.deg2rad(incidence_angle) for x in U_e]; # otherwise, we assume they are matched 1D arrays
		else:
			phi = [np.deg2rad(x) for x in flight_angle];  # 1D arrays of angles in radians nows
			lamda= [np.deg2rad(x) for x in incidence_angle];
		d_los = [0*i for i in U_e];
		for i in range(len(U_e)):
			d_los[i] = ( (U_n[i]*np.sin(phi) - U_e[i]*np.cos(phi) )*np.sin(lamda)  + U_u[i]*np.cos(lamda) );
	

	else:               # processing a single value
		phi=np.deg2rad(flight_angle); 
		lamda=np.deg2rad(incidence_angle);
		d_los = (U_n*np.sin(phi) - U_e*np.cos(phi) )*np.sin(lamda)  + U_u*np.cos(lamda) ;

	# Flipping by negative one, because the convention is positive when moving away from the satellite. 
	d_los=np.array(d_los)*-1;

	return d_los

def get_point_enu_interp(reference_point, f_east=None, f_north=None, f_up=None):
	# Useful for reference points, for example
	# reference point is [lon, lat]
	# Interpolated functions are required if the reference isn't located at a gps station. 
	velref_e=f_east(reference_point[0],reference_point[1]);
	velref_n=f_north(reference_point[0],reference_point[1]);
	if f_up is None:
		velref_u=0;
	else:
		velref_u=f_up(reference_point[0], reference_point[1]);
	return velref_e, velref_n, velref_u;

def get_point_enu_veltuple(vel_tuple, reference_point_coords=None, reference_point_name=None, zero_vertical=False):
	# If the reference is co-located with a GPS station, we find it within the tuple.
	# We either use name or lat/lon
	if reference_point_name is not None:
		for i in range(len(vel_tuple.name)):
			if vel_tuple.name[i]==reference_point_name:
				velref_e=vel_tuple.e[i];
				velref_n=vel_tuple.n[i];
				if zero_vertical:
					velref_u=0;
				else:
					velref_u=vel_tuple.u[i];
				reflon=vel_tuple.elon[i];
				reflat=vel_tuple.nlat[i];
		return velref_e, velref_n, velref_u, reflon, reflat;
	else:
		for i in range(len(vel_tuple.elon)):
			if vel_tuple.elon[i]==reference_point[0] and vel_tuple.nlat[i]==reference_point[1]:  # should I make these tolerances? 
				velref_e=vel_tuple.e[i];
				velref_n=vel_tuple.n[i];
				if zero_vertical:
					velref_u=0;
				else:
					velref_u=vel_tuple.u[i];
		return velref_e, velref_n, velref_u;


def look_vector2flight_incidence_angles(lkv_e, lkv_n, lkv_u):
	"""
	I'm so tired of writing these trig functions
	lkv_e, lkv_n, lkv_u are the components of the look vector from ground to satellite
	incidence angle is angle between look vector and vertical in degrees
	Flight angle is clockwise from north in degrees
	"""
	unit_lkv = [lkv_e, lkv_n, lkv_u]
	unit_lkv = unit_lkv / np.linalg.norm(unit_lkv);
	vert_vector = [0, 0, 1]
	dotproduct = np.dot(unit_lkv, vert_vector);
	incidence_angle = np.rad2deg(np.arccos(dotproduct));

	lkv_horiz_angle = np.arctan2(lkv_n, lkv_e);  # the cartesian angle of the horizontal look vector (negative small # for DESC)
	heading_deg = cartesian_to_heading(np.rad2deg(lkv_horiz_angle));
	flight_angle = heading_deg + 90;  # satellite flies 90 degrees away from look vector direction
	return [flight_angle,incidence_angle];

def cartesian_to_heading(cartesian_angle):
	# Take a cartesian angle in degrees (CCW from east)
	# Convert to heading angle in degrees (CW from north)
	return 90 - cartesian_angle;


def misfit_gps_geocoded_insar():
	# A function I'd like to write to calculate the difference between a GNSS velocity field and an InSAR result. 
	return 0;



