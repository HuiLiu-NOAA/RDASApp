from netCDF4 import Dataset
import pdb
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.geodesic
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
import numpy as np
import colormap
import time
import sys, os
import shapely.geometry
import warnings
from scipy.spatial.distance import cdist

warnings.filterwarnings('ignore')

############ USER INPUT ##########################################################
plot_var = "Increment"
lev = 65               # 65=sfc; 1=toa
clevmax_incr = 0.1     # max contour level for colorbar increment plots
decimals = 4            # number of decimals to round for text boxes
plot_box_width = 5.     # define size of plot domain (units: lat/lon degrees)
singleob_type = "MSONET"
variable = "airTemperature"
if variable == "airTemperature":
    obtype = 't'
    offset = -273.15

# JEDI data
datapath = "./"
jgrid = f"{datapath}/Data/bkg/grid_spec.nc"
janalysis = f"{datapath}/ens3dvar-fv3_lam-C775.fv_core.res.nc" #Ens3dvar-fv3_lam-C775.fv_core.res.nc"
jbackgrnd = f"{datapath}/Data/bkg/20240527.000000.fv_core.res.tile1.nc"
jdiag = f"{datapath}/jdiag_{singleob_type}_2024052700.nc4"

###################################################################################
# Set cartopy shapefile path
platform = os.getenv('HOSTNAME').upper()
if 'ORION' in platform:
        cartopy.config['data_dir']='/work/noaa/fv3-cam/sdegelia/cartopy'
elif 'H' in platform: # Will need to improve this once Hercules is supported
        cartopy.config['data_dir']='/home/Donald.E.Lippi/cartopy'

print(f"{jdiag}")
# Do a quick omf and hofx value check from GSI diag file

# FROM JEDI diag
jncdiag = Dataset(jdiag, mode='r')
oberr_input = jncdiag.groups["EffectiveError0"].variables[f"{variable}"][:][0]
oberr_final = jncdiag.groups["EffectiveError2"].variables[f"{variable}"][:][0]
ob = jncdiag.groups["ObsValue"].variables[f"{variable}"][:][0] + offset
omf= jncdiag.groups["ombg"].variables[f"{variable}"][:][0]
fmo= -1*omf
hofx= fmo+ob

oberr_input = np.around(oberr_input.astype(np.float64), decimals)
oberr_final = np.around(oberr_final.astype(np.float64), decimals)
job = np.around(ob.astype(np.float64), decimals)
jomf = np.around(omf.astype(np.float64), decimals)
jhofx = np.around(hofx.astype(np.float64), decimals)
print(f"JEDI:")
print(f"  oberr_input: {oberr_input}")
print(f"  oberr_final: {oberr_final}")
subtitle1_hofx = f"  ob:   {job}\n  omf:  {jomf}\n  hofx: {jhofx}\n  oberr_final: {oberr_final}\n"
print(subtitle1_hofx)

# Grab single ob lat/lon and double check they're the same.
joblat = jncdiag.groups["MetaData"].variables["latitude"][:][0]
joblon = jncdiag.groups["MetaData"].variables["longitude"][:][0]

joblat = np.around(joblat.astype(np.float64), decimals)
joblon = np.around(joblon.astype(np.float64), decimals)

singleob_lat = joblat
singleob_lon = np.around(joblon - 360., decimals)  # convert to E-W

print(f"Using:")
print(f"  singleob_lat: {singleob_lat}")
print(f"  singleob_lon: {singleob_lon}\n")

print(f"Creating {plot_var} Plot...\n")
lev = lev - 1

# JEDI ####################################
nc_g = Dataset(jgrid, mode='r')
lats = nc_g.variables["grid_latt"][:,:]
lons = nc_g.variables["grid_lont"][:,:]
#lons = lons[:,:] - 180

# Open NETCDF4 dataset for reading
nc_a = Dataset(janalysis, mode='r')
nc_b = Dataset(jbackgrnd, mode='r')

# Read data and get dimensions
jedi_a = nc_a.variables["T"][0,lev,:,:].astype(np.float64)
jedi_b = nc_b.variables["T"][0,lev,:,:].astype(np.float64)

# compute increment
jedi_inc = jedi_a - jedi_b

if plot_var == "Increment":
    title1 = "JEDI"
    jedi = jedi_inc
    clevmax = clevmax_incr

# CREATE PLOT ##############################
fig = plt.figure(figsize=(3,3))
m1 = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree(central_longitude=0))

# Determine extent for plot domain
half = plot_box_width / 2.
left = singleob_lon - half
right = singleob_lon + half
bot = singleob_lat - half
top = singleob_lat + half

# Set extent for both plots
domain="single_ob"
m1.set_extent([left, right, top, bot])

# Add features to the subplots
m1.add_feature(cfeature.GSHHSFeature(scale='low'))

m1.add_feature(cfeature.COASTLINE)

m1.add_feature(cfeature.BORDERS)

m1.add_feature(cfeature.STATES)

#m.add_feature(cfeature.OCEAN)
#m.add_feature(cfeature.LAND)
#m.add_feature(cfeature.LAKES)

# Gridlines for the subplots
gl1 = m1.gridlines(crs = ccrs.PlateCarree(), draw_labels = True, linewidth = 0.5, color = 'k', alpha = 0.25, linestyle = '-')

gl1.xlocator = mticker.FixedLocator([])

gl1.xlocator = mticker.FixedLocator(np.arange(-180., 181., 5.))

gl1.ylocator = mticker.FixedLocator(np.arange(-80., 91., 5.))

gl1.xformatter = LONGITUDE_FORMATTER

gl1.yformatter = LATITUDE_FORMATTER

gl1.xlabel_style = {'size': 5, 'color': 'gray'}

gl1.ylabel_style = {'size': 5, 'color': 'gray'}


def plot_T_inc(var_n, clevmax):
    """Temperature increment/diff [K]"""
    longname = "airTemperature"
    units="K"
    inc = 0.05*clevmax
    clevs = np.arange(-1.0*clevmax, 1.0*clevmax+inc, inc)
    cm = colormap.diff_colormap(clevs)
    return(clevs, cm, units, longname)

# Plot the data
if variable == "airTemperature":
    clevs, cm, units, longname = plot_T_inc(jedi_inc, clevmax)

units="K"
c1 = m1.contourf(lons, lats, jedi, clevs, cmap = cm)

# Scatter the single ob location
m1.scatter(singleob_lon, singleob_lat, color='g', marker='o', s=2)

# Add colorbar
cbar1 = fig.colorbar(c1, orientation="horizontal", fraction=0.046, pad=0.07)

cbar1.set_label(units, size=8)

cbar1.ax.tick_params(labelsize=5, rotation=30)

# Add titles, text, and save the figure
plt.suptitle(f"Temperature {plot_var} at Level: {lev+1}\nobtype: {longname}", fontsize = 9, y = 1.05)

m1.set_title(f"{title1}", fontsize = 9, y = 0.98)

subtitle1_minmax = f"min: {np.around(np.min(jedi), decimals)}\nmax: {np.around(np.max(jedi), decimals)}"
m1.text(left, top, f"{subtitle1_minmax}", fontsize = 6, ha='left', va='bottom')

m1.text(left, bot, f"{subtitle1_hofx}", fontsize = 6, ha='left', va='bottom')

if plot_var == "Increment":
    plt.savefig(f"./increment_{variable}.png", dpi=250, bbox_inches='tight')

# Print some final stats
print(f"Stats:")
print(f" {title1} max: {np.around(np.max(jedi), decimals)}")
print(f" {title1} min: {np.around(np.min(jedi), decimals)}")
