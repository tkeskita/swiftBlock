# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from mathutils import Vector, Matrix, Euler
import bgl
import bmesh



def vertices_from_mesh(ob):
    '''
    '''

    # get the modifiers
    if ob.modifiers:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = ob.evaluated_get(depsgraph)
        mesh = obj_eval.to_mesh()
    else:
        mesh = ob.data

    matrix = ob.matrix_world.copy()

    for v in mesh.vertices:
        yield (matrix @ v.co)

def edges_from_mesh(ob):
    '''
    '''

    # get the modifiers
    if ob.modifiers:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = ob.evaluated_get(depsgraph)
        mesh = obj_eval.to_mesh()
    else:
        mesh = ob.data

    for e in mesh.edges:
        yield list(e.vertices)

def activateObject(ob, hideCurrent = False):
    bpy.ops.object.mode_set(mode='OBJECT')
    cob = bpy.context.active_object
    if cob:
        cob.hide_set(hideCurrent)
        cob.select_set(False)
    ob.select_set(True)
    ob.hide_set(False)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='EDIT')


def previewMesh(ob, points, faces):
    blocking = ob
    blocking.hide_set(True)
    blocking.select_set(False)
    if not ob.swiftBlock_preview_object or \
       not ob.swiftBlock_preview_object in bpy.data.objects:
        mesh_data = bpy.data.meshes.new("previewMesh")
        previewMeshOb = bpy.data.objects.new('previewMesh', mesh_data)
        previewMeshOb.swiftBlock_ispreviewObject = True
        bpy.context.collection.objects.link(previewMeshOb)
        ob.swiftBlock_preview_object = previewMeshOb.name
    else:
        previewMeshOb = bpy.data.objects["previewMesh"]
        oldme = previewMeshOb.data
        mesh_data = bpy.data.meshes.new("previewMesh")
        previewMeshOb.data = mesh_data
        bpy.data.meshes.remove(oldme)
    previewMeshOb.hide_set(False)
    previewMeshOb.select_set(True)
    previewMeshOb.swiftBlock_blocking_object = blocking.name
    mesh_data.from_pydata(points, [], faces)
    mesh_data.update()

    bpy.context.view_layer.objects.active = previewMeshOb
    # FIXME: show_extra_edge_length is now Overlay property, find out how to do this.
    #bpy.context.object.data.show_extra_edge_length = True
    #bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    previewMeshOb.show_all_edges = True
    previewMeshOb.show_wire = True

arrow_head = [
    [-1,-1],
    [0,0],
    [1,-1],
]
def draw_arrow_head(ob, vecFrom, vecTo):
    if ob is None:
        return

    direction = Vector(vecTo) - Vector(vecFrom)
    print(direction)
    # direction.resize_2d()
    # print(direction)
    angle = direction.angle(Vector((0,1,0)))

    # form a 2d rotation matrix
    mat = Matrix().Rotation(angle, 2)

    # middle point
    middle = (Vector(vecTo) + Vector(vecFrom)) / 2.0


    bgl.glEnable(bgl.GL_BLEND)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    for v in arrow_head:
        xy = Vector(v)* 1.0 * mat
        xy.resize_3d()
        newPos = xy + middle
        bgl.glVertex3f(*newPos)
        bgl.glLineWidth(2)
        bgl.glColor4f(0.0,0.0,0.0,0.5)
    bgl.glEnd()

    # bgl.glEnable(bgl.GL_BLEND)
    # bgl.glBegin(bgl.GL_LINES)
    # bgl.glVertex3f(*(middle-Vector((1,0,0))))
    # bgl.glVertex3f(*(middle-Vector((-1,0,0))))
    # bgl.glVertex3f(*(middle-Vector((0,1,0))))
    # bgl.glVertex3f(*(middle-Vector((0,-1,0))))
    # print((middle-Vector((1,0,0))),(middle-Vector((-1,0,0))))

def draw_edge_direction(self,context):
    ob = bpy.context.active_object
    if ob is None:
        return
    if bpy.context.active_object.mode != 'EDIT':
        return
    me = ob.data
    bm = bmesh.from_edit_mesh(me)
    # draw_arrow_head(bm.edges[0])
    bgl.glEnable(bgl.GL_BLEND)
    for e in bm.edges:
        draw_arrow_head(ob, e.verts[0].co, e.verts[1].co)
    bgl.glEnd()
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0,0.0,0.0,1.0)
