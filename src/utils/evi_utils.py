import ee
import geemap
from datetime import datetime, timedelta
#-------------------------------------------------------------------------------------------------------------------
def generate_evi(bbox, start_date, end_date, cloud_cover=80):
    """
    Generate an Enhanced Vegetation Index (EVI) for a given bbox and time period.

    Parameters:
        bbox (ee.Geometry): The bbox of interest.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
        cloud_cover (int): Maximum cloud cover percentage (default: 80).

    Returns:
        ee.ImageCollection: Image collection with EVI and NDVI bands.
    """
    # Load Landsat 8 SR dataset
    landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(bbox) \
        .filterDate(start_date, end_date) \
        .filterMetadata('CLOUD_COVER', 'less_than', cloud_cover)
    
    # Function to scale Landsat bands
    def scaling_ls(img):
        optical = img.select('SR_B.').multiply(0.0000275).add(-0.2)
        thermal = img.select('ST_B.*').multiply(0.00341802).add(149.0)
        return img.addBands(optical, None, True).addBands(thermal, None, True)
    
    # Function to mask clouds
    def mask_clouds(img):
        cloud_shadow_bit_mask = (1 << 4)
        clouds_bit_mask = (1 << 3)
        clouds_cirrus_bit_mask = (1 << 2)
        clouds_dilated_bit_mask = (1 << 1)
        qa = img.select('QA_PIXEL')
        mask = qa.bitwiseAnd(cloud_shadow_bit_mask).eq(0) \
                .And(qa.bitwiseAnd(clouds_bit_mask).eq(0)) \
                .And(qa.bitwiseAnd(clouds_cirrus_bit_mask).eq(0)) \
                .And(qa.bitwiseAnd(clouds_dilated_bit_mask).eq(0))
        return img.updateMask(mask)
    
    # Function to calculate NDVI and EVI
    def calc_vis_ls(img):
        ndvi = img.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi')
        evi = img.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
                'NIR': img.select('SR_B5'),
                'RED': img.select('SR_B4'),
                'BLUE': img.select('SR_B2')
            }).rename('evi')
        return img.addBands([ndvi, evi])
    
    # Apply the scaling, cloud masking, and VI calculation
    processed = landsat.map(scaling_ls).map(mask_clouds).map(calc_vis_ls)
    return processed

#-------------------------------------------------------------------------------------------------------------------

def landsat8_evi_event_id_custom_date(event_id, start_date, end_date, cloud_cover):
    """
    Generate an Enhanced Vegetation Index (EVI) for a given Event ID and time period.

    Parameters:
        event_id (str): The Event ID to filter the MTBS dataset.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
        cloud_cover (int): Maximum cloud cover percentage (default: 80).

    Returns:
        ee.ImageCollection: Image collection with EVI and NDVI bands.
    """

    # Load the MTBS burned area boundaries dataset
    dataset = ee.FeatureCollection('USFS/GTAC/MTBS/burned_area_boundaries/v1')

    # Define the field and value to filter by
    field_name = 'Event_ID'

    # Filter the dataset by the specified Event ID
    filtered_feature = dataset.filter(ee.Filter.eq(field_name, event_id))

    # Check if the filtered dataset is empty
    count = filtered_feature.size().getInfo()
    if count == 0:
        print(f"No feature found with {field_name}: {event_id}")
        return None
    else:
        print(f"Generating EVI for feature with {field_name}: {event_id}")

    # Get the bounding box of the filtered feature
    bbox = filtered_feature.geometry()

    # Load Landsat 8 SR dataset
    landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(bbox) \
        .filterDate(start_date, end_date) \
        .filterMetadata('CLOUD_COVER', 'less_than', cloud_cover)

    # Function to scale Landsat bands
    def scaling_ls(img):
        optical = img.select('SR_B.').multiply(0.0000275).add(-0.2)
        thermal = img.select('ST_B.*').multiply(0.00341802).add(149.0)
        return img.addBands(optical, None, True).addBands(thermal, None, True)

    # Function to mask clouds
    def mask_clouds(img):
        cloud_shadow_bit_mask = (1 << 4)
        clouds_bit_mask = (1 << 3)
        clouds_cirrus_bit_mask = (1 << 2)
        clouds_dilated_bit_mask = (1 << 1)
        qa = img.select('QA_PIXEL')
        mask = qa.bitwiseAnd(cloud_shadow_bit_mask).eq(0) \
                .And(qa.bitwiseAnd(clouds_bit_mask).eq(0)) \
                .And(qa.bitwiseAnd(clouds_cirrus_bit_mask).eq(0)) \
                .And(qa.bitwiseAnd(clouds_dilated_bit_mask).eq(0))
        return img.updateMask(mask)

    # Function to calculate NDVI and EVI
    def calc_vis_ls(img):
        ndvi = img.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi')
        evi = img.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
                'NIR': img.select('SR_B5'),
                'RED': img.select('SR_B4'),
                'BLUE': img.select('SR_B2')
            }).rename('evi')
        return img.addBands([ndvi, evi])

    # Apply the scaling, cloud masking, and VI calculation
    processed = landsat.map(scaling_ls).map(mask_clouds).map(calc_vis_ls)

    # Create a map object to visualize the result
    map_ = geemap.Map()
    map_.addLayer(filtered_feature, {'color': 'red'}, f"MTBS Boundary: {event_id}")
    map_.addLayer(processed.median().clip(bbox), {'bands': ['evi'], 'min': 0, 'max': 1, 'palette': ['white', 'blue', 'green']}, 'EVI')

    # Center the map on the feature
    map_.centerObject(filtered_feature, zoom=10)

    return map_

#-------------------------------------------------------------------------------------------------------------------

def landsat_evi_by_event_id(event_id, cloud_cover):
    """
    Generate an Enhanced Vegetation Index (EVI) for a given Event ID and a time period
    10 days before and 10 days after the event's Ig_Date.

    Parameters:
        event_id (str): The Event ID to filter the MTBS dataset.
        cloud_cover (int): Maximum cloud cover percentage (default: 80).

    Returns:
        geemap.Map: Map displaying the MTBS boundary and the EVI layer.
    """

    # Load the MTBS burned area boundaries dataset
    dataset = ee.FeatureCollection('USFS/GTAC/MTBS/burned_area_boundaries/v1')

    # Define the field and value to filter by
    field_name = 'Event_ID'

    # Filter the dataset by the specified Event ID
    filtered_feature = dataset.filter(ee.Filter.eq(field_name, event_id))

    # Check if the filtered dataset is empty
    count = filtered_feature.size().getInfo()
    if count == 0:
        print(f"No feature found with {field_name}: {event_id}")
        return None
    else:
        print(f"Generating EVI for feature with {field_name}: {event_id}")

    # Get the Ig_Date of the filtered feature (Unix timestamp in milliseconds)
    ig_date_ms = filtered_feature.first().get('Ig_Date').getInfo()
    if not ig_date_ms:
        print(f"No Ig_Date found for {field_name}: {event_id}")
        return None

    # Convert the Ig_Date from Unix timestamp (milliseconds) to datetime object
    ig_date_dt = datetime.utcfromtimestamp(ig_date_ms / 1000)

    # Calculate the start and end dates (10 days before and after)
    start_date = (ig_date_dt - timedelta(days=10)).strftime('%Y-%m-%d')
    end_date = (ig_date_dt + timedelta(days=10)).strftime('%Y-%m-%d')

    print(f"Ig_Date: {ig_date_dt.strftime('%Y-%m-%d')}")
    print(f"Start Date: {start_date}")
    print(f"End Date: {end_date}")

    # Get the bounding box of the filtered feature
    bbox = filtered_feature.geometry()

    # Load Landsat 8 SR dataset
    landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(bbox) \
        .filterDate(start_date, end_date) \
        .filterMetadata('CLOUD_COVER', 'less_than', cloud_cover)

    # Function to scale Landsat bands
    def scaling_ls(img):
        optical = img.select('SR_B.').multiply(0.0000275).add(-0.2)
        thermal = img.select('ST_B.*').multiply(0.00341802).add(149.0)
        return img.addBands(optical, None, True).addBands(thermal, None, True)

    # Function to mask clouds
    def mask_clouds(img):
        cloud_shadow_bit_mask = (1 << 4)
        clouds_bit_mask = (1 << 3)
        clouds_cirrus_bit_mask = (1 << 2)
        clouds_dilated_bit_mask = (1 << 1)
        qa = img.select('QA_PIXEL')
        mask = qa.bitwiseAnd(cloud_shadow_bit_mask).eq(0) \
                .And(qa.bitwiseAnd(clouds_bit_mask).eq(0)) \
                .And(qa.bitwiseAnd(clouds_cirrus_bit_mask).eq(0)) \
                .And(qa.bitwiseAnd(clouds_dilated_bit_mask).eq(0))
        return img.updateMask(mask)

    # Function to calculate NDVI and EVI
    def calc_vis_ls(img):
        ndvi = img.normalizedDifference(['SR_B5', 'SR_B4']).rename('ndvi')
        evi = img.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
                'NIR': img.select('SR_B5'),
                'RED': img.select('SR_B4'),
                'BLUE': img.select('SR_B2')
            }).rename('evi')
        return img.addBands([ndvi, evi])

    # Apply the scaling, cloud masking, and VI calculation
    processed = landsat.map(scaling_ls).map(mask_clouds).map(calc_vis_ls)

    # Create a map object to visualize the result
    map_ = geemap.Map()
    map_.addLayer(filtered_feature, {'color': 'red'}, f"MTBS Boundary: {event_id}")
    map_.addLayer(processed.median().clip(bbox), {'bands': ['evi'], 'min': 0, 'max': 1, 'palette': ['white', 'blue', 'green']}, 'EVI')

    # Center the map on the feature
    map_.centerObject(filtered_feature, zoom=10)

    return map_

#-------------------------------------------------------------------------------------------------------------------

def sentinel2_evi_by_event_id(event_id, cloud_cover):
    """
    Generate an Enhanced Vegetation Index (EVI) using Sentinel-2 data for a given Event ID 
    and a time period 10 days before and 10 days after the event's Ig_Date.

    Parameters:
        event_id (str): The Event ID to filter the MTBS dataset.
        cloud_cover (int): Maximum cloud cover percentage (default: 20).

    Returns:
        geemap.Map or None: Map displaying the MTBS boundary and the EVI layer, or None if no images are found.
    """

    # Load the MTBS burned area boundaries dataset
    dataset = ee.FeatureCollection('USFS/GTAC/MTBS/burned_area_boundaries/v1')

    # Define the field and value to filter by
    field_name = 'Event_ID'

    # Filter the dataset by the specified Event ID
    filtered_feature = dataset.filter(ee.Filter.eq(field_name, event_id))

    # Check if the filtered dataset is empty
    count = filtered_feature.size().getInfo()
    if count == 0:
        print(f"No feature found with {field_name}: {event_id}")
        return None
    else:
        print(f"Generating EVI for feature with {field_name}: {event_id}")

    # Get the Ig_Date of the filtered feature (Unix timestamp in milliseconds)
    ig_date_ms = filtered_feature.first().get('Ig_Date').getInfo()
    if not ig_date_ms:
        print(f"No Ig_Date found for {field_name}: {event_id}")
        return None

    # Convert the Ig_Date from Unix timestamp (milliseconds) to datetime object
    ig_date_dt = datetime.utcfromtimestamp(ig_date_ms / 1000)

    # Calculate the start and end dates (10 days before and after)
    start_date = (ig_date_dt - timedelta(days=10)).strftime('%Y-%m-%d')
    end_date = (ig_date_dt + timedelta(days=10)).strftime('%Y-%m-%d')

    print(f"Ig_Date: {ig_date_dt.strftime('%Y-%m-%d')}")
    print(f"Start Date: {start_date}")
    print(f"End Date: {end_date}")

    # Get the bounding box of the filtered feature
    bbox = filtered_feature.geometry()

    # Load Sentinel-2 surface reflectance dataset    
    sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
        .filterBounds(bbox) \
        .filterDate(start_date, end_date) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover))

    # Check if the collection is empty
    if sentinel2.size().getInfo() == 0:
        print(f"No Sentinel-2 images found for Event ID: {event_id} in the specified date range.")
        return None

    # Function to calculate EVI for Sentinel-2
    def calc_evi(img):
        evi = img.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
                'NIR': img.select('B8'),     # Near-Infrared (NIR) band
                'RED': img.select('B4'),     # Red band
                'BLUE': img.select('B2')     # Blue band
            }).rename('evi')
        return img.addBands(evi)

    # Apply the EVI calculation
    processed = sentinel2.map(calc_evi)
    # Define visualization parameters
   



    # Create a map object to visualize the result
    map_ = geemap.Map()
    map_.addLayer(filtered_feature, {'color': 'red'}, f"MTBS Boundary: {event_id}")
    map_.addLayer(processed.median().clip(bbox), {'bands': ['evi'], 'min': 0, 'max': 1, 'palette': ['white', 'blue', 'green']}, 'EVI')

    # Center the map on the feature
    map_.centerObject(filtered_feature, zoom=10)

    return map_

#-------------------------------------------------------------------------------------------------------------------
