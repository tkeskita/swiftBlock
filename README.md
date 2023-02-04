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

* structured meshes with control of boundary layers
* orthogonal base mesh with elongated or stretched cells for
  SnappyHexMesh
* controlled grading of hexahedral meshes inside or outside
  rectangular, cylindrical or spherical shapes.

<p align="center">
<img src="docs/images/complex_block_with_elongations.png">
</p>

The add-on has been tested with
[Blender LTS 3.3](https://www.blender.org/) and
[OpenFOAM Foundation](https://openfoam.org/) version 10 of OpenFOAM.

## Documentation

Documentation (made using [Sphinx](https://www.sphinx-doc.org/en/master/))
is located in docs directory of the sources and is viewable online at
https://swiftblock.readthedocs.io.

### OpenFOAM Trade Mark Notice

This offering is not approved or endorsed by OpenCFD Limited, producer
and distributor of the OpenFOAM software via www.openfoam.com, and
owner of the OPENFOAM® and OpenCFD® trade marks.
