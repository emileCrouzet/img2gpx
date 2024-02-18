# pip install gpxpy
# pip install python-dotenv

import os
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import xml.etree.ElementTree as ET
import pickle
import gpxpy
import gpxpy.gpx
from dotenv import load_dotenv
load_dotenv()

os.system('clear')

images_folder = os.path.expanduser(os.environ["IMG_FOLER"])
gpx_path = "gpx/i727-00.gpx"
distance_filter = 100 #Ignorer image plus loin de la trace

# Initit exif cache
def init_cache():
    global cache, cache_file

    cache_file = os.path.expanduser("_exif_cache.pkl")

    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as fichier_cache:
            cache = pickle.load(fichier_cache)
    else:
        cache = {}

def save_cache():
    global cache, cache_file

    with open(cache_file, 'wb') as fichier_cache:
        pickle.dump(cache, fichier_cache)

# Lecture du fichier GPX
def gpx_reader(path):

    with open(path, 'r') as fichier:
        gpx = gpxpy.parse(fichier)
        return gpx


def gpx_meters(gpx):
    
    gpx_meters = []    
    km = 0
    prev_point = None

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                #print(point.latitude, point.longitude,point.elevation)
                if prev_point:
                    km += point.distance_3d(prev_point)
                prev_point = point
                gpx_meters.append(km)
    return gpx_meters


def calculate_distance(gpx, meters, latitude, longitude):
    
    photo_point = gpxpy.gpx.GPXTrackPoint(latitude, longitude, 0)
    distance = float('inf') #valeur infinie positive
    i = 0
    from_start = 0

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                
                current_distance = point.distance_2d(photo_point)

                if current_distance < distance:
                    distance = current_distance
                    from_start = meters[i]

                i += 1

    return (round(distance), round(from_start))


def get_exif_data(image_path):
    global cache

    if image_path in cache:
        return cache[image_path]

    image = Image.open(image_path)
    exif_data = {}
    
    if hasattr(image, '_getexif'):
        exif_info = image._getexif()
        if exif_info is not None:
            for tag, value in exif_info.items():
                decoded = TAGS.get(tag, tag)
                #print(decoded,value)
                exif_data[decoded] = value

    cache[image_path] = exif_data
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


def process_img(folder, gpx, meters):
    global cache, distance_filter
    init_cache()

    images = []

    # Parcours du dossier source pour copier les images
    for root, _, files in os.walk(folder):
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                source_path = os.path.join(root, filename)

                exif_data = get_exif_data(source_path)
                geotags = get_geotagging(exif_data)
 
                if geotags is not None:
                    (lat, lon) = get_decimal_coords(geotags)
                    (distance,from_start) = calculate_distance(gpx, meters, lat, lon)
                    datetime = exif_data['DateTime']

                    if distance>distance_filter:
                        continue

                else:
                    continue
                
                dic = {
                    "path" : source_path, 
                    "latitude" : lat,
                    "longitude" : lon,
                    "distance" : distance,
                    "meters" : from_start,
                    "datetime": datetime
                }

                images.append(dic)

    save_cache()
    return images


gpx = gpx_reader(gpx_path)
meters = gpx_meters(gpx)
images = process_img(images_folder, gpx, meters)
images = sorted(images, key=lambda dico: dico["meters"])

nb_photo = 0
for image in images:
    print(image)
    exit()

        