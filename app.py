# Geocoder app test

# 

import streamlit as st
from shapely.geometry import Point, Polygon
import geopandas as gpd
import pandas as pd
import geopy
import pandas as pd
import geopandas as gpd
import googlemaps
import os

st.set_page_config(page_title=None, page_icon=None, layout="centered", initial_sidebar_state="expanded", menu_items=None)

# Initialize Google Maps client with API key using st.secrets

api_key = st.secrets["GM_API_KEY"]

gmaps = googlemaps.Client(key=api_key)

# Read in kmz file as GeoDataFrame

polling_locations = gpd.read_file("data.geojson",driver="GeoJSON")

polling_locations = gpd.GeoDataFrame(polling_locations,crs="EPSG:4326")

# Geocoding function

street = st.sidebar.text_input("Enter the Street address", "1901 W Carrol Ave")
city = "Chicago"
state = "Illinois"
country = "USA"

location = [street+", "+city+", "+state+", "+country]

def geocode(add):
    try:
        g = gmaps.geocode(add)
        lat = g[0]["geometry"]["location"]["lat"]
        lng = g[0]["geometry"]["location"]["lng"]
        return (lat, lng)
    except:
        return (None)

address = [location]

geocoded = pd.Series(address).apply(geocode)
print(geocoded)

lat = geocoded[0][0]
long = geocoded[0][1]

map_data = pd.DataFrame({'lat': [lat], 'lon': [long]})

df = pd.DataFrame({
    "Latitude":[lat],
    "Longitude":[long]
})

st.markdown(f"<b>You entered the address: </b><br><br>{location[0]}", unsafe_allow_html=True)

geocoded = gpd.GeoDataFrame(geocoded,geometry=gpd.points_from_xy(df.Longitude, df.Latitude),crs="EPSG:4326")

# Select polling_location in 2 miles of the geocoded location
# Make a distance radio button 1 mile or two mile
buffer_option = st.sidebar.radio("Select the polling location search distance", ("1 mile", "2 miles"))
buffer_distance = 1609.34 if buffer_option == "1 mile" else 2 * 1609.34  # 1 mile or 2 miles in meters
geocoded_buffer = geocoded.to_crs(epsg=3857).buffer(buffer_distance)
geocoded_buffer = geocoded_buffer.to_crs(epsg=4326)

polling_locations_nearby = polling_locations[ polling_locations.geometry.within(geocoded_buffer.unary_union) ]

gdf = polling_locations_nearby.copy()

polling_locations_nearby = polling_locations_nearby[['full_address','name','ward_pct']]
polling_locations_nearby.columns = ['Address','Name','Ward & Precinct']

st.markdown(f"""<b>Polling locations within {buffer_option} of the geocoded location:</b><br><sub>Duplicate occur when polling location serves multiple precincts</sub>""",unsafe_allow_html=True)
st.dataframe(polling_locations_nearby,hide_index=True)


