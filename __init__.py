bl_info = {
    "name": "SwiftBlock",
    "author": "Karl-Johan Nogenmyr, Mikko Folkersma, Turo Valikangas, Tuomo Keskitalo",
    "version": (0, 4),
    "blender": (2, 80, 0),
    "location": "View_3D > Object > SwiftBlock",
    "description": "Creates OpenFOAM blockMeshDict block geometry definition file",
    "warning": "",
    "wiki_url": "https://github.com/tkeskita/swiftBlock",
    "tracker_url": "https://github.com/tkeskita/swiftBlock/issues",
    "category": "OpenFOAM"}

import bpy
import bmesh
import time
import importlib
from . import blockBuilder
importlib.reload(blockBuilder)
#from . import blender_utils
#importlib.reload(blender_utils)
from .utils import *
importlib.reload(utils)
from mathutils import Vector


# Property groups
# ---------------
# Note: Property groups must be registered immediately to avoid later error
# about "missing bl_rna attribute from 'RNAMetaPropGroup' instance
# (may not be registered)". This will generate warnings about
# registration failed for these classes when all classes are registered.
# TODO: Find elegant solution.

class SWIFTBLOCK_PG_BlockProperty(bpy.types.PropertyGroup):
    id: bpy.props.IntProperty()
    name: bpy.props.StringProperty()
    verts: bpy.props.IntVectorProperty(size = 8)
    enabled: bpy.props.BoolProperty(default=True)
    namedRegion: bpy.props.BoolProperty(default=False)
bpy.utils.register_class(SWIFTBLOCK_PG_BlockProperty)

class SWIFTBLOCK_PG_ProjectionProperty(bpy.types.PropertyGroup):
    type: bpy.props.StringProperty() #vert2surf,edge2surf,face2sur,edge2polyline
    id: bpy.props.IntProperty() #bmesh id
    ob: bpy.props.StringProperty()
bpy.utils.register_class(SWIFTBLOCK_PG_ProjectionProperty)

class SWIFTBLOCK_PG_EdgeGroupProperty(bpy.types.PropertyGroup):
    group_name: bpy.props.StringProperty()
    group_edges: bpy.props.StringProperty()
bpy.utils.register_class(SWIFTBLOCK_PG_EdgeGroupProperty)



# Object properties
# -----------------

bpy.types.Object.swiftBlock_isblockingObject = bpy.props.BoolProperty(default=False)
bpy.types.Object.swiftBlock_blocking_object = bpy.props.StringProperty(default="")
bpy.types.Object.swiftBlock_ispreviewObject = bpy.props.BoolProperty(default=False)
bpy.types.Object.swiftBlock_preview_object = bpy.props.StringProperty(default='')
bpy.types.Object.swiftBlock_direction_object = bpy.props.StringProperty(default="")
bpy.types.Object.swiftBlock_isdirectionObject = bpy.props.BoolProperty(default=False)

bpy.types.Object.swiftBlock_Mesher = bpy.props.EnumProperty(
    name="Blocking Method Selection",
    items = (
        ("blockMeshMG","blockMeshMG","Block Mesh (with Multigrading and Projections)", 1),
        # blockMeshBodyFit has not been upgraded/tested with Blender 2.8, disable for now
        # ("blockMeshBodyFit","blockMeshBodyFit","Body Fit Method (Requires blockMeshBodyFit)", 2),
    ),
    update=changeMesher)

# Blocking properties
bpy.types.Object.swiftBlock_blocks = bpy.props.CollectionProperty(type=SWIFTBLOCK_PG_BlockProperty)
bpy.types.Object.swiftBlock_block_index = bpy.props.IntProperty()
bpy.types.Object.swiftBlock_useNumba = bpy.props.BoolProperty(
    name="Use Numba",
    description="Option to Use Python Numba Performance Library (Must be Installed Separately)",
    default=False,
)

# Projection/snapping properties
bpy.types.Object.swiftBlock_projections = \
    bpy.props.CollectionProperty(type=SWIFTBLOCK_PG_ProjectionProperty)
bpy.types.Object.swiftBlock_projection_index = bpy.props.IntProperty()
bpy.types.Object.swiftBlock_Autosnap = bpy.props.BoolProperty(
    name="Automatic Edge Projection",
    description = "Option to Snap Lines Automatically from Geometry"
)
bpy.types.Object.swiftBlock_ShowInternalFaces = bpy.props.BoolProperty(
    name="Show Internal Faces",
    description = "Show Internal Faces",
    default=False, update=showInternalFaces
)
bpy.types.Object.swiftBlock_ProjectionObject = bpy.props.EnumProperty(
    name="Projection Object",
    items=getProjectionObjects, description = "Projection Object"
)
bpy.types.Object.swiftBlock_EdgeSnapObject = bpy.props.EnumProperty(
    name="Object",
    items=getProjectionObjects, description = "Projection Object"
)

# Mapping properties
bpy.types.Object.swiftBlock_MappingType = bpy.props.EnumProperty(
    name="",
    items = (("Geometric MG","Geometric MG","",1),
             ("Geometric","Geometric","",2),)
)

# bpy.types.Object.swiftBlock_Dx = bpy.props.FloatProperty(
#    name="dx", default=1, update=setCellSize, min=0)
bpy.types.Object.swiftBlock_Cells = bpy.props.IntProperty(
    name="Cells", default=10, min=1, description="Number of Cell Divisions for Edge")
bpy.types.Object.swiftBlock_x1 = bpy.props.FloatProperty(
    name="x1", default=0.1, description="First Cell Edge Length", min=0)
bpy.types.Object.swiftBlock_x2 = bpy.props.FloatProperty(
    name="x2", default=0.1, description="Last Cell Edge Length", min=0)
bpy.types.Object.swiftBlock_r1 = bpy.props.FloatProperty(
    name="r1", default=1.0, description="First Boundary Layer Geometric Ratio", min=1.0)
bpy.types.Object.swiftBlock_r2 = bpy.props.FloatProperty(
    name="r2", default=1.0, description="Last Boundary Layer Geometric Ratio", min=1.0)
bpy.types.Object.swiftBlock_Ratio = bpy.props.FloatProperty(
    name="Ratio", default=1.0, description="Ratio of First Cell Length to Last Cell Length", min=0)
bpy.types.Object.swiftBlock_SearchLength = bpy.props.FloatProperty(
    name="Search Length", default=1.0, description="Search Length", min=0)
# bpy.types.Object.swiftBlock_ShowEdgeDirections = bpy.props.BoolProperty(
#    name="Show directions", default=True, update = updateEdgeDirections, description="Show edge directions?")

# Boundary condition properties
bpy.types.Object.swiftBlock_bcTypeEnum = bpy.props.EnumProperty(
    items = [('wall', 'wall', 'Defines the patch as wall'),
             ('patch', 'patch', 'Defines the patch as generic patch'),
             ('empty', 'empty', 'Defines the patch as empty'),
             ('symmetry', 'symmetry', 'Defines the patch as symmetry'),
    ],
    name = "Patch Type"
)
bpy.types.Object.swiftBlock_patchName = bpy.props.StringProperty(
    name = "Patch Name",
    description = "Specify Name of Patch",
    default = "default"
)
bpy.types.Object.swiftBlock_boundary_index = bpy.props.IntProperty(
    description = "Boundary Patch Index",
    update = selectActiveBoundary
)
bpy.types.Material.boundary_type = bpy.props.EnumProperty(
    items = [('wall', 'wall', '', 1),
             ('patch', 'patch', '', 2),
             ('empty', 'empty', '', 3),
             ('symmetry', 'symmetry', '', 4),
    ],
    name = "Patch Type",
    description = "Boundary Patch Type"
)

# Edge group properties
bpy.types.Object.swiftBlock_edgegroups = \
    bpy.props.CollectionProperty(type=SWIFTBLOCK_PG_EdgeGroupProperty)

bpy.types.Object.swiftBlock_edgegroup_index = bpy.props.IntProperty()

# Main class definitions
# ----------------------

# Create the swiftBlock panel
class VIEW3D_PT_SwiftBlockPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "SwiftBlock"
    bl_label = "SwiftBlock"

    def draw(self, context):
        ob = context.active_object
        if not ob:
            return
        box = self.layout.column(align=True)

        if ob.swiftBlock_ispreviewObject:
            box = self.layout.box()
            box.operator("swift_block.activate_blocking").hide = True
        elif ob.swiftBlock_blocking_object and ob.name != ob.swiftBlock_blocking_object:
            box = self.layout.box()
            box.operator("swift_block.activate_blocking").hide = False
        elif not ob.swiftBlock_isblockingObject and ob.type == 'MESH':
            box.operator("swift_block.init_blocking")

        elif context.active_object and bpy.context.active_object.mode == "EDIT":

            box = self.layout.box()
            box.label(text="Block Method Settings")
            box.alignment = 'RIGHT'
            box.prop(ob, "swiftBlock_Mesher", text="Method")
            split = box.split(factor=0.5)
            split.operator("swift_block.build_blocking")
            split.prop(ob, "swiftBlock_useNumba")

            split = box.split()
            split.operator("swift_block.preview_mesh")
            split = split.split()
            split.operator("swift_block.write_mesh")
            box.template_list("SWIFTBLOCK_UL_block_items", "", ob, "swiftBlock_blocks", ob, "swiftBlock_block_index", rows=2)
            box.operator("swift_block.get_block")

            box = self.layout.box()
            box.label(text="Edge Settings")
            # box.prop(ob, "swiftBlock_MappingType")
            split = box.split()
            split.prop(ob, "swiftBlock_Cells")
            # split.operator("swift_block.set_cellsize")
            if ob.swiftBlock_Mesher == "blockMeshMG":
                split = box.split()
                col = split.column()
                col.label(text="Start")
                col.prop(ob, "swiftBlock_x1")
                col.prop(ob, "swiftBlock_r1")
                col = split.column()
                col.label(text="End")
                col.prop(ob, "swiftBlock_x2")
                col.prop(ob, "swiftBlock_r2")
            elif ob.swiftBlock_Mesher == "blockMeshBodyFit":
                split.prop(ob, "swiftBlock_Ratio")
            split = box.split()
            split.operator("swift_block.set_edge")
            split.operator("swift_block.get_edge")
            split = box.split()
            split.operator("swift_block.edge_select_parallel")
            split.operator("swift_block.flip_edges")
            if 'Edge_directions' in bpy.data.objects:
                box.operator("swift_block.draw_edge_directions",text='Show edge directions',emboss=False,icon="CHECKBOX_HLT").show=False
            else:
                box.operator("swift_block.draw_edge_directions",text='Show edge directions',emboss=False,icon="CHECKBOX_DEHLT").show=True
            #Edge grouping control panel
            box = self.layout.box()
            box.label(text="Edge groups")
            row = box.row()
            row.template_list("SWIFTBLOCK_UL_edgegroup_items", "", ob, "swiftBlock_edgegroups", ob, "swiftBlock_edgegroup_index", rows=max(len(ob.swiftBlock_edgegroups),2))
            col = row.column(align=True)
            col.operator("swift_block.edgegroups_action",  text="Add").action = 'ADD'
            col.operator("swift_block.edgegroups_action",  text="Remove").action = 'REMOVE'
            col.operator("swift_block.edgegroups_action", text="Select").action = 'SELECT'

            box = self.layout.box()
            box.label(text="Projections")
            split = box.split()
            split.prop(ob, "swiftBlock_ProjectionObject", text="", icon="OUTLINER_OB_SURFACE")
            split.operator("swift_block.add_projections", text="Add")
            split.operator("swift_block.remove_projections", text="Remove")
            if ob.swiftBlock_Mesher == "blockMeshBodyFit":
                box.prop(ob, 'swiftBlock_SearchLength')
            box.template_list("SWIFTBLOCK_UL_projection_items", "", ob, "swiftBlock_projections", ob, "swiftBlock_projection_index", rows=2)
            if ob.swiftBlock_Autosnap:
                split = box.split(factor=0.1)
                split.prop(ob, "swiftBlock_Autosnap", text="")
                split = split.split(factor=0.9)
                split.prop(ob, "swiftBlock_EdgeSnapObject", text="")
                if ob.swiftBlock_EdgeSnapObject != "":
                    o = split.operator("swift_block.activate_snap",text="",emboss=False,icon="OBJECT_DATA")
                    o.ob = ob.swiftBlock_EdgeSnapObject
            else:
                box.prop(ob, "swiftBlock_Autosnap")
            box.prop(ob,"swiftBlock_ShowInternalFaces")


            box = self.layout.box()
            box.label(text="Boundary Patches")
            row = box.row()
            row.template_list("SWIFTBLOCK_UL_boundary_items", "", ob.data, "materials", ob, "swiftBlock_boundary_index", rows=2)
            col = row.column(align=True)
            col.operator("swift_block.boundaries_action", icon='ZOOM_IN', text="").action = 'ADD'
            col.operator("swift_block.boundaries_action", icon='ZOOM_OUT', text="").action = 'REMOVE'
            row = self.layout.row()
            row.operator("swift_block.boundaries_action", text="Assign").action = 'ASSIGN'

# For the lists in GUI
class SWIFTBLOCK_UL_block_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.9)
        block = context.active_object.swiftBlock_blocks[index]
        name = block.name + ' %d'%index
        c = split.operator("swift_block.edit_block", text=name, emboss=False, icon="UV_FACESEL")
        c.blockid = index
        c.name = block.name

        if block.enabled:
            c = split.operator("swift_block.enable_block", text='',emboss=False,icon="CHECKBOX_HLT").blockid = index
        else:
            c = split.operator("swift_block.enable_block", text='', emboss=False,icon="CHECKBOX_DEHLT").blockid = index

class SWIFTBLOCK_UL_boundary_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        mat = data.materials[index]
        split = layout.split(factor=0.2)
        split.prop(item, "diffuse_color", text='')
        split.prop(item, "name", text='', emboss = False)
        split.prop(item, "boundary_type", text='', emboss = False)

class SWIFTBLOCK_OT_BoundariesAction(bpy.types.Operator):
    bl_idname = "swift_block.boundaries_action"
    bl_label = "Boundary Action"
    bl_description = "Runs Action on Selected Boundary"

    action: bpy.props.EnumProperty(
        items=(
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
            ('ASSIGN', "Assign", ""),
        )
    )

    def invoke(self, context, event):

        ob = context.active_object
        bm = bmesh.from_edit_mesh(ob.data)

        if self.action == 'REMOVE':
            mat_name = ob.active_material.name
            ob.data.materials.pop(index=ob.active_material_index)
            if not bpy.data.materials[mat_name].users:
                bpy.data.materials.remove(bpy.data.materials[mat_name])

        elif self.action == 'ASSIGN':
            for f in bm.faces:
                if f.select:
                    f.material_index = ob.swiftBlock_boundary_index
            ob.data.update()

        if self.action == 'ADD':
            name = 'default'
            mat = bpy.data.materials.new(name)
            color = patchColor(len(ob.data.materials))
            mat.diffuse_color = color
            ob.data.materials.append(mat)
            material_index = len(ob.data.materials) - 1

            for f in bm.faces:
                if f.select:
                    f.material_index = material_index
            ob.swiftBlock_boundary_index = material_index
            ob.active_material_index = material_index
            ob.data.update()

        return {"FINISHED"}

class SWIFTBLOCK_UL_projection_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.4)
        proj = context.active_object.swiftBlock_projections[index]
        if proj.type == 'vert2surf':
            icon = "VERTEXSEL"
        elif proj.type == 'edge2surf':
            icon = "EDGESEL"
        elif proj.type == 'face2surf':
            icon = "FACESEL"
        c = split.operator("swift_block.get_projection", text='{}{}'.format(proj.type[0],proj.id), emboss=False, icon=icon)
        c.type = proj.type
        c.id = proj.id
        split = split.split(factor=0.6)
        c = split.operator("swift_block.activate_snap", text=proj.ob, emboss=False, icon="OBJECT_DATA")
        c.ob = proj.ob
        c = split.operator("swift_block.remove_projection", text='', emboss = False, icon='X')
        c.proj_id = index


class SWIFTBLOCK_UL_edgegroup_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        # eg = context.active_object.swiftBlock_edgegroups[index]
        layout.prop(item, "name", text='', emboss = False)


#Edge grouping function for creating, removing and selecting edges in groups
class SWIFTBLOCK_OT_EdgeGroupsAction(bpy.types.Operator):
    bl_idname = "swift_block.edgegroups_action"
    bl_label = "Edge group action"
    bl_description = "Runs Action on selected edges"

    action: bpy.props.EnumProperty(
        items=(
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", ""),
            ('SELECT', "Select", ""),
        )
    )

    def invoke(self, context, event):
        ob = context.active_object
        bm = bmesh.from_edit_mesh(ob.data)
        egLayer = bm.edges.layers.int.get("edgegroup")
        index = ob.swiftBlock_edgegroup_index

        if self.action == 'REMOVE':
            ob.swiftBlock_edgegroups.remove(index)
            for e in bm.edges:
                if e[egLayer] == index:
                    e[egLayer] = -1
                elif e[egLayer] > index:
                    e[egLayer] -= 1

        if self.action == 'ADD':
            index = len(ob.swiftBlock_edgegroups)
            edgesSelected = False
            for e in bm.edges:
                if e.select:
                    e[egLayer] = len(ob.swiftBlock_edgegroups)
                    edgesSelected = True
            if edgesSelected:
                neweg = ob.swiftBlock_edgegroups.add()
                neweg.name = 'EdgeGroup_{}'.format(index)
        if self.action == 'SELECT':
            for e in bm.edges:
                if e[egLayer] == index:
                    e.select = True
        ob.data.update()
        return {"FINISHED"}

# Initialize all the bmesh layer properties for the blocking object
class SWIFTBLOCK_OT_InitBlocking(bpy.types.Operator):
    bl_idname = "swift_block.init_blocking"
    bl_label = "Initialize Object"
    bl_description = "Initializes the Active Object for SwiftBlock"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        print("initialize BMesh")

        bpy.ops.object.mode_set(mode='EDIT')
        ob = bpy.context.active_object
        bm = bmesh.from_edit_mesh(ob.data)

        bm.edges.layers.string.new("type")
        bm.edges.layers.float.new("x1")
        bm.edges.layers.float.new("x2")
        bm.edges.layers.float.new("r1")
        bm.edges.layers.float.new("r2")
        bm.edges.layers.float.new("dx")
        bm.edges.layers.float.new("ratio")
        bm.edges.layers.int.new("cells")
        bm.edges.layers.int.new("groupid")
        bm.edges.layers.int.new("modtime")
        bm.edges.layers.int.new("edgegroup")

        bm.faces.layers.int.new('pos') # block number on positive side of the face, -1 boundary face
        bm.faces.layers.int.new('neg') # block number on negative side of the face, -1 boundary face
        bm.faces.layers.int.new('enabled') # 0 = disabled, 1 = boundary face, 2 = internal face

        ob.swiftBlock_blocks.clear()
        ob.swiftBlock_projections.clear()
        # ob.swiftBlock_edge_groups.clear()
        bpy.ops.swift_block.boundaries_action("INVOKE_DEFAULT",action='ADD')

        ob.swiftBlock_isblockingObject = True
        ob.data.update()
        ob.show_all_edges = True
        ob.show_wire = True
        return {"FINISHED"}

# Blocking and previewing operators
# Automatical block detection.
class SWIFTBLOCK_OT_BuildBlocking(bpy.types.Operator):
    bl_idname = "swift_block.build_blocking"
    bl_label = "Build"
    bl_description = "Generates Blocks from Mesh (Main Routine)"
    bl_options = {"UNDO"}

    def invoke(self, context, event):
        ob = context.active_object
        bm = bmesh.from_edit_mesh(ob.data)

        verts = []
        edges = []

        for v in bm.verts:
            verts.append(v.co)
        for e in bm.edges:
            edges.append([e.verts[0].index,e.verts[1].index])

        disabled = [] #not needed anymore

        print('Beginning automatic block detection')
        stime = time.time()
        log, block_verts, block_edges, face_info, all_edges, faces_as_list_of_nodes = blockBuilder.blockFinder(edges, verts, disabled = disabled, numba = ob.swiftBlock_useNumba)
        print('Found {} blocks in {:.1f} seconds, used Numba={}'.format(len(block_verts), time.time()-stime,ob.swiftBlock_useNumba))


        ob.swiftBlock_blocks.clear()
        for i,bv in enumerate(block_verts):
            b = ob.swiftBlock_blocks.add()
            b.id = i
            b.name = 'block'#_{}'.format(i)
            b.verts = bv

        groupl = bm.edges.layers.int.get('groupid')
        bm.verts.ensure_lookup_table()

        for i, g in enumerate(block_edges):
            for e in g:
                bme = bm.edges.get((bm.verts[e[0]],bm.verts[e[1]]))
                bme[groupl] = i

        # A bug in face_info when there are o-grids. The block indices after o-grid block have to be decreased by one.
        replace_ids = dict()
        block_ids = []
        for key in face_info.keys():
            block_ids.extend(face_info[key]['pos'])
            block_ids.extend(face_info[key]['neg'])
        block_ids = sorted(set(block_ids))
        nblocks = len(ob.swiftBlock_blocks)-1

        decrease = []
        if nblocks < max(block_ids):
            for i in range(max(block_ids)):
                if i not in block_ids:
                    decrease.append(i)

        negl = bm.faces.layers.int.get('neg')
        posl = bm.faces.layers.int.get('pos')
        enabledl = bm.faces.layers.int.get('enabled')

        block_faces = []

        for key, value in face_info.items():
            # probably a bug, some extra faces which do not belong to any block
            if not value['neg'] and not value['pos']:
                continue
            verts = [bm.verts[v] for v in faces_as_list_of_nodes[key]]
            f = bm.faces.get(verts)
            if not f:
                f = bm.faces.new(verts)
            f[enabledl] = -1
            block_faces.append(f)
            if value['pos']:
                f[posl] = value['pos'][0]
                dec = sum(x < f[posl] for x in decrease)
                f[posl] -= dec
            else:
                f[posl] = -1
            if value['neg']:
                f[negl] = value['neg'][0]
                dec = sum(x < f[negl] for x in decrease)
                f[negl] -= dec
            else:
                f[negl] = -1

        for f in bm.faces:
            if not f in block_faces:
                bm.faces.remove(f)


        bpy.ops.object.mode_set(mode='OBJECT')

        edgeDirections = utils.getEdgeDirections(block_verts, block_edges)

        ob = bpy.context.active_object
        edgelist = dict()
        for e in ob.data.edges:
            edgelist[(e.vertices[0],e.vertices[1])] = e.index
        for ed in edgeDirections:
            # consistentEdgeDirs(ed)
            for e in ed:
                if (e[0],e[1]) not in edgelist:
                    ei = ob.data.edges[edgelist[(e[1],e[0])]]
                    (e0, e1) = ei.vertices
                    ei.vertices = (e1, e0)
        bpy.ops.object.mode_set(mode='EDIT')
        updateProjections(ob)
        hideFacesEdges(ob, ob.swiftBlock_ShowInternalFaces)
        bpy.ops.swift_block.draw_edge_directions('INVOKE_DEFAULT',show=False)
        self.report({'INFO'}, "Number of blocks: {}".format(len(block_verts)))
        return {"FINISHED"}


class SWIFTBLOCK_OT_PreviewMesh(bpy.types.Operator):
    bl_idname = "swift_block.preview_mesh"
    bl_label = "Preview"
    bl_description = "Preview the Blocking Result"
    bl_options = {"UNDO"}

    filename: bpy.props.StringProperty(default='')

    def invoke(self, context, event):
        ob = context.active_object
        mesh, cells = writeMesh(ob)
        points, faces = mesh.runMesh()
        if points == []:
            self.report({'ERROR'}, "blockMesh command not found! Preview is unavailable. Source OpenFOAM in terminal and start Blender from that terminal to enable previewing.")
        else:
            self.report({'INFO'}, "Cells in mesh: " + str(cells))
        blender_utils.previewMesh(ob, points, faces)
        return {"FINISHED"}

class SWIFTBLOCK_OT_WriteMesh(bpy.types.Operator):
    bl_idname = "swift_block.write_mesh"
    bl_label = "Export"
    bl_description = "Generates OpenFOAM Files to a Case Folder"

    filepath: bpy.props.StringProperty(subtype='DIR_PATH')
    # filepath = bpy.props.StringProperty(
            # name="File Path",
            # description="Filepath used for exporting the file",
            # maxlen=1024,
            # subtype='FILE_PATH',
            # default='/opt',
            # )
    check_existing: bpy.props.BoolProperty(
            name="Check Existing",
            description="Check and warn on overwriting existing files",
            default=True,
            options={'HIDDEN'},
            )

    # use_filter_folder = True

    def invoke(self, context, event):
        bpy.context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        ob = context.active_object
        mesh, cells = writeMesh(ob, self.filepath)
        bpy.ops.object.mode_set(mode='EDIT')
        self.report({'INFO'}, "Cells in mesh: " + str(cells))
        return {"FINISHED"}

class SWIFTBLOCK_OT_ActivateBlocking(bpy.types.Operator):
    bl_idname = "swift_block.activate_blocking"
    bl_label = "Return to SwiftBlock"
    bl_description = "Go Back to SwiftBlock Settings"
    bl_options = {"UNDO"}

    hide: bpy.props.BoolProperty()

    def invoke(self, context, event):
        ob = context.active_object
        bob = bpy.data.objects[ob.swiftBlock_blocking_object]
        blender_utils.activateObject(bob, self.hide)
        return {'FINISHED'}

class SWIFTBLOCK_OT_GetBlock(bpy.types.Operator):
    """Get block from selection"""
    bl_idname = "swift_block.get_block"
    bl_label = "Get Block from Selection"
    bl_description = "Identifies the Block from Active Selection"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        ob = bpy.context.active_object
        bm = bmesh.from_edit_mesh(ob.data)
        selection = []
        for v in bm.verts:
            if v.select:
                selection.append(v.index)
        block = False
        occs = []
        for b in ob.swiftBlock_blocks:
            occ = [v in selection for v in b.verts].count(True)
            if occ == 8:
                block = b
                break
            else:
                occs.append(occ)
        if not block:
            max_occ = max(enumerate(occs), key=lambda x:x[1])[0]
            block = ob.swiftBlock_blocks[max_occ]
        if not block:
            self.report({'INFO'}, "No block found with selected vertices")
            return {'CANCELLED'}
        bpy.ops.swift_block.edit_block('INVOKE_DEFAULT', blockid=block.id, name = block.name )
        return {'FINISHED'}

class SWIFTBLOCK_OT_EditBlock(bpy.types.Operator):
    bl_idname = "swift_block.edit_block"
    bl_label = "Select Block"
    bl_description = "Selects Block for Editing"
    bl_options = {'REGISTER', 'UNDO'}


    blockid: bpy.props.IntProperty(name='id')
    namedRegion: bpy.props.BoolProperty(name='Named region', default = False)
    name: bpy.props.StringProperty(name='name')

    def draw(self, context):
        ob = context.active_object
        if not ob.swiftBlock_blocks[self.blockid].enabled:
            return
        col = self.layout.column(align = True)
        # col.prop(self, "enabled")
        # split = col.split(factor=0.1, align=True)
        # col = split.column()
        col.prop(self, "namedRegion")
        if self.namedRegion:
            # col = split.column()
            col.prop(self, "name")

    # this could be used to select multiple blocks
    def invoke(self, context, event):
        ob = context.active_object
        ob.swiftBlock_block_index = self.blockid
        if event.shift:
            self.shiftDown = True
        else:
            self.shiftDown = False
        self.execute(context)
        return {'FINISHED'}

    def execute(self, context):
        bpy.ops.mesh.select_all(action="DESELECT")
        ob = context.active_object
        ob.swiftBlock_blocks[self.blockid].name = self.name
        ob.swiftBlock_blocks[self.blockid].namedRegion = self.namedRegion
        # OK to remove? ob = context.active_object

        verts = ob.swiftBlock_blocks[self.blockid].verts

        bm = bmesh.from_edit_mesh(ob.data)
        bm.verts.ensure_lookup_table()
        for v in verts:
            bm.verts[v].select = True
        for e in bm.edges:
            if e.verts[0].select and e.verts[1].select:
                e.select = True
        for f in bm.faces:
            if len(f.verts) == 4 and sum([v.select for v in f.verts]) == 4:
                f.select = True
        ob.data.update()
        return {'FINISHED'}

class SWIFTBLOCK_OT_EnableBlock(bpy.types.Operator):
    bl_idname = "swift_block.enable_block"
    bl_label = "Include in Build Blocking"
    bl_description = "Option to Include This Block in Build Blocking"

    blockid: bpy.props.IntProperty()

    def execute(self, context):
        ob = context.active_object
        block = ob.swiftBlock_blocks[self.blockid]
        ob.swiftBlock_block_index = self.blockid

        if block.enabled:
            block.enabled = False
        else:
            block.enabled = True
        # repair_blockFacesEdges(ob)
        hideFacesEdges(ob)

        return {'FINISHED'}

# Mapping operators

# Change the layer properties of currently selected edges
class SWIFTBLOCK_OT_SetEdge(bpy.types.Operator):
    """Set mapping for the edge"""
    bl_idname = "swift_block.set_edge"
    bl_label = "Set Params"
    bl_description = "Set Parameters for Currently Selected Edges"
    bl_options = {"UNDO"}

    def execute(self, context):
        ob = context.active_object
        if not ob.swiftBlock_blocks:
            bpy.ops.swift_block.build_blocking('INVOKE_DEFAULT')

        bm = bmesh.from_edit_mesh(ob.data)
        typel = bm.edges.layers.string.get('type')
        cellsl = bm.edges.layers.int.get('cells')
        x1l = bm.edges.layers.float.get('x1')
        x2l = bm.edges.layers.float.get('x2')
        r1l = bm.edges.layers.float.get('r1')
        r2l = bm.edges.layers.float.get('r2')
        rl = bm.edges.layers.float.get('ratio')
        groupl = bm.edges.layers.int.get('groupid')
        timel = bm.edges.layers.int.get('modtime')

        for e in bm.edges:
            if e.select:
                e[typel] = str.encode(ob.swiftBlock_MappingType)
                e[cellsl] = ob.swiftBlock_Cells
                e[timel] = time.time()
                if ob.swiftBlock_MappingType == "Geometric MG":
                    e[x1l] = ob.swiftBlock_x1
                    e[x2l] = ob.swiftBlock_x2
                    e[r1l] = ob.swiftBlock_r1
                    e[r2l] = ob.swiftBlock_r2
                elif ob.swiftBlock_MappingType == "Geometric":
                    e[rl] = ob.swiftBlock_Ratio
        return {'FINISHED'}

class SWIFTBLOCK_OT_GetEdge(bpy.types.Operator):
    bl_idname = "swift_block.get_edge"
    bl_label = "Get Params"
    bl_description = "Get Parameter Values from Active Edge"
    bl_options = {"UNDO"}

    def execute(self, context):
        ob = context.active_object
        if not ob.swiftBlock_blocks:
            bpy.ops.swift_block.build_blocking('INVOKE_DEFAULT')

        bm = bmesh.from_edit_mesh(ob.data)
        typel = bm.edges.layers.string.get('type')
        x1l = bm.edges.layers.float.get('x1')
        x2l = bm.edges.layers.float.get('x2')
        r1l = bm.edges.layers.float.get('r1')
        r2l = bm.edges.layers.float.get('r2')
        cellsl = bm.edges.layers.int.get('cells')

        for e in bm.edges:
            if e.select:
                # e[typel] = str.encode(ob.swiftBlock_MappingType)
                 ob.swiftBlock_Cells = e[cellsl]
                 ob.swiftBlock_x1 = e[x1l]
                 ob.swiftBlock_x2 = e[x2l]
                 ob.swiftBlock_r1 = e[r1l]
                 ob.swiftBlock_r2 = e[r2l]
        return {'FINISHED'}

class SWIFTBLOCK_OT_SetCellSize(bpy.types.Operator):
    """Calculates the number of cells from maximum cell size"""
    bl_idname = "swift_block.set_cellsize"
    bl_label = "Set Cell Size"
    bl_description = "Set Cell Size"
    bl_options = {"UNDO"}

    def execute(self, context):
        ob = context.active_object
        bm = bmesh.from_edit_mesh(ob.data)
        typel = bm.edges.layers.string.get('type')
        x1l = bm.edges.layers.float.get('x1')
        x2l = bm.edges.layers.float.get('x2')
        r1l = bm.edges.layers.float.get('r1')
        r2l = bm.edges.layers.float.get('r2')
        cellsl = bm.edges.layers.int.get('cells')
        verts = [v.co for v in bm.verts]
        edges = [(e.verts[0].index, e.verts[1].index) for e in bm.edges]

        if ob.swiftBlock_Autosnap and ob.swiftBlock_EdgeSnapObject:
            polyLines, polyLinesPoints, lengths = getPolyLines(verts, edges, ob)
        else:
            polyLines = []
            lengths = [[]]


        for e in bm.edges:
            if e.select:
                ev = list([e.verts[0].index,e.verts[1].index])
                if ev in lengths[0]:
                    ind = lengths[0].index(ev)
                    L = lengths[1][ind]
                else:
                    L = (e.verts[0].co-e.verts[1].co).length

                e[typel] = str.encode(ob.swiftBlock_MappingType)
                N=utils.getCells(ob.swiftBlock_x1,ob.swiftBlock_x2,ob.swiftBlock_r1,ob.swiftBlock_r2,L,ob.swiftBlock_Dx)
                e[cellsl] = N
                e[x1l] = ob.swiftBlock_x1
                e[x2l] = ob.swiftBlock_x2
                e[r1l] = ob.swiftBlock_r1
                e[r2l] = ob.swiftBlock_r2
                print(N)
        return {'FINISHED'}

    filename = bpy.props.StringProperty(default='')

class SWIFTBLOCK_OT_EdgeSelectParallel(bpy.types.Operator):
    bl_idname = "swift_block.edge_select_parallel"
    bl_label = "Select Group"
    bl_description = "Selects All Edges in Active Edge Group"

    def execute(self, context):
        ob = context.active_object
        bm = bmesh.from_edit_mesh(ob.data)
        groupl = bm.edges.layers.int.get('groupid')
        for e in bm.edges:
            if e.select:
                groupid = e[groupl]
                for i in bm.edges:
                    if i[groupl] == groupid:
                        i.select = True
        ob.data.update()
        return {'FINISHED'}

class SWIFTBLOCK_OT_FlipEdges(bpy.types.Operator):
    """Flips parallel edges, select only one edge per group"""
    bl_idname = "swift_block.flip_edges"
    bl_label = "Flip Dir"
    bl_description = "Flip Edge Direction"

    def execute(self, context):
        ob = context.active_object
        bm = bmesh.from_edit_mesh(ob.data)
        groupl = bm.edges.layers.int.get('groupid')
        flip_edges = []
        for e in bm.edges:
            if e.select:
                groupid = e[groupl]
                for i in bm.edges:
                    if i[groupl] == groupid:
                        flip_edges.append(i.index)
                break
        bpy.ops.object.mode_set(mode='OBJECT')
        for fe in flip_edges:
            e = ob.data.edges[fe]
            (e0,e1) = e.vertices
            e.vertices = (e1,e0)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.swift_block.draw_edge_directions('INVOKE_DEFAULT',show=False)
        return {'FINISHED'}

class GetBlock(bpy.types.Operator):
    "Get block from selection"
    bl_idname = "get.block"
    bl_label = "Get block"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        ob = bpy.context.active_object
        bm = bmesh.from_edit_mesh(ob.data)
        selection = []
        for v in bm.verts:
            if v.select:
                selection.append(v.index)
        block = False
        occs = []
        for b in ob.blocks:
            occ = [v in selection for v in b.verts].count(True)
            if occ == 8:
                block = b
                break
            else:
                occs.append(occ)
        if not block:
            max_occ = max(enumerate(occs), key=lambda x:x[1])[0]
            block = ob.blocks[max_occ]
        if not block:
            self.report({'INFO'}, "No block found with selected vertices")
            return {'CANCELLED'}
        bpy.ops.edit.block('INVOKE_DEFAULT', blockid=block.id, name = block.name )
        return {'FINISHED'}

# Projection operators
# TODO Projections are saved to a Blender CollectionProperty. At the
# moment if verts, edges or faces have been deleted, the id might not be
# up to date anymore. It would make sense to save the projections to bmesh
# layer.
class SWIFTBLOCK_OT_GetProjection(bpy.types.Operator):
    bl_idname = "swift_block.get_projection"
    bl_label = "Get Projection"
    bl_description = "Get Projection"

    id: bpy.props.IntProperty()
    type: bpy.props.StringProperty()

    def invoke(self, context, event):
        if not event.shift:
            bpy.ops.mesh.select_all(action='DESELECT')
        self.execute(context)
        return {'FINISHED'}


    def execute(self, context):
        ob = context.active_object
        bm = bmesh.from_edit_mesh(ob.data)
        if self.type == 'vert2surf':
            bm.verts.ensure_lookup_table()
            bm.verts[self.id].select = True
        elif self.type == 'edge2surf':
            bm.edges[self.id].select = True
        elif self.type == 'face2surf':
            bm.faces[self.id].select = True
        ob.data.update()
        return {'FINISHED'}

class SWIFTBLOCK_OT_AddProjections(bpy.types.Operator):
    bl_idname = "swift_block.add_projections"
    bl_label = "Project to Selected Object"
    bl_description = "Project to Selected Object"
    bl_options = {"REGISTER","UNDO"}

    pob: bpy.props.EnumProperty(name="Projection Object",
            items=getProjectionObjects, description = "Projection Object")

    verts: bpy.props.BoolProperty(default=True)
    edges: bpy.props.BoolProperty(default=True)
    faces: bpy.props.BoolProperty(default=True)

    def invoke(self, context, event):
        ob = context.active_object
        self.pob = ob.swiftBlock_ProjectionObject
        self.added = 1
        return self.execute(context)

    def execute(self, context):
        def projectionExists(ob, ptype, index, pob):
            for p in ob.swiftBlock_projections:
                if p.type == ptype and p.id == index and p.ob == pob:
                    return True
            return False
        def addProjection(ptype, index):
            for p in ob.swiftBlock_projections:
                if p.type == ptype and p.id == index and p.ob == self.pob:
                    return
            newp = ob.swiftBlock_projections.add()
            newp.type = ptype
            newp.id = index
            newp.ob = self.pob
            self.added += 1

        ob = context.active_object
        bm = bmesh.from_edit_mesh(ob.data)

        if not self.pob:
            return {"CANCELLED"}

        np = len(ob.swiftBlock_projections)
        for i in range(self.added):
            ob.swiftBlock_projections.remove(np-i)

        for v in bm.verts:
            if v.select and self.verts:
                addProjection('vert2surf', v.index)

        for e in bm.edges:
            if e.select and self.edges:
                addProjection('edge2surf', e.index)

        for f in bm.faces:
            if f.select and self.faces:
                addProjection('face2surf', f.index)
        return {"FINISHED"}

class SWIFTBLOCK_OT_RemoveProjection(bpy.types.Operator):
    bl_idname = "swift_block.remove_projection"
    bl_label = "Remove Projection"
    bl_description = "Remove Projection"
    bl_options = {"UNDO"}

    proj_id: bpy.props.IntProperty(default = -1)

    def execute(self, context):
        ob = context.active_object
        if self.proj_id != -1:
            ob.swiftBlock_projections.remove(self.proj_id)
        return {"FINISHED"}

class SWIFTBLOCK_OT_RemoveProjections(bpy.types.Operator):
    bl_idname = "swift_block.remove_projections"
    bl_label = "Remove Projections"
    bl_description = "Remove All Projections"
    bl_options = {"UNDO"}


    def execute(self, context):
        ob = context.active_object
        bm = bmesh.from_edit_mesh(ob.data)

        remove_projections = []

        for v in bm.verts:
            if v.select:
                for i,p in enumerate(ob.swiftBlock_projections):
                    if p.type == 'vert2surf' and p.id == v.index:
                        remove_projections.append(i)
        for e in bm.edges:
            if e.select:
                for i,p in enumerate(ob.swiftBlock_projections):
                    if p.type == 'edge2surf' and p.id == e.index:
                        remove_projections.append(i)
        for f in bm.faces:
            if f.select:
                for i,p in enumerate(ob.swiftBlock_projections):
                    if p.type == 'face2surf' and p.id == f.index:
                        remove_projections.append(i)
        remove_projections = reversed(sorted(remove_projections))
        for i in remove_projections:
            ob.swiftBlock_projections.remove(i)
        return {"FINISHED"}

class SWIFTBLOCK_OT_ActivateSnap(bpy.types.Operator):
    bl_idname = "swift_block.activate_snap"
    bl_label = "Activate Snapping Object"
    bl_description = "Activate Snapping Object"
    bl_options = {"UNDO"}

    ob: bpy.props.StringProperty()


    def invoke(self, context, event):
        ob = context.active_object
        pob = bpy.data.objects[self.ob]
        pob.swiftBlock_blocking_object = ob.name
        blender_utils.activateObject(pob, False)
        return {'FINISHED'}

class SWIFTBLOCK_OT_EdgetoPolyLine(bpy.types.Operator):
    bl_idname = "swift_block.edge_to_polyline"
    bl_label = "Project Edge to Polyline"
    bl_description = "Project Edge to Polyline"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context, event):
        self.ob = context.active_object
        bm = bmesh.from_edit_mesh(self.ob.data)

        for e in bm.edges:
            if e.select:
                self.edge = e.index

        self.proj_ob = bpy.data.objects[self.ob.swiftBlock_ProjectionObject]
        blender_utils.activateObject(self.proj_ob)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'RETURN'}:
            bm = bmesh.from_edit_mesh(self.proj_ob.data)
            selected_edges = []
            projl = bm.edges.layers.string.get("projectionEdgeId")
            if not projl:
                projl = bm.edges.layers.int.new("projectionEdgeId")
                self.proj_ob.data.update()
            for e in bm.edges:
                if e.select:
                    e[projl] = self.edge
            blender_utils.activateObject(self.ob)
            return {'FINISHED'}
        elif event.type in 'ESC':
            return {'CANCELLED'}
        else:
            return {'PASS_THROUGH'}

class SWIFTBLOCK_OT_ExtrudeBlocks(bpy.types.Operator):
    """Extrude blocks without removing internal edges"""
    bl_idname = "swift_block.extrude_blocks"
    bl_label = "Extrude Blocks (Retain Internal Edges)"
    bl_description = "Extrude Blocks without Removing Internal Edges (BlockSwift)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = bpy.context.active_object
        bm = bmesh.from_edit_mesh(ob.data)
        sel_mode = bpy.context.scene.tool_settings.mesh_select_mode
        bpy.context.scene.tool_settings.mesh_select_mode = (False, True, False)
        selected_faces = []
        for f in bm.faces:
            if f.select:
                selected_faces.append((f,[v for v in f.verts]))
        bpy.ops.mesh.extrude_faces_move()
        for f in selected_faces:
            newf = bm.faces.new(f[1])
            for p in ob.swiftBlock_projections:
                if p.type == 'face' and p.id == f[0].index:
                    p.id = newf.index
        bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False)
        ob.data.update()
        bpy.ops.transform.translate('INVOKE_REGION_WIN')
        return {"FINISHED"}

class SWIFTBLOCK_OT_DrawEdgeDirections(bpy.types.Operator):
    """Draw edge directions"""
    bl_idname = "swift_block.draw_edge_directions"
    bl_label = "Draw Edge Directions"
    bl_description = "Draw Edge Directions"
    bl_options = {'REGISTER', 'UNDO'}

    show: bpy.props.BoolProperty(default=True)
    size: bpy.props.FloatProperty(default=0,min=0)
    verts: bpy.props.IntProperty(default=12,min=0)
    relativeSize: bpy.props.BoolProperty(default=True)

    def invoke(self, context, event):
        self.bob = bpy.context.active_object
        bm = bmesh.from_edit_mesh(self.bob.data)
        self.edges = []
        for e in bm.edges:
            if not e.hide:
                self.edges.append((Vector(e.verts[0].co[:]),Vector(e.verts[1].co[:])))
        self.lengths = [(e[0]-e[1]).length for e in self.edges]
        self.size = 0.1
        self.execute(context)
        return {"FINISHED"}


    def execute(self,context):
        try:
            eob = bpy.data.objects['Edge_directions']
            self.remove(context,eob)
        except:
            pass
        if not self.edges or not self.show:
            self.bob.swiftBlock_direction_object = ''
            return {"CANCELLED"}
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.mesh.primitive_cone_add(vertices=self.verts,radius1=0.3,depth=1)#,end_fill_type='NOTHING')
        default_arrow = context.active_object
        arrows = []
        # this is "a bit" slow
        for e,l in zip(self.edges,self.lengths):
            v1 = Vector(e[0])
            v2 = Vector(e[1])
            tob = bpy.data.objects.new("Arrow_duplicate", default_arrow.data)
            tob.location = v1+0.5*(v2-v1)
            if self.relativeSize:
                scale = self.size*l
            else:
                scale = self.size
            tob.scale = (scale,scale,scale)
            tob.rotation_mode = 'QUATERNION'
            tob.rotation_quaternion = (v1-v2).to_track_quat('Z','Y')
            bpy.context.collection.objects.link(tob)
            arrows.append(tob)
            tob.select_set(True)
        aob = arrows[0]
        bpy.context.view_layer.objects.active = aob
        aob.name = 'Edge_directions'
        aob.hide_select = True

        mat = bpy.data.materials.new('black')
        #mat.emit = 2
        mat.diffuse_color = (0,0,0,1)
        bpy.ops.object.material_slot_add()
        aob.material_slots[-1].material = mat
        self.remove(context, default_arrow)
        aob.swiftBlock_isdirectionObject = True

        bpy.ops.object.join()
        bpy.ops.object.shade_smooth()
        blender_utils.activateObject(self.bob)
        self.bob.swiftBlock_direction_object = aob.name
        return {"FINISHED"}

    def remove(self, context, ob):
        bpy.context.collection.objects.unlink(ob)
        bpy.data.objects.remove(ob)

        # Remove lingering Arrow_duplicate objects
        if not self.show:
            for ob in bpy.data.objects:
                if ob.name.startswith('Arrow_duplicate'):
                    bpy.data.objects.remove(ob)


class SWIFTBLOCK_OT_EdgeVisualiser(bpy.types.Operator):
    bl_idname = "swift_block.edge_visualiser"
    bl_label = "Show Edge Directions"
    bl_description = "Show Edge Directions"

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type == 'ESC':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {"CANCELLED"}
        return {"PASS_THROUGH"}

    def invoke(self, context, event):
        args = (self, context)
        if context.area.type == "VIEW_3D":
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_edge_direction, args, 'WINDOW', 'POST_VIEW')
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        else:
            self.report({"WARNING"}, "View3D not found, can't run operator")
            return {"CANCELLED"}

# -----------------

classes = (
    SWIFTBLOCK_PG_BlockProperty,
    SWIFTBLOCK_PG_ProjectionProperty,
    SWIFTBLOCK_PG_EdgeGroupProperty,

    VIEW3D_PT_SwiftBlockPanel,

    SWIFTBLOCK_UL_block_items,
    SWIFTBLOCK_UL_boundary_items,
    SWIFTBLOCK_UL_projection_items,
    SWIFTBLOCK_UL_edgegroup_items,

    SWIFTBLOCK_OT_BoundariesAction,
    SWIFTBLOCK_OT_EdgeGroupsAction,
    SWIFTBLOCK_OT_InitBlocking,
    SWIFTBLOCK_OT_BuildBlocking,
    SWIFTBLOCK_OT_PreviewMesh,
    SWIFTBLOCK_OT_WriteMesh,
    SWIFTBLOCK_OT_ActivateBlocking,
    SWIFTBLOCK_OT_GetBlock,
    SWIFTBLOCK_OT_EditBlock,
    SWIFTBLOCK_OT_EnableBlock,
    SWIFTBLOCK_OT_SetEdge,
    SWIFTBLOCK_OT_GetEdge,
    SWIFTBLOCK_OT_SetCellSize,
    SWIFTBLOCK_OT_EdgeSelectParallel,
    SWIFTBLOCK_OT_FlipEdges,
    SWIFTBLOCK_OT_GetProjection,
    SWIFTBLOCK_OT_AddProjections,
    SWIFTBLOCK_OT_RemoveProjection,
    SWIFTBLOCK_OT_RemoveProjections,
    SWIFTBLOCK_OT_ActivateSnap,
    SWIFTBLOCK_OT_EdgetoPolyLine,
    SWIFTBLOCK_OT_ExtrudeBlocks,
    SWIFTBLOCK_OT_DrawEdgeDirections,
    SWIFTBLOCK_OT_EdgeVisualiser,
)

def blockExtrusion_menu(self, context):
    self.layout.operator("swift_block.extrude_block")

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except:
            print("Warning: %s registration failed, continuing.." % cls)
    bpy.types.VIEW3D_MT_edit_mesh_extrude.prepend(blockExtrusion_menu)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_edit_mesh_extrude.remove(blockExtrusion_menu)

if __name__ == "__main__":
    register()
