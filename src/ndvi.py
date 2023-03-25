# Supress Warnings
import warnings
warnings.filterwarnings('ignore')

from tqdm import tqdm

# Import Planetary Computer tools
import pystac_client
import planetary_computer as pc
from odc.stac import stac_load

import pandas as pd

crop_data = pd.read_csv('./data/crop_data.csv')
#crop_data = pd.read_csv('./data/validation_data.csv')

# Define the bbox size
box_size_deg = 0.005 # Surrounding box in degrees

# Define the time window
#time_window="2020-04-01/2020-06-30"
time_window="2020-02-29/2020-03-30"

def get_ndvi():
	ndvi_list = []

	for coordinates in tqdm(crop_data['Latitude and Longitude']):
		latlong = coordinates.replace('(','').replace(')','').replace(' ','').split(',')

		# Calculate the Lat-Lon bounding box region
		min_lon = float(latlong[1])-box_size_deg/2
		min_lat = float(latlong[0])-box_size_deg/2
		max_lon = float(latlong[1])+box_size_deg/2
		max_lat = float(latlong[0])+box_size_deg/2
		bounds = (min_lon, min_lat, max_lon, max_lat)

		# Using the `pystac_client` we can search the Planetary Computer's STAC catalog for items matching our query parameters. The result is the number of scenes matching our search criteria that touch our area of interest. Some of these may be partial scenes and may contain clouds.

		stac = pystac_client.Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
		search = stac.search(collections=["sentinel-2-l2a"], bbox=bounds, datetime=time_window)
		items = list(search.get_all_items())

		# Define the pixel resolution for the final product
		# Define the scale according to our selected crs, so we will use degrees
		resolution = 20  # meters per pixel
		scale = resolution / 111320.0 # degrees per pixel for CRS:4326

		xx = stac_load(
			items,
			bands=["red", "green", "blue", "nir", "SCL"],
			crs="EPSG:4326", # Latitude-Longitude
			resolution=scale, # Degrees
			chunks={"x": 2048, "y": 2048},
			dtype="uint16",
			patch_url=pc.sign,
			bbox=bounds
		)

		# Not filtering water
		cloud_mask = \
			(xx.SCL != 0) & \
			(xx.SCL != 1) & \
			(xx.SCL != 3) & \
			(xx.SCL != 8) & \
			(xx.SCL != 9) & \
			(xx.SCL != 10)

		cleaned_data = xx.where(cloud_mask).astype("uint16")

		mean_clean = cleaned_data.mean(dim=['longitude','latitude']).compute()
		ndvi_mean_clean = (mean_clean.nir-mean_clean.red)/(mean_clean.nir+mean_clean.red)

		ndvi_list.append((coordinates, float(ndvi_mean_clean.mean()), float(ndvi_mean_clean.max()), float(ndvi_mean_clean.min())))

	return ndvi_list

ndvi_list = get_ndvi()

ndvi_list = pd.DataFrame(ndvi_list, columns=['Latitude and Longitude', 'ndvi_mean', 'ndvi_max', 'ndvi_min'])

ndvi_list.to_csv('./data/ndvi.csv', index=False)
