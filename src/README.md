# Assessing climate factors and vegetation conditions influencing the wildfires in California

This guide will walk you through running a Docker container using the provided Dockerfile, setting up the Conda environment, and executing these file Jupyter notebook.

## Pre-requisites

Ensure that you have the following installed on your machine:

- [Docker](https://docs.docker.com/get-docker/)
- Clone of this repository

## Steps to Run the Docker Container

### 1. Pull the Docker Image form Dockerhub

It's recommended to pull the Docker image from Dockerhub.

```bash
docker pull bikal3/wildfire_image:1.0.0
```

Otherwise, if you prefer, you can build your own image go to folder geog313-final-project

```bash
docker build -t bikal3/wildfire_image:1.0.0 .
```

### 2. Run the Docker Container

Go to folder geog313-final-project and run the container using the following command:

```bash
docker run -p 8888:8888 -p 8787:8787 -v $(pwd):/home/jupyteruser --name wildfire_container bikal3/wildfire_image:1.0.0
```

Port `8787` is used by Dask Dashboard.

### 3. Access JupyterLab

Once the container is running, JupyterLab will start and an access token will be printed in the terminal.

### 4. Open the Notebook

After logging into JupyterLab, you should see the file name with ipynb extention notebook in the directory. Click to open it, and you can start running the code.

### Stopping the Container

To stop the running container, execute:

```bash
docker stop wildfire_container
```

### Restarting the Container

If you want to restart the container later, you can use:

```bash
docker start -i wildfire_container
```

### Removing the Container and Image

To remove the container and image after you are done:

```bash
docker rm wildfire_container
docker rmi bikal3/wildfire_image:1.0.0
```

## User Recommendation
Go through each notebook listed here to generate the required outcomes. For more information about the project's purpose, refer to the Report linked above. 

| src                     | Objective                                                                                                  |
| ----------------------- | ---------------------------------------------------------------------------------------------------------- |
| fires_notebook.ipynb    | Explore and visualize MTBS burned boundaries, burned severity, and Existing Vegetation Cover from Landfire |
| evi.api.ipynb           | Generate a map using Landsat and Sentinel2 for display an Enhanced Vegetation Index         |
| mtbs_example.ipynb      | Retrieve seasonality of wildfire based on bbox, start date and end date.                                       |
| openmeteo_example.ipynb | Retrieve weather conditions based on event_id giving a period of analysis and selected variables                                                              |
| mtbs_source_coop.ipynb  | Create a wildfire severity map using the MTBS shapefile data 1982-2022                                              |

## Folder Structure: SRC

| src                     | Description                                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------- |
| evi.api.ipynb           | Jupyter notebook for retrieve Landsat and Sentinel2 for display an Enhanced Vegetation Index |
| fires_notebook.ipynb    | Jupyter notebook to visualize MTBS and Existing Vegetation Cover                             |
| mtbs_example.ipynb      | Jupyter notebook for retrieve MTBS by bbox from Google Earth Engine and geemap               |
| mtbs_source_coop.ipynb  | Jupyter notebook for retrieve MTBS by state from Source coop,Dask,Docker                     |
| openmeteo_example.ipynb | Jupyter notebook for retrieve weather data from open meteo 

## Folder Structure: utils

| utils                | Description                                          |
| -------------------- | ---------------------------------------------------- |
| evi_utils.py         | List of extension to retrieve Landsat and Sentinel 2 |
| mtbs_utils.py        | List of extension to retrieve mtbs                   |
| openmeteo_utils.py   | List of extension to retrieve openmeteo              |
| source_coop_utils.py | List of extension to retrieve source coop            |

## File Structure: mtbs_utils

| mtbs_utils.py                   | Parameters                                                                                                                      | Description                                                                                   |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| initialize_gee                  | ee.Initialize()                                                                                                                 | Authenticate and initialize the Google Earth Engine API.                                      |
| get_month_start_end             | Date string in 'YYYY-MM-DD HH:MM:SS' format.                                                                                    | Given an event date, return the start date and end date of that month                         |
| datetime_to_unix                | Unix timestamp in milliseconds                                                                                                  | Convert a date string in 'YYYY-MM-DD' format to Unix timestamp in milliseconds                |
| display_mtbs_burn_severity      | start_date:'YYYY-MM-DD' format, end_date:'YYYY-MM-DD' format, bbox (list): Bounding box as [min_lon, min_lat, max_lon, max_lat] | Display the MTBS burn severity map within a specified date range and bounding box             |
| display_mtbs_boundaries         | start_date:'YYYY-MM-DD' format, end_date:'YYYY-MM-DD' format, bbox (list): Bounding box as [min_lon, min_lat, max_lon, max_lat] | Display the MTBS burned area boundaries within a specified bounding box and date range        |
| display_mtbs_by_event_id        | event ID                                                                                                                        | Display the MTBS burned area boundary for a specific Event ID                                 |
| get_mtbs_properties             | event ID                                                                                                                        | Retrieve the properties of an MTBS burned area boundary feature based on Event ID.            |
| get_mtbs_properties_by_name     | event name                                                                                                                      | Retrieve the properties of an MTBS burned area boundary feature based on event name           |
| get_mtbs_time_series_by_Ig_date | start date, end date, bounding box                                                                                              | Perform a time series analysis on the MTBS burned area boundaries dataset using Ig_Date range |
| get_season                      | by month                                                                                                                        | Retrieve season by specific months. Eg. eg. winter = 12,1,2, summer = 6,7,8,                  |
| plot_burned_area_by_season      | x=year and y=season                                                                                                             | Function to plot BurnBndAcres by seasonality in stacked bars.                                 |
| plot_burnedareabyseasonside     | x=year and y=season                                                                                                             | Function to plot BurnBndAcres by seasonality with side-by-side bars.                          |
| plot_burnedareabyseasonhect     | x=year and y=season                                                                                                             | Function to plot BurnBndHectares by seasonality with side-by-side bars                        |
| displaymtbsbyeventstartdate     | The Event ID to filter the dataset                                                                                              | Display the MTBS burned area boundary for a specific Event ID and Event Date                  |

## File Structure: evi_utils

| evi_utils.py                      | Parameters                                                                                | Description                                                                                                                                                    |
| --------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| generate_evi                      | bbox (ee.Geometry from MTBS);start_date:'YYYY-MM-DD' format; end_date:'YYYY-MM-DD' format | Generate an Enhanced Vegetation Index (EVI) for a given bbox and time period                                                                                   |
| scaling_ls                        |                                                                                           | Function to scale Landsat bands                                                                                                                                |
| mask_clouds                       |                                                                                           | Function to mask clouds                                                                                                                                        |
| calc_vis_ls                       |                                                                                           | Function to calculate NDVI and EVI                                                                                                                             |
| landsat8_evi_event_id_custom_date | event_id, start_date, end_date, cloud_cover                                               | Generate an Enhanced Vegetation Index (EVI) for a given Event ID and time period                                                                               |
| landsat_evi_by_event_id           | event_id (str): The Event ID to filter the MTBS dataset; cloud_cover:80                   | Generate an Enhanced Vegetation Index (EVI) for a given Event ID and a time period 10 days before and 10 days after the event's Ig_Date.                       |
| sentinel2_evi_by_event_id         | event_id (str): The Event ID to filter the MTBS dataset; cloud_cover:20                   | Generate an Enhanced Vegetation Index (EVI) using Sentinel-2 data for a given Event ID and a time period 10 days before and 10 days after the event's Ig_Date. |

## File Structure: openmeteo_utils

| openmeteo_utils.py | Parameters                                                                 | Description                                 |
| ------------------ | -------------------------------------------------------------------------- | ------------------------------------------- |
| fetch_weather_data | latitude, longitude, start_date, end_date, daily_variables, timezone="GMT" | Function to setup the Open-Meteo API client |

## File Structure: source_coop_utils

| source_coop_utils.py    | Parameters                  | Description                                                                 |
| ----------------------- | --------------------------- | --------------------------------------------------------------------------- |
| initialize_dask_cluster | cluster_kwargs              | Initializes a Dask LocalCluster and Client, and prints the dashboard link   |
| get_s3_keys             | bucket_name, prefix, client | Fetches all the S3 keys associated with a specified prefix.                 |
| get_usgs_data           | file_name, s3_client        | Extract parquet                                                             |
| get_mtbs_shp            | file_name, s3_client        | Extract shapefile or any other file if you write the extension of that file |
