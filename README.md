# SwiftBlock

SwiftBlock is a [Blender](https://www.blender.org/) GUI add-on for
the OpenFOAM® *BlockMesh* utility, which creates hexahedral block
structured volume meshes for OpenFOAM simulations. Block structure is
first modelled as a mesh object in Blender. A graph theory based
method implemented in the addon identifies the discrete hexahedral
blocks in the mesh object and generates blockMeshDict. Main features
include

* user specified divisions and optional grading of block edges
* specification of patches (boundary surfaces)
* specification of blocks to create cell zones/sets
* easy block manipulations including selection, visualisation and disabling of blocks
* visualization of edge directions
* projection of block edges to surfaces on another object to
  create curved shapes

Application examples include creation of block meshes for

* orthogonal base mesh with elongated or stretched cells for
  SnappyHexMesh
* controlled grading of hexahedral meshes inside or outside
  rectangular, cylindrical or spherical shapes.

The add-on has been tested with
[Blender 2.81a](https://www.blender.org/) and
[OpenFOAM Foundation](https://openfoam.org/) version 7 of OpenFOAM.

## Documentation

Documentation is available in the *doc* directory in the source code,
and for web viewing at
http://tkeskita.kapsi.fi/blender/SwiftBlock/docs/swift.html

### OpenFOAM Trade Mark Notice

This offering is not approved or endorsed by OpenCFD Limited, producer
and distributor of the OpenFOAM software via www.openfoam.com, and
owner of the OPENFOAM® and OpenCFD® trade marks.
