import logging

import azure.functions as func

import pystac_client
import planetary_computer

from IPython.display import Image
# from PIL import Image

import pandas as pd
import matplotlib.pyplot as plt
import geopandas as geopd

import io
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )

    logging.info('Python HTTP trigger function processed a request.')
    
    try:
        req_body = req.get_json()
        dataset = req_body['dataset']
        time_range = req_body['time_range']
        if "bbox" in req_body:
            bbox = req_body['bbox']
        elif "area_of_interest" in req_body:
            area_of_interest = req_body['area_of_interest']

        asset = req_body['asset']
        
        ext = req_body['extension']
        prop = req_body['property']

        # example tests:
        # {
        #     "dataset": "sentinel-2-l2a",
        #     "time_range": "2020-01-01/2020-12-31",
        #     "bbox": [-124.2751, 45.5469, -123.9613, 45.7458],
        #     "asset": "rendered_preview",
        #     "extension": "eo",
        #     "property": "cloud_cover",
        #     "plot": 24
        # }

        # {
        #     "dataset": "landsat-c2-l2",
        #     "time_range": "2020-12-01/2020-12-31",
        #     "bbox": [-122.2751, 47.5469, -121.9613, 47.7458],
        #     "asset": "rendered_preview",
        #     "extension": "eo",
        #     "property": "cloud_cover"
        # }
        #
    except (KeyError, json.JSONDecodeError) as e:
        return func.HttpResponse("Triggered successfully, but incomplete request body", status_code=400)

    search = catalog.search(collections=[dataset], bbox=bbox, datetime=time_range) if bbox else catalog.search(collections=[dataset], intersects=area_of_interest, datetime=time_range)
    items = search.get_all_items()
    selected_item = min(items, key=lambda item: item.properties[f"{ext}:{prop}"])

    # plots given extension:property against time
    if "plot" in req_body:
        windows = req_body.get('plot')
        df = geopd.GeoDataFrame.from_features(items.to_dict())
        df["datetime"] = pd.to_datetime(df["datetime"])
        ts = df.set_index("datetime").sort_index()[f"{ext}:{prop}"].rolling(windows).mean()
        fig, ax = plt.subplots()
        ts.plot(ax=ax, title=f"{ext}:{prop} ({windows}-window mean)")
        img = plt_to_img(plt)
        plt.close()

        headers = {
            'Content-Type': 'image/png'
        }
        return func.HttpResponse(body=img, headers=headers, status_code=200)

    return func.HttpResponse(
        selected_item.assets[asset].href,
        status_code=200
    )

# converts a matplotlib plot to a png image
def plt_to_img(plot):
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    img_bytes = buffer.getvalue()
    return img_bytes