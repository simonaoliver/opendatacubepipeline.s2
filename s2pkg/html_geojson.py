# coding=utf-8
"""
Execution method for creation of map.html and bounding geojson:
    python html_geojson.py ALLBANDS_20m.contiguity.img
"""
from __future__ import absolute_import
import os
import logging
import rasterio
import rasterio.features
import folium
from folium import GeoJson
import shapely
import shapely.affinity
import shapely.geometry
import shapely.ops
import geopandas as gpd
import click
os.environ["CPL_ZIP_ENCODING"] = "UTF-8"


def valid_region(fname, mask_value=None):
    """
    Return valid data region for input images based on mask value and input image path
    """
    mask = None
    logging.info("Valid regions for %s", fname)
    # ensure formats match
    with rasterio.open(str(fname), 'r') as dataset:
        transform = dataset.transform.to_gdal()
        crs = dataset.crs.to_dict()
        img = dataset.read(1)

        if mask_value is not None:
            new_mask = img & mask_value == mask_value
        else:
            new_mask = img != 0
        if mask is None:
            mask = new_mask
        else:
            mask |= new_mask

    shapes = rasterio.features.shapes(mask.astype('uint8'), mask=mask)
    shape = shapely.ops.unary_union([shapely.geometry.shape(shape) for shape, val in shapes if val == 1])

    # convex hull
    geom = shape.convex_hull

    # buffer by 1 pixel
    geom = geom.buffer(1, join_style=3, cap_style=3)

    # simplify with 1 pixel radius
    geom = geom.simplify(1)

    # intersect with image bounding box
    geom = geom.intersection(shapely.geometry.box(0, 0, mask.shape[1], mask.shape[0]))

    # transform from pixel space into CRS space
    geom = shapely.affinity.affine_transform(geom, (transform[1], transform[2], transform[4], transform[5], transform[0], transform[3]))

    return geom, crs


def html_map(contiguity_fname, html_out_fname, json_out_fname):
    """
    Create HTML and GeoJSON files showing the valid geometry
    for the input contiguity image.

    :param contiguity_fname:
        A full file pathname to the image representing the data
        contiguity.

    :param html_out_fname:
        A full file pathname that will contain the html bounday map.

    :param json_out_fname:
        A full file pathname that will contain the json bounday map.

    :return:
        None; Outputs will be saved directly to disk.
    """
    # remove any previous creations
    try:
        os.remove(html_out_fname)
    except OSError:
        pass
    try:
        os.remove(json_out_fname)
    except OSError:
        pass

    # Find metadata yaml and add to geopandas attributes
    #metadata = os.path.abspath(os.path.join(out_dir, "..", "ARD-METADATA.yaml"))

    logging.info("Create valid bounds " + json_out_fname)
    geom, crs = valid_region(contiguity_fname)
    gpdsr = gpd.GeoSeries([geom])
    gpdsr.crs = crs
    gpdsr = gpdsr.to_crs({'init': 'epsg:4326'})

    # TODO - Add metadata to PopUp
    #with open(metadata, 'r') as stream:
    #    try:
    #        yaml_metadata = yaml.load(stream)
    #    except yaml.YAMLError as exc:
    #        print(exc)
    #gpdyaml = gpd.GeoSeries(yaml_metadata)

    gpdsr.to_file(json_out_fname, driver='GeoJSON')
    m = folium.Map()

    #GeoJson(gpdsr, name='geojson').add_to(m)
    style_function = lambda x: {'fillColor': None,
                                'color' : '#0000ff'}
    GeoJson(json_out_fname, name='bounds.geojson', style_function=style_function).add_to(m)
    # TODO - add MGRS tile reference to map with layer active = False
    #style_function = lambda x: {'fillColor': None, 'fillOpacity': 0.1, 'weight': 0.1,
    #                               'color' : '#ff0000'}
    #GeoJson('/home/simonaoliver/reference/agdcv2-reference/MGRS_Australia.geojson', name='MGRS_tiles.geojson', style_function=style_function).add_to(m)

    m.fit_bounds(GeoJson(gpdsr).get_bounds())
    folium.LatLngPopup().add_to(m)

    #m.add_child(folium.Popup("Insert Date Here"))
    folium.LayerControl().add_to(m)
    m.save(html_out_fname)


@click.command(help=__doc__)
@click.argument('contiguity',
                type=click.Path(exists=True, readable=True, writable=False),
                nargs=-1)
def main(contiguity):
    """
    For input contiguity write geojson valid data extent and publish html folium map to
    'contiguity directory'
    """
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    contiguity = os.path.abspath(str(contiguity[0]))
    out_dir = os.path.dirname(contiguity)
    geo_path = os.path.join(out_dir, 'bounds.geojson')
    html_path = os.path.join(out_dir, 'map.html')

    html_map(contiguity, html_path, geo_path)


if __name__ == "__main__":
    main()
