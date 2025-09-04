import paramak
import numpy as np
import argparse
from stl_to_h5m import stl_to_h5m
import json
import sys

parser = argparse.ArgumentParser(
    prog='tile_paramak.py',
    description='Paramak tile geometry generator. Useage: python tile_paramak.py <config file path>'
)

parser.add_argument('config_file', help='Config .json file with the parameters for the geometry creation. See https://github.com/UoMResearchIT/omniverse-galaxy/tree/main/templates/openmc/paramak_config_MASTER.txt for more details.')
args = parser.parse_args()
config_path = args.config_file


class tokamak_sizing:
    def __init__(self, tile_thickness=15, no_gap=True, full_geometry=False, tile_segments=0):
        self.tile_thickness = tile_thickness
        self.no_gap = no_gap
        self.pv_tile_gapsize = 2
        self.full_geometry = full_geometry
        self.tile_segments = tile_segments

        # PLASMA BASELINE PARAMETERS - DO NOT CHANGE (unless we re-size tokamak baseline)
        self.n_tile_segments = 8
        self.tile_gap_size = 2
        self.max_tile_major_radius = 85
        self.max_tile_minor_radius = 60
        self.max_tile_triangularity = 0.3
        self.max_tile_elongation = 1.8
        self.solenoid_clearance = 5
        self.max_PV_thickness = 5
        self.max_tile_thickness = self.max_tile_major_radius - self.max_tile_minor_radius - self.solenoid_clearance - self.max_PV_thickness
        self.max_tile_r_upper = self.max_tile_major_radius-(self.max_tile_triangularity*self.max_tile_minor_radius)
        self.max_tile_b = self.max_tile_minor_radius*self.max_tile_elongation  # 1/2 height of tokamak
        self.tile_thickness_is_acceptable = tile_thickness <=self.max_tile_thickness

    def get_pressure_vessel_size(self):
        if not self.tile_thickness_is_acceptable:
            sys.exit('[ERROR] Tile thickness must be <= '+str(self.max_tile_thickness))
        PV_major_radius = self.max_tile_major_radius
        PV_minor_radius = self.max_tile_minor_radius + self.max_tile_thickness
        PV_triangularity = (PV_major_radius-self.max_tile_r_upper)/PV_minor_radius
        PV_b = self.max_tile_thickness + self.max_tile_b
        PV_elongation = PV_b/PV_minor_radius
        PV_thickness = self.max_PV_thickness
        return PV_major_radius, PV_minor_radius, PV_triangularity, PV_b, PV_elongation, PV_thickness

    def get_tile_size(self):
        if not self.tile_thickness_is_acceptable:
            sys.exit('[ERROR] Tile thickness must be <= '+str(self.max_tile_thickness))
        PV_major_radius, PV_minor_radius, PV_triangularity, PV_b, PV_elongation, PV_thickness = self.get_pressure_vessel_size()
        tile_major_radius = self.max_tile_major_radius
        if self.no_gap:
            tile_minor_radius = PV_minor_radius-self.tile_thickness
        else:
            tile_minor_radius = PV_minor_radius-self.tile_thickness-self.pv_tile_gapsize
        tile_triangularity = (tile_major_radius - self.max_tile_r_upper)/tile_minor_radius
        tile_b = PV_b-self.tile_thickness
        tile_elongation = tile_b/tile_minor_radius-0.05
        return tile_major_radius, tile_minor_radius, tile_triangularity, tile_b, tile_elongation

    def generate_pressure_vessel_geometry(self):
        PV_major_radius, PV_minor_radius, PV_triangularity, PV_b, PV_elongation, PV_thickness = self.get_pressure_vessel_size()
        if self.full_geometry:
            pressure_vessel = paramak.BlanketFP(
                minor_radius=PV_minor_radius,
                major_radius=PV_major_radius,
                triangularity=PV_triangularity,
                elongation=PV_elongation,
                thickness=PV_thickness,
                start_angle=-270,
                stop_angle=90,
                rotation_angle=360)
        else:
            pressure_vessel = paramak.BlanketFP(
                minor_radius=PV_minor_radius,
                major_radius=PV_major_radius,
                triangularity=PV_triangularity,
                elongation=PV_elongation,
                thickness=PV_thickness,
                start_angle=-270,
                stop_angle=90,
                rotation_angle=90)
        return pressure_vessel

    def generate_tile_geometry(self, pressure_vessel=None, segmented=False):
        tile_major_radius, tile_minor_radius, tile_triangularity, tile_b, tile_elongation = self.get_tile_size()
        offset = 0  # no need to change
        outboard_gaps = paramak.BlanketCutterStar(
            distance=self.tile_gap_size,
            azimuth_placement_angle=np.linspace(
                0 + offset,
                360 + offset,
                self.n_tile_segments,
                endpoint=False)
            )

        if self.full_geometry:
            rotation_angle = 360
        else:
            rotation_angle = 90

        if self.no_gap:
            cut_list = [outboard_gaps, pressure_vessel]
            tile_thickness_adjusted = self.tile_thickness+self.max_PV_thickness-1
        else:
            pressure_vessel = None
            cut_list = [outboard_gaps]
            tile_thickness_adjusted = self.tile_thickness

        if segmented:
            # segmentation in the poloidal direction - off by default
            # print(self.tile_segments)
            poloidalCut = paramak.BlanketFPPoloidalSegments(
                minor_radius=tile_minor_radius,
                major_radius=tile_major_radius,
                triangularity=tile_triangularity,
                elongation=tile_elongation,
                num_segments=int(self.tile_segments),
                segments_gap=0.5,
                thickness=self.tile_thickness,
                stop_angle=90,
                start_angle=-270,
                rotation_angle=rotation_angle
            )
            poloidalCutterGeom = poloidalCut.segments_cutters
            cut_list.append(poloidalCutterGeom)

        tiles = paramak.BlanketFP(
            minor_radius=tile_minor_radius,
            major_radius=tile_major_radius,
            triangularity=tile_triangularity,
            elongation=tile_elongation,
            thickness=tile_thickness_adjusted,
            start_angle=-270,
            stop_angle=90,
            rotation_angle=rotation_angle,
            cut=cut_list
            )

        return tiles


if __name__ == "__main__":
    with open(config_path, 'r') as f:
        data = json.load(f)
        config_dict = data['geometry']

    tile_thickness = config_dict["tile_thickness"]
    if "tile_segments" in config_dict.keys():
        tile_segments = config_dict["tile_segments"]
    else:
        tile_segments = 0
    tokamak_sizer = tokamak_sizing(tile_thickness=tile_thickness, no_gap=False, full_geometry=False, tile_segments=tile_segments)
    pressure_vessel = tokamak_sizer.generate_pressure_vessel_geometry()
    if tile_segments != 0:
        segmented_bool = True
    else:
        segmented_bool = False
    tiles = tokamak_sizer.generate_tile_geometry(pressure_vessel=pressure_vessel, segmented=segmented_bool)
    reactor = paramak.Reactor([pressure_vessel, tiles])

    tiles.export_stl('./sampleTiles.stl')
    pressure_vessel.export_stl('./samplePressureVessel.stl')

    h5m_file = stl_to_h5m(
        files_with_tags=[
            ('sampleTiles.stl', 'tiles'),
            ('samplePressureVessel.stl', 'pressure_vessel'),
        ],
        h5m_filename='dagmc.h5m'
    )

    pressure_vessel.export_stp('./vessel.stp')
