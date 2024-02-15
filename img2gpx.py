import os
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import math
import xml.etree.ElementTree as ET

os.system('clear')

source_folder= os.path.expanduser(f"~/Documents/python/727/images/")
gpx_path = os.path.expanduser(f"~/Documents/python/img2gpx/gpx/i727-00.gpx")

# Chemin vers le fichier GPX
def gpx_reader(path):

    with open(path, 'r', encoding='utf-8') as file:
        gpx_file_content = file.read()

    return ET.ElementTree(ET.fromstring(gpx_file_content))

def haversine_distance(lat1, lon1, lat2, lon2):
    earth_radius = 6371000

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(delta_lon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = earth_radius * c

    return distance

def calculate_distance(gpx_tree, latitude, longitude):
    distance = float('inf')

    for trkpt in gpx_tree.iter(tag='{http://www.topografix.com/GPX/1/1}trkpt'):
        point_latitude = float(trkpt.get('lat'))
        point_longitude = float(trkpt.get('lon'))

        # print(f"{point_latitude} {point_longitude} {latitude} {longitude}")

        current_distance = haversine_distance(point_latitude, point_longitude, latitude, longitude)

        if current_distance < distance:
            distance = current_distance

    return round(distance)

def get_exif_data(image_path):
    image = Image.open(image_path)
    exif_data = {}
    
    if hasattr(image, '_getexif'):
        exif_info = image._getexif()
        if exif_info is not None:
            for tag, value in exif_info.items():
                decoded = TAGS.get(tag, tag)
                exif_data[decoded] = value

    return exif_data

def get_geotagging(exif_data):
    if 'GPSInfo' in exif_data:
        gps_info = exif_data['GPSInfo']
        
        geotagging = {}
        for tag in gps_info.keys():
            decoded = GPSTAGS.get(tag, tag)
            geotagging[decoded] = gps_info[tag]

        return geotagging
    return None

def convert_to_degrees(value):
    """ Convertit une valeur DMS EXIF en degrés décimaux """
    # Convertit chaque valeur IFDRational en un nombre décimal
    d, m, s = value
    return round(float(d) + float(m) / 60 + float(s) / 3600,5)

def get_decimal_coords(geotags):
    lat = convert_to_degrees(geotags['GPSLatitude'])
    lon = convert_to_degrees(geotags['GPSLongitude'])

    if geotags['GPSLatitudeRef'] != 'N':
        lat = -lat
    if geotags['GPSLongitudeRef'] != 'E':
        lon = -lon

    return (lat, lon)


def process_img(folder):
    
    images = []

    # Parcours du dossier source pour copier les images
    for root, _, files in os.walk(folder):
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                source_path = os.path.join(root, filename)

                exif_data = get_exif_data(source_path)
                geotags = get_geotagging(exif_data)
                # exif_date = exif_data.get('DateTime')

                coords = ("", "")
                if geotags is not None:
                    coords = get_decimal_coords(geotags)
                else:
                    continue
                
                dic = {
                    "path" : source_path, 
                    "coords" : coords,
                    "metters" : 0
                }

                images.append(dic)

    return images


images = process_img(source_folder)
gpx_tree = gpx_reader(gpx_path)

nb_photo = 0
for image in images:
    (lat, lon) = image['coords']
    distance = calculate_distance(gpx_tree, lat, lon)
    if distance<100:
        nb_photo = nb_photo + 1
        print(nb_photo, distance)
    # exit()