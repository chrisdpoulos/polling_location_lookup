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

# Get api key. Try st.secrets except StreamlitSecretNotFoundError(error_msg)
try:
    if "GM_API_KEY" in st.secrets:
        api_key = st.secrets["GM_API_KEY"]
    else:
        api_key = os.getenv("GM_API_KEY")
except Exception as e:
    api_key = os.getenv("GM_API_KEY")

gmaps = googlemaps.Client(key=api_key)

# Read in kmz file as GeoDataFrame

polling_locations = gpd.read_file("data.geojson",driver="GeoJSON")

polling_locations = gpd.GeoDataFrame(polling_locations,crs="EPSG:4326")
polling_locations = polling_locations.to_crs(epsg=3425)

# Geocoding function

street = st.sidebar.text_input("Enter the street address", "1901 W Carrol Ave")
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

st.markdown(f"<b>You entered the address:</b><br><br>{location[0]}<br><br>", unsafe_allow_html=True)

geocoded = gpd.GeoDataFrame(geocoded,geometry=gpd.points_from_xy(df.Longitude, df.Latitude),crs="EPSG:4326")
geocoded = geocoded.to_crs(epsg=3425)

# Select polling_location in 2 miles of the geocoded location
# Make a distance radio button 1 mile or two mile
buffer_option = st.sidebar.radio("Select the polling location search distance", ("1 mile", "2 miles"))
buffer_distance = 1609.34 if buffer_option == "1 mile" else 2 * 1609.34  # 1 mile or 2 miles in meters
geocoded_buffer = geocoded.buffer(buffer_distance)


polling_locations_nearby = polling_locations[ polling_locations.geometry.within(geocoded_buffer.unary_union) ]

# add distance from geocoded location in miles

polling_locations_nearby['distance_to_location'] = polling_locations_nearby.geometry.distance(geocoded.geometry.iloc[0])/ 1609.34 

# sort by distance to the geocoded location
polling_locations_nearby = polling_locations_nearby.sort_values(by='distance_to_location')

gdf = polling_locations_nearby.copy()

polling_locations_nearby = polling_locations_nearby[['full_address','name','ward_pct','distance_to_location']]
polling_locations_nearby.columns = ['Address','Name','Ward & Precinct','Distance (Miles)']

# Merge Ward & Precinct if polling_locations_nearby['Name'] has duplicates
polling_locations_nearby = polling_locations_nearby.groupby('Name', as_index=False).agg({
    'Address': 'first',
    'Ward & Precinct': ', '.join,
    'Distance (Miles)': 'first'
})

# Format name so first letter of every word is capitalized
polling_locations_nearby['Name'] = polling_locations_nearby['Name'].apply(lambda x: ' '.join([i.capitalize() for i in x.split(' ')]))

# If words like St are used add a period after them
polling_locations_nearby['Name'] = polling_locations_nearby['Name'].apply(lambda x: x.replace('St', ' St.'))

# make Name a link https://www.google.com/maps/search/?api=1&query=ADDRESS where ADDRESS is the 'Address'

polling_locations_nearby['Name'] = polling_locations_nearby.apply(lambda x: f'<a href="https://www.google.com/maps/search/?api=1&query={x["Address"]}" target="_blank">{x["Name"]}</a>', axis=1)

st.markdown(f"""<b>Polling locations within {buffer_option} of the geocoded location:</b>""",unsafe_allow_html=True)

# for each name, display the polling location as a link in bulleted list, sort by distance
polling_locations_nearby = polling_locations_nearby.sort_values(by='Distance (Miles)')


for index, row in polling_locations_nearby.iterrows():
    st.markdown(f"- {row['Name']} ({row['Distance (Miles)']:.2f} miles)- Serves: {row['Ward & Precinct']}", unsafe_allow_html=True)


