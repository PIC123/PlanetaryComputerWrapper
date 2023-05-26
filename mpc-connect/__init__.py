import logging

import azure.functions as func

import pystac_client
import planetary_computer

# from IPython.display import Image
from PIL import Image

import pandas as pd
import matplotlib.pyplot as plt
import geopandas as geopd

# from django.http import HttpResponse

import io

def main(req: func.HttpRequest) -> func.HttpResponse:
    catalog = pystac_client.Client.open(
        "https://planetarycomputer.microsoft.com/api/stac/v1",
        modifier=planetary_computer.sign_inplace,
    )

    logging.info('Python HTTP trigger function processed a request.')

    # TODO: change to read from req body
    dataset = req.params.get('dataset') # ex: "landsat-c2-l2"
    time_range = '/'.join(req.params.get('time_range').split('_')) # ex: 2020-12-01_2020-12-31 -- underscore delimiter
    if "bbox" in req.params:
        bbox = map(lambda x: float(x), req.params.get('bbox').split('_')) # -122.2751_47.5469_-121.9613_47.7458 -- underscore delimiter
    elif "area_of_interest" in req.params:
        area_of_interest = req.params.get('area_of_interest')

    asset = req.params.get('asset') # ex: "rendered_preview" or "qa"
    
    ext = req.params.get('extension') # ex: "eo", "view", "proj"
    prop = req.params.get('property') # ex: "cloud_cover" / "snow_cover" (eo), "transform" (proj)

    # for testing example values:
    # dataset = landsat-c2-l2
    # time_range = 2020-12-01/2020-12-31
    # bbox = -122.2751_47.5469_-121.9613_47.7458
    # extension = eo
    # property = cloud_cover

    if not dataset or (not bbox and not area_of_interest) or not time_range or not asset or not ext or not prop:
        return func.HttpResponse("Hello! This HTTP triggered function executed successfully, but is missing some of the following: dataset, bbox, time_range, asset, extension, property.")

    search = catalog.search(collections=[dataset], bbox=bbox, datetime=time_range) if bbox else catalog.search(collections=[dataset], intersects=area_of_interest, datetime=time_range)
    items = search.get_all_items()
    selected_item = min(items, key=lambda item: item.properties[f"{ext}:{prop}"])

    # TODO: fix img_io type (returns ByteIO, not "str, bytes, or bytearray")
    if "plot" in req.params:
        windows = int(req.params.get('plot')) # ex: windows = 10
        df = geopd.GeoDataFrame.from_features(items.to_dict())
        df["datetime"] = pd.to_datetime(df["datetime"])
        ts = df.set_index("datetime").sort_index()[f"{ext}:{prop}"].rolling(windows).mean()
        ts.plot(title=f"{ext}:{prop} ({windows}-window mean)")
        
        # response = func.HttpResponse(status_code=200, mimetype="image/png")
        # plt.savefig(response, format="png")
        # return response

        img_io = plt_to_img(plt)

        return func.HttpResponse(
            img_io,
            mimetype="image/jpeg",
            status_code=200
        )

    return func.HttpResponse(
        selected_item.assets[asset].href,
        status_code=200
    )

def plt_to_img(plt):
    plt.figure()
    plt.plot([1, 2])
    plt.title("test")
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    im = Image.open(buf)
    rgb_im = im.convert('RGB')
    img_io = io.BytesIO()
    rgb_im.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    buf.close()
    img_io.close()
    return img_io