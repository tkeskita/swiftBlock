# SwiftBlock
Blender addon for creating blockMeshDict files for OpenFOAM's blockMesh application. Compatible with Blender 3D 2.76 -> , OpenFOAM 5.0 -> and numpy 1.13->

## New features:
* The SwiftBlock panel has moved from properties panel to tools panel
* The block structure is saved to .blend file and therefore the time consuming block detection algorithm is only required when the block structure is changed
* The blocks are listed in the SwiftBlock panel
* Blocks can be selected, disabled and enabled interactively from the list
* Blocks can be searched from the current mesh selection
* Number of cells are defined instead of the maximum cell size
* The parallel edges of an edge can be selected easily
* The edge directions visualization
* The new projection vertices, edges and faces to surfaces has been implemented
* The projections are listed in the panel
* The projections can be selected and removed from the list
* Show/hide internal faces to make projections on them
* The automatic snapping algorithm can also be selected
* Extrude blocks operator which preserves internal edges and faces (ALT+E opens the extrude menu)
