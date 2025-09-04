from typing import Iterable
from pxr import Usd, UsdShade
from vertices_to_h5m import vertices_to_h5m
import numpy as np
import os, tempfile
import argparse

"""
Converter from USD to h5m for use in a Omniverse - OpenMC workflow (and other related workflows :))

Usage:
    On the OpenMC docker container (currently williamjsmith15/omniverse-openmc)
    Run:
        python usd_h5m.py <usd_to_convert.usd> <h5m_as_output.h5m> <up-axis> 
        usd_to_convert - Input USD file (omniverse output format)
        h5m_as_output - Output h5m file (DAGMC input format)
        up-axis - Set the up-axis of the conversion (Omniverse is annoying with its choice of up axis (they choose Y whereas it should be Z for OpenMC...))
"""

# USD Helper Functions
def getValidProperty (primative, parameterName):
    # Get param
    prop = primative.GetProperty(parameterName)
    
    # Test validity
    if ( type(prop) == type(Usd.Attribute())): # is valid
        return prop.Get()
    else: # is not
        print("Requested parameter is not valid!")
        return None
        #raise Exception("Requested parameter is not valid!")

def getProperty (primative, parameterName): # Unsafe 
    # Get param
    prop = primative.GetProperty(parameterName).Get()

    return prop

def propertyIsValid (primative, parameterName):
    # Get param
    prop = primative.GetProperty(parameterName)
    
    # Test validity
    if ( type(prop) == type(Usd.Attribute())): # is valid
        return True
    else:
        return False

def get_rot(rotation):
    # Calculates rotation matrix given a x,y,z rotation in degrees
    factor = 2.0 * np.pi / 360.0   # Convert to radians
    x_angle, y_angle, z_angle = rotation[0]*factor, rotation[1]*factor, rotation[2]*factor
    x_rot = np.array([[1,0,0],[0,np.cos(x_angle),-np.sin(x_angle)],[0,np.sin(x_angle),np.cos(x_angle)]], dtype='float64')
    y_rot = np.array([[np.cos(y_angle),0,np.sin(y_angle)],[0,1,0],[-np.sin(y_angle),0,np.cos(y_angle)]], dtype='float64')
    z_rot = np.array([[np.cos(z_angle),-np.sin(z_angle),0],[np.sin(z_angle),np.cos(z_angle),0],[0,0,1]], dtype='float64')
    rot_mat = np.dot(np.dot(x_rot,y_rot),z_rot)
    return rot_mat

_ALLOWED_MATERIAL_PURPOSES = (
    UsdShade.Tokens.full,
    UsdShade.Tokens.preview,
    UsdShade.Tokens.allPurpose,
)

def get_bound_material(
    prim, material_purpose=UsdShade.Tokens.allPurpose, collection=""
):
    # From https://github.com/ColinKennedy/USD-Cookbook/blob/master/tricks/bound_material_finder/python/material_binding_api.py 30/01/23
    """
    Find the strongest material for some prim / purpose / collection.
    If no material is found for `prim`, this function will check every
    ancestor of Prim for a bound material and return that, instead.
    Reference:
        https://graphics.pixar.com/usd/docs/UsdShade-Material-Assignment.html#UsdShadeMaterialAssignment-MaterialResolve:DeterminingtheBoundMaterialforanyGeometryPrim
    Args:
        prim (`pxr.Usd.Prim`):
            The path to begin looking for material bindings.
        material_purpose (str, optional):
            A specific name to filter materials by. Available options
            are: `UsdShade.Tokens.full`, `UsdShade.Tokens.preview`,
            or `UsdShade.Tokens.allPurpose`.
            Default: `UsdShade.Tokens.allPurpose`
        collection (str, optional):
            The name of a collection to filter by, for any found
            collection bindings. If not collection name is given then
            the strongest collection is used, instead. Though generally,
            it's recommended to always provide a collection name if you
            can. Default: "".
    Raises:
        ValueError:
            If `prim` is invalid or if `material_purpose` is not an allowed purpose.
    Returns:
        `pxr.UsdShade.Material` or NoneType:
            The strongest bound material, if one is assigned.
    """
    def is_collection_binding_stronger_than_descendents(binding):
        return (
            UsdShade.MaterialBindingAPI.GetMaterialBindingStrength(
                binding.GetBindingRel()
            )
            == "strongerThanDescendents"
        )

    def is_binding_stronger_than_descendents(binding, purpose):
        """bool: Check if the given binding/purpose is allowed to override any descendent bindings."""
        return (
            UsdShade.MaterialBindingAPI.GetMaterialBindingStrength(
                binding.GetDirectBindingRel(materialPurpose=purpose)
            )
            == "strongerThanDescendents"
        )

    def get_collection_material_bindings_for_purpose(binding, purpose):
        """Find the closest ancestral collection bindings for some `purpose`.
        Args:
            binding (`pxr.UsdShade.MaterialBindingAPI`):
                The material binding that will be used to search
                for a direct binding.
            purpose (str):
                The name of some direct-binding purpose to filter by. If
                no name is given, any direct-binding that is found gets
                returned.
        Returns:
            list[`pxr.UsdShade.MaterialBindingAPI.CollectionBinding`]:
                The found bindings, if any could be found.
        """
        # XXX : Note, Normally I'd just do
        # `UsdShadeMaterialBindingAPI.GetCollectionBindings` but, for
        # some reason, `binding.GetCollectionBindings(purpose)` does not
        # yield the same result as parsing the relationships, manually.
        # Maybe it's a bug?
        #
        # return binding.GetCollectionBindings(purpose)
        #
        parent = binding.GetPrim()

        # TODO : We're doing quadratic work here... not sure how to improve this section
        while not parent.IsPseudoRoot():
            binding = binding.__class__(parent)

            material_bindings = [
                UsdShade.MaterialBindingAPI.CollectionBinding(relationship)
                for relationship in binding.GetCollectionBindingRels(purpose)
                if relationship.IsValid()
            ]

            if material_bindings:
                return material_bindings

            parent = parent.GetParent()

        return []

    def get_direct_bound_material_for_purpose(binding, purpose):
        """Find the bound material, using direct binding, if it exists.
        Args:
            binding (`pxr.UsdShade.MaterialBindingAPI`):
                The material binding that will be used to search
                for a direct binding.
            purpose (str):
                The name of some direct-binding purpose to filter by. If
                no name is given, any direct-binding that is found gets
                returned.
        Returns:
            `pxr.UsdShade.Material` or NoneType: The found material, if one could be found.
        """
        relationship = binding.GetDirectBindingRel(materialPurpose=purpose)
        direct = UsdShade.MaterialBindingAPI.DirectBinding(relationship)

        if not direct.GetMaterial():
            return None

        material = direct.GetMaterialPath()
        prim = binding.GetPrim().GetStage().GetPrimAtPath(material)

        if not prim.IsValid():
            return None

        return UsdShade.Material(prim)

    if not prim.IsValid():
        raise ValueError('Prim "{prim}" is not valid.'.format(prim=prim))

    if material_purpose not in _ALLOWED_MATERIAL_PURPOSES:
        raise ValueError(
            'Purpose "{material_purpose}" is not valid. Options were, "{options}".'.format(
                material_purpose=material_purpose,
                options=sorted(_ALLOWED_MATERIAL_PURPOSES),
            )
        )

    purposes = {material_purpose, UsdShade.Tokens.allPurpose}

    for purpose in purposes:
        material = None
        parent = prim

        while not parent.IsPseudoRoot():
            binding = UsdShade.MaterialBindingAPI(parent)

            if not material or is_binding_stronger_than_descendents(binding, purpose):
                material = get_direct_bound_material_for_purpose(binding, purpose)

            for collection_binding in get_collection_material_bindings_for_purpose(
                binding, purpose
            ):
                binding_collection = collection_binding.GetCollection()

                if collection and binding_collection.GetName() != collection:
                    continue

                membership = binding_collection.ComputeMembershipQuery()

                if membership.IsPathIncluded(parent.GetPath()) and (
                    not material
                    or is_collection_binding_stronger_than_descendents(
                        collection_binding
                    )
                ):
                    material = collection_binding.GetMaterial()

            # Keep searching ancestors until we hit the scene root
            parent = parent.GetParent()

        if material:
            return material













class USD_to_h5m:
    '''
    Class to convert USD to h5m file format usable for DAGMC, for use with OpenMC
    '''
    def __init__(self):
        # Initialise with blank numpy arrays
        self.vertices       = np.array([])
        self.triangles      = []
        self.material_tags  = []

    def add_USD_file(self, filepath, up_axis):
        '''
        Load parts form USD into class with their associated material tags and then converts to triangles for use 
        in the conversion script

        Args:
            filepath: filepath used to import the USD file with
        '''

        stage_file = filepath
        stage = Usd.Stage.Open(stage_file)
        volumeOffset = 0 # Required as all vertices have to be in a global 1D array (all volumes) => this offsets the indexing
                         # for each individual volume as all vertices for new volumes are added into the same array as previous
                         # volumes (vertices is 1D, triangles is 2D with 2nd dimension have the number of volumes in)

        material_count = 0 # For materials that 'fall through the net'

        for primID, x in enumerate(stage.Traverse()):
            primType = x.GetTypeName()
            print(f"PRIM: {str(primType)}")
            print(f'PrimID is {primID}')

            if str(primType) == 'Mesh' or str(primType) == 'Xform':
                material_count += 1
                # Get the material type of the meshes
                material_name = str(get_bound_material(x))
                try:
                    material_name = material_name.split('<')[1] # Just get material name from between <>
                    material_name = material_name.split('>')[0] # In form of UsdShade.Material(Usd.Prim(</World/Looks/Aluminum_Anodized>))
                    material_name = material_name.split('/')[-1] # Get the last name from file path
                    print(f"Material name is: {material_name}")
                except:
                    material_name = str(get_bound_material(x))
                    print('No omniverse-set USD material found')
                    print(f'Setting material name to default: {material_name}')

                # Get num of vertecies in elements
                allVertexCounts  = np.array(getValidProperty(x,"faceVertexCounts"))
                allVertexIndices = np.array(getValidProperty(x,"faceVertexIndices"))
                print(allVertexCounts.size)

                # Get if there is rotation or translation of the meshes
                rotation = [0.0,0.0,0.0] if not propertyIsValid(x,"xformOp:rotateXYZ") else list(getProperty(x,"xformOp:rotateXYZ"))
                translation = np.array([0,0,0]) if not propertyIsValid(x,"xformOp:translate") else np.array(list(getProperty(x,"xformOp:translate")))
                print(f'Rotation is {rotation}')
                print(f'Translation is {translation}')

                # Handling for changing the up axis
                if up_axis == 'X':
                    rotation[1] -= 90.0 # TODO: Check this is correct...
                elif up_axis == 'Y':
                    rotation[0] += 90.0
                elif up_axis == 'Z':
                    rotation = rotation
                else:
                    print('Something went wrong with up_axis')


                rot_matrix = get_rot(rotation)
                
                # TODO: Make the rotation matrix multiplication better! Lazy coding for now...
                newVertices = np.array(getValidProperty(x,"points"), dtype='float64') # Assign vertices here and add rotation and translation
                newVertices = np.array([np.dot(rot_matrix,xyz) for xyz in newVertices]) # Have to rotate first before translating as it rotates around the origin
                newVertices = newVertices + translation

                if self.vertices.size == 0: # For first run though just set vertices to newVertices array
                    self.vertices = newVertices
                else:
                    self.vertices = np.append(self.vertices, newVertices, axis=0)

                globalCount = 0
                extraPointCount = 0
                endOfVolumeIdx = np.size(self.vertices,0)
                trianglesForVolume = np.array([], dtype="int")

                if np.all(allVertexCounts == 3): # Case where mesh is already in triangles (makes program run much faster - hopeuflly!)
                    trianglesForVolume = allVertexIndices.reshape((allVertexCounts.size,3)) + volumeOffset
                else:
                    for Count in allVertexCounts:
                        if Count == 3:      # Triangle
                            a, b, c = globalCount, globalCount+1, globalCount+2
                            # For explanation of +volumeOffset see initialisation of volumeOffset variable
                            if trianglesForVolume.size == 0: # This whole shenanegans is because i dont know how to use numpy arrays properly.... LEARN
                                trianglesForVolume = np.array([[allVertexIndices[a]+volumeOffset, allVertexIndices[b]+volumeOffset, allVertexIndices[c]+volumeOffset]])
                            else:
                                trianglesForVolume = np.append(trianglesForVolume, np.array([[allVertexIndices[a]+volumeOffset, allVertexIndices[b]+volumeOffset, allVertexIndices[c]+volumeOffset]]), axis=0)
                        elif Count == 4:    # Quadrilateral => Split into 2 triangles
                            a, b, c, d = globalCount, globalCount+1, globalCount+2, globalCount+3
                            if trianglesForVolume.size == 0:
                                trianglesForVolume = np.array([[allVertexIndices[a]+volumeOffset, allVertexIndices[b]+volumeOffset, allVertexIndices[c]+volumeOffset]])
                            else:
                                trianglesForVolume = np.append(trianglesForVolume, np.array([[allVertexIndices[a]+volumeOffset, allVertexIndices[b]+volumeOffset, allVertexIndices[c]+volumeOffset]]), axis=0)
                            #Think this may cause issues with some quadrilaterials being split into 2 triangles that overlap and leave a gap - see latex doc
                            trianglesForVolume = np.append(trianglesForVolume, np.array([[allVertexIndices[a]+volumeOffset, allVertexIndices[c]+volumeOffset, allVertexIndices[d]+volumeOffset]]), axis=0) 
                        elif Count > 4:     # n points to triangles
                            indices = np.array([allVertexIndices[globalCount+i]+volumeOffset for i in range(Count)]) # Get array of indices of points 
                            points = np.array([self.vertices[idx] for idx in indices]) # Get points that match those indices
                            # Find mifddle of n-sided polygon => can make triangles from every edge to centre point and add to end of vertices matrix
                            self.vertices = np.append(self.vertices, np.array([[np.average(points[:,dir]) for dir in range(3)]]), axis=0) 
                            
                            centrePointIdx = endOfVolumeIdx + extraPointCount
                            extraPointCount += 1 # Just added an extra point into the vertices array

                            for triangleNum in range(Count):
                                if triangleNum == Count - 1: # Last triangle
                                    trianglesForVolume = np.append(trianglesForVolume, np.array([[indices[0], indices[triangleNum], centrePointIdx]]), axis=0)
                                else:
                                    if trianglesForVolume.size == 0:
                                        trianglesForVolume = np.array([[indices[triangleNum], indices[triangleNum+1], centrePointIdx]])
                                    else:
                                        trianglesForVolume = np.append(trianglesForVolume, np.array([[indices[triangleNum], indices[triangleNum+1], centrePointIdx]]), axis=0)
                        else:
                            print(f"I don't know what to do with a {Count} count yet...")
                    
                        globalCount += Count

                
                self.triangles.append(trianglesForVolume)
                self.material_tags.append(material_name)
                shapeVertices = np.shape(newVertices)
                volumeOffset += shapeVertices[0] + extraPointCount # Account for all points plus any extras added in from Counts>4

            else:
                print(f"I don't know what to do with a {str(primType)} yet...")
            
            print("\n\n")


    def save_to_h5m(self, filepath):
        '''
        Use the verticies saved in the class to convert to h5m using the vertices_to_h5m mini package
        https://github.com/fusion-energy/vertices_to_h5m

        Args:
            filename: Filename to save the h5m file, default will be dagmc.h5m (as this is the format required by DAGMC)
        '''

        vertices_to_h5m(
            vertices=self.vertices,
            triangles=self.triangles,
            material_tags=self.material_tags,
            h5m_filename=filepath,
        )



if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="USD to h5m geometry converter",
        prog="usd_h5m.py"
    )

    parser.add_argument("usd_to_convert", help="USD file to convert")
    parser.add_argument("h5m_as_output", help="h5m filename/location to write")
    parser.add_argument("up_axis", help="The up axis for the simulation (Omniverse sets y as vertical, OpenMC sets Z)")

    args = parser.parse_args()

    usd_to_convert = args.usd_to_convert
    h5m_as_output = args.h5m_as_output
    up_axis = args.up_axis
    convert = USD_to_h5m()
    convert.add_USD_file(filepath=usd_to_convert, up_axis=up_axis)
    convert.save_to_h5m(filepath=h5m_as_output)