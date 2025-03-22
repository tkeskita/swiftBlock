SwiftBlock Addon for Blender
============================

.. image:: images/naca_airfoil_mesh_preview.png

Introduction
------------

SwiftBlock is a `Blender <https://www.blender.org/>`_ GUI add-on for
the OpenFOAM® *blockMesh* utility, which creates hexahedral block
structured volume meshes for OpenFOAM simulations.
The target of SwiftBlock is to ease the creation of structured
block meshes for controlled grading (e.g. boundary layers) or streched
cells composed of hexahedral cell blocks.

Block structure is first modelled as a mesh object in Blender. A graph
theory based method implemented in the addon identifies the discrete
hexahedral blocks in the mesh object and generates blockMeshDict. Main
features include

* user specified divisions and optional grading of block edges
* specification of patches (boundary surfaces)
* specification of blocks to create cell zones/sets
* easy block manipulations including selection, visualisation and disabling of blocks
* visualization of edge directions
* projection of block edges to surfaces on mesh objects to
  create e.g. curved shapes


Versions
--------

This documentation describes the version of the add-on available under
`github/tkeskita <https://github.com/tkeskita/swiftBlock>`_.
The add-on is aimed to work with latest
`Blender LTS version <https://www.blender.org/download/lts/>`_ and
latest `OpenFOAM Foundation <https://openfoam.org>`_ and
latest `OpenFOAM.com <https://openfoam.com>`_ versions.
Tested with Blender 4.2 and OpenFOAM.org v12

Please note that
`Preview command has an issue on Windows OS <https://github.com/tkeskita/swiftBlock/issues/12>`_.

Previous versions of the add-on are available in
`github/nogenmyr <https://github.com/nogenmyr/swiftBlock>`_ and
`github/Flowkersma <https://github.com/Flowkersma/swiftBlock>`_, 
and the documentation for original version is available at
`OpenFOAM wiki <http://openfoamwiki.net/index.php/SwiftBlock>`_.


Installation and Start-up
-------------------------

* Add-on code is available at https://github.com/tkeskita/swiftBlock.
  To download add-on from Github, Select "Code", then
  "Download ZIP".
* Start a terminal (command line window).
* Source OpenFOAM in the terminal window if needed (see `OpenFOAM environment variables <https://openfoamwiki.net/index.php/Installation/Working_with_the_Shell#OpenFOAM_Environment_Variables>`_).
  If OpenFOAM commands (e.g. `blockMesh`) are not available in the terminal,
  you can't run the *Preview* command in the add-on.
* Start Blender from the same terminal window.
* Add-on installation:

  * In Blender, go to
    "Edit" --> "Preferences" --> "Add-ons" --> "Install" --> open the add-on zip file.
  * Activate the "SwiftBlock" add-on in Preferences.
    Add-on is located in OpenFOAM category, Testing level of Blender add-ons.


Add-on visibility
-----------------

Add-on is visible in Blender's 3D Viewport in Sidebar as a separate
tab in Edit Mode. To view the add-on panels, you must

  * Select a mesh object (in 3D Viewport or in Outliner)
  * View Sidebar ("View" --> "Toggle Sidebar" or press "N" key in 3D Viewport)
  * Select "SwiftBlock" tab in the Sidebar

Quickstart
----------

* Install and start Blender as specified above
* In Blender, select the default Cube object in 3D Viewport or in Outliner
* Make add-on panels visible as described above
* Click *Initialize Object*
* Model block geometry in Blender
* Set Edge Parameters for each edge
* Optionally add projections and/or Boundary Patches
* Optionally preview blocks
* Press *Export* to save blockMeshDict to a case folder
* Run blockMesh OpenFOAM command in terminal to generate mesh

Panels and Settings
-------------------

SwiftBlock GUI consists of four panels: Block Method Settings, Edge
Settings, Projections and Boundary Patches.

.. image:: images/ui.png

Block Method Settings
^^^^^^^^^^^^^^^^^^^^^

This panel contains overall settings and tool buttons.
You can hover mouse cursor over fields to see tool tips for more
information.

.. image:: images/block_method_settings.png

* *Initialize Object* tool appears when a mesh object is selected
  Running the tool will intialize the selected object for SwiftBlock,
  enables Edit Mode, and reveals the rest of the GUI.
  **Note**: SwiftBlock tools are available only in Edit Mode.
* *Method* defines the block generation method. Default value is
  *BlockMeshMG*, which supports multi grading.
  **Note:** Currently no other methods are available. The source
  code also includes the original *blockMeshBodyFit* method, but is has
  not been upgraded/tested with Blender 2.8, so it is currently disabled.
* *Build* tool identifies the blocks from the current mesh.
  Blocks are listed in the panel window after building is completed.
  **Warning**: Bulding may take a long time for complex block systems.
* *Use Numba* option box enables Python Numba performance library.
  Numba compiles the Build tool into machine code, which decreases the
  time required for *Build*.
  **Note**: Numba requires installation of the Numba Python libraries
  into Blender. You can use similar installation procedure as
  `installation of VTK into Blender <https://github.com/tkeskita/BVtkNodes/blob/master/pip_install_vtk.md>`_.
  **Warning**: Not tested.
* *Preview* tool shows preview of the edges on the result block mesh.
  Preview requires that the OpenFOAM blockMesh utility is available in
  Blender. An error message is displayed if blockMesh command is not
  found. To make blockMesh available, you must start terminal command
  prompt, source OpenFOAM in the terminal, and start blender from the
  same terminal. Preview will automatically run *Build* tool if needed.
* *Export* tool saves blockMeshDict file into a case folder. The user
  is prompted to select the case folder. Any file name is ignored, only
  the directory matters.
* *Block list* contains the list of blocks identified by the *Build* tool.

  * Clicking a block selects and highlights the block in the 3D
    Viewport. Enable e.g. "Show whole scene transparent" option in
    the 3D Viewport header to see blocks inside.
  * Check box can be deselected to disable a block

* *Get Block from Selection* selects the block attached to the current
  selection.
* *Extrude Blocks (Retain Internal Edges)* is a special extrusion tool
  for Swift Block, which keeps the internal edges in extrusion.

Edge Settings
^^^^^^^^^^^^^

This panel is used to set parameter values and apply them on selected edges.

.. image:: images/edge_settings.png

* *Cells* specifies the number of divisions.
* *Start* and *End* refer to optional edge grading at the start and
  end of edges.

  * *x1* is the first cell length at the start of edge.
  * *x2* is the last cell length at the end of edge.
  * *r1* is the geometric boundary layer ratio of neighbor cell
    lengths at the start of edge. Values larger than 1.0 create grading.
  * *r2* is the geometric boundary layer ratio of neighbor cell
    lengths at the end of edge.

* *Set Params* tool applies the above parameter values to currently
  selected edges.
* *Get Params* tool gets the parameter values from active edge.
* *Select Group* tool adds edges in same edge group to selection. This
  is a convenience tool to select aligned or connected edges, to ease
  specification of consistent parameter values.
* *Flip Dir* tool flips the edge direction of selected edges.
* *Show Edge Directions* tool visualizes the edge directions by adding
  cones to edge centers.


Edge Groups
^^^^^^^^^^^

Edge Groups is a new panel which allows creation of Edge Groups,
similar to Vertex Groups in Blender.

* *Add (+)* will create a new edge group
* *Delete (-)* will remove the active edge group
* *Assign* will add the selected edges to active edge group
* *Remove* will remove the selected edges from the active edge group
* *Select* adds the edges in the active edge group into current edge selection
* *Deselect* removes currently selected edges from the active edge group

    
Projections
^^^^^^^^^^^

This panel contains settings for projecting edges to surfaces on other
mesh objects.

.. image:: images/projections.png

* *Icon* drop down menu specifies the projection object.
  **Note**: Projection object must be visible (not hidden) for
  projection to work correctly.
  **Note**: Object name must start with a letter and not a number,
  so that OpenFOAM interprets the result correctly. If object name
  starts with a number, you will get error like
  ``Expected a '(' or a '{' while reading List...``
* *Add* button will add the specified object as projection object and
  populates list of projected vertices, edges and faces.
* *Remove* button will remove all projections
* *Projection list* contains the projected vertices, edges and faces.

  * Clicking on a list row will highlight the item in 3D Viewport.
    Click *Return to SwiftBlock* button to return to GUI panel.
  * Click on the cross icon to remove a projection.

* *Automatic Edge Projection* select box will enable automatic
  snapping of edges to geometry.
* *Show Internal Faces* will highlight internal faces.


Boundary Patches
^^^^^^^^^^^^^^^^

Boundary Patches panel is used to specify boundary faces and their
types utilizing Blender material system. Patches are shown as a
list. Initially all faces are added to *default* boundary patch.

**Note**: Blender may add a default "Material" material. You can
remove it from the patch list unless you intend to use it.

.. image:: images/boundary_patches.png

* Clicking on list item will select and highlight the faces belonging
  to a boundary
* Double-clicking on item will edit the boundary name
* Clicking on the right column will open a drop-down menu, which
  allows to change the boundary patch type.
* New boundaries are created by selecting one or more faces and then
  click on the plus icon.
* Selected boundary is deleted by clicking on minus icon.
* *Assign* button will assign selected faces to a selected boundary patch

Feedback and Help
-----------------

If you're new to OpenFOAM, please see links at
https://holzmann-cfd.com/community/learn-openfoam,
https://openfoamwiki.net and
https://www.cfd-online.com/Forums/openfoam/.

File bug reports for the add-on in
`GitHub <https://github.com/tkeskita/swiftBlock/issues>`_.
Please ask for help for the add-on or discuss in the
`SwiftBlock thread on CFD-Online <https://www.cfd-online.com/Forums/openfoam-community-contributions/100604-swiftsnap-swiftblock-guis-openfoams-meshers.html>`_.

If you use this add-on, please star the project in GitHub!


Tutorial Example: Flow Around Sphere
------------------------------------

This example shows steps to create a block mesh around a sphere. This
tutorial was originally presented for the previous Blender version on
`Youtube <https://www.youtube.com/watch?v=V4Omjmm40GQ>`_.
The final Blender file is included in the
add-on source at *example/flow_around_sphere.blend*. **Note**: This
tutorial assumes that the user is familiar with mesh modelling
in Blender.

.. image:: images/flow_around_sphere.png

* Select the default Cube object and click on *Initialize Object* in
  SwiftBlock panel
* Select all vertices, run Swift Block operator *Extrude Blocks (Retain Internal Edges)* from
  either the button on the panel or
  the operator search menu by pressing F3 in the 3D Viewport, type
  name of operator, click operator name in the list. Finally,
  right-click to cancel moving. *Extrude Blocks (Retain Internal Edges)* creates face
  extrusion retaining internal edges.
* Scale exruded vertices by factor 3 using selection center or origin
  as pivot point. This positions 6 blocks around center cube block.
* Extrude the face in positive X direction by 12 m to create a
  block towards outlet.
* Extrude the face in negative X direction by 6 m to create another
  block towards the inlet.
* Click on *Build*, which creates 9 blocks
* Click on *block 0* in the block list to select and highlight the
  original cube block in the center, then disable that block by
  clicking on the check box next to block name, so that the inside of
  that block will not be meshed
* Go to Object Mode and add UV Sphere to origin
* Go back to Object Mode, select Cube object and go to Edit Mode to
  view SwiftBlock panels
* Click on *block 0* in block list to select center block faces.
* In Projections panel, the Sphere is automatically selected as the
  projection object. Click *Add* to add projections to Sphere. Check
  that the projection list includes the 6 center faces by clicking on
  the face items at the end of the list to highlight them.
* In order to preview mesh near sphere, you must disable one of the
  four outer central blocks. To do that, select one of the outer faces
  in the center piece, and click *Get Block from Selection* to
  identify the block. Then uncheck the box next to the block in the
  block list.
* Click on *Preview* to preview the default mesh, then return to SwiftBlock.
* To add grading towards the sphere, first select one of the diagonal edges
  inside, then click on *Select Group*, which will select all diagonal edges.
* Enter values to edge parameters: Cells: 20, x1: 0.01, r1: 1.2
* Then click on *Set Params* to assign those values to selected edges.
* Click on *Preview* to preview the graded mesh, then return to SwiftBlock.
* Enable the block that was disabled 6 steps ago.
* Name Boundary Patches by selecting face(s) for each patch and click
  on plus icon, then rename patch and change patch type:

  * inlet: face on negative X end, patch type: patch
  * outlet: face on positive X end, patch type: patch
  * wall_outer: other 12 outer faces, patch type: wall

* Finally rename default patch (which should now contain 6 internal
  faces) to wall_sphere.
* Save Blender file, then click on *Export* to export blockMeshDict
  into an OpenFOAM case folder
* Run OpenFOAM command *blockMesh* in case folder to create block
  volume mesh and inspect the result with e.g.
  `Paraview <https://www.paraview.org>`_


More examples
-------------

More examples can be found in the `example` folder of the add-on sources.

.. image:: images/naca_airfoil_mesh_preview.png

NACA airfoil example

.. image:: images/complex_block_with_elongations.png

Complex block example


OpenFOAM Trade Mark Notice
--------------------------

This offering is not approved or endorsed by OpenCFD Limited, producer
and distributor of the OpenFOAM software via www.openfoam.com, and
owner of the OPENFOAM® and OpenCFD® trade marks.
