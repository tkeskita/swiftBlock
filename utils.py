import bpy
import numpy as np
import bmesh
from . import blender_utils
import importlib

def edgeMapping(edge):
    if edge["type"] == "Geometric MG":
        return multiGrading(edge)
    elif edge["type"] == "Geometric":
        edge["ratio"] == edge["ratio"]
        return edge

def multiGrading(edge):
    eps = 1e-6
    grading1 = True
    grading2 = True
    x1,x2 = edge['x1'], edge['x2']
    r1,r2 = edge['r1'], edge['r2']
    N, L = edge['N'], edge['L']

    def both(L,N,x1,x2,r1,r2,dx):
        n1 = np.log(dx/x1) / np.log(r1) + 1
        n2 = np.log(dx/x2) / np.log(r2) + 1
        l1 = x1*(1-r1**n1)/(1-r1)
        l2 = x2*(1-r2**n2)/(1-r2)
        Lapprox = l1 + l2 + (N - n1 - n2-1)*dx
        err = (L-Lapprox)
        return err,(n1,n2,l1,l2)

    def oneside(L,N,x,r,dx):
        n = np.log(dx/x) / np.log(r) + 1
        l = x*(1-r**n)/(1-r)
        Lapprox = l + (N - n)*dx
        err = (L-Lapprox)
        return err,(n,l)

    if abs(x1) < eps or (abs(r1) - 1) < eps:
        grading1 = False
    if abs(x2) < eps or (abs(r2) - 1) < eps:
        grading2 = False

    if not grading1 and not grading2:
        edge["l1"], edge["l2"] = 0,0
        edge["n1"], edge["n2"] = 0,0
        edge["ratio1"], edge["ratio2"] = 1,1
        edge["dL"], edge["nL"] = 1, N
        return edge

    elif grading1 and not grading2:
        l1 = x1*(1-r1**N)/(1-r1)
        if l1 < L:
            n1 = np.log(1-l1/x1*(1-r1))/np.log(r1)
            n1 += 1
            dx = x1*r1**n1
            edge["l1"], edge["l2"] = L,0
            edge["n1"], edge["n2"] = n1,0
            edge["ratio1"], edge["ratio2"] = dx/x1,1
            edge["dL"], edge["nL"] = 0, 0
            return edge
        approx = oneside
        x,r = x1,r1
        dx = L/N #initial guess
        parameters = [L,N,x,r,dx]
    elif not grading1 and grading2:
        l2 = x2*(1-r2**N)/(1-r2)
        if l2 < L:
            n2 = np.log(1-l2/x2*(1-r2))/np.log(r2)
            n2 += 1
            dx = x2*r2**n2
            edge["l1"], edge["l2"] = 0,L
            edge["n1"], edge["n2"] = 0,n2
            edge["ratio1"], edge["ratio2"] = 1,dx/x2
            edge["dL"], edge["nL"] = 0, 0
            return edge
        approx = oneside
        x,r = x2,r2
        dx = L/N
        parameters = [L,N,x,r,dx]
    else:
        n1 = (np.log(x2/x1)+N*np.log(r2))/np.log(r1*r2)
        n1 = int(n1+0.5)
        n2 = N-n1-1
        l1 = x1*((1-r1**n1)/(1-r1))
        l2 = x2*((1-r2**n2)/(1-r2))
        if (l1+l2) < L:
            n1 = np.log((L*(1-r1)*(1-r2)-x1-x2+x1*r2+x2*r1)/(-2*x1+x1*r1+x1*r2))/np.log(r1)
            n2 = np.log(x1/x2*r1**n1)/np.log(r2)
            l1 = x1*((1-r1**n1)/(1-r1))
            l2 = x2*((1-r2**n2)/(1-r2))
            dx = x1*r1**n1
            n1 += 1
            n2 += 1
            edge["l1"], edge["l2"] = l1,l2
            edge["n1"], edge["n2"] = n1,n2
            edge["ratio1"], edge["ratio2"] = dx/x1, dx/x2
            edge["dL"], edge["nL"] = 0, 0
            return edge
            # l2 = (x2-x1+L-L*r1)/(2-r2-r1)
            # l1 = L - l2
            # n1 = np.log(1-l1/x1*(1-r1))/np.log(r1)
            # n2 = N-n1
        approx = both
        dx = L/N
        parameters = [L,N,x1,x2,r1,r2,dx]


    Lapprox = 0.0
    err = 1.0
    count = 0

    err,pars=approx(*parameters)
    dx_old = dx
    err_old = err
    dx = dx*1.2*1e-10 # small perturbation
    parameters[-1] = dx
    err,pars=approx(*parameters)

    while abs(err)>1e-12 and count < 1000:
        dx_temp = dx
        derr = (err - err_old)/(dx - dx_old)
        dx = dx - err/derr
        dx_old = dx_temp
        err_old = err
        parameters[-1] = dx
        err, out = approx(*parameters)
        count = count+1

    if grading1 and not grading2:
        n1,l1 = out
        ratio1 = dx/x1
        n2,l2,ratio2 = 0,0,1
    elif not grading1 and grading2:
        n2,l2 = out
        ratio2 = dx/x2
        n1,l1,ratio1 = 0,0,1
    else:
        n1,n2,l1,l2 = out
        ratio1 = dx/x1
        ratio2 = dx/x2

    if (dx < x1 and abs(x1) > eps) or (dx < x2 and abs(x2) > eps):
        dx = x1
        l1, l2 = 0,0
        n1, n2 = 0,0
        ratio1, ratio2 = 1, 1

    dL = L-l1-l2
    nL = N-n1-n2
    dx = dL/nL
    edge['l1'], edge['l2'] = l1, l2
    edge['n1'], edge['n2'] = n1, n2
    edge['ratio1'], edge['ratio2'] = ratio1, ratio2
    edge['dL'], edge['nL'] = dL, nL
    return edge

def getNodes(x1,x2,r1,r2,L,dx):
    n1 = np.log(dx/x1)/np.log(r1) + 1
    n2 = np.log(dx/x1)/np.log(r1) + 1
    l1 = x1*(1-r1**n1)/(1-r1)
    l2 = x2*(1-r2**n2)/(1-r2)
    if (l1+l2) > L:
        n1 = np.log((L*(1-r1)*(1-r2)-x1-x2+x1*r2+x2*r1)/(-2*x1+x1*r1+x1*r2))/np.log(r1)
        n1 = int(n1+0.5)+1
        n2 = np.log(x1/x2*r1**n1)/np.log(r2)
        n2 = int(n2+0.5)
        l1 = x1*((1-r1**n1)/(1-r1))
        l2 = x2*((1-r2**n2)/(1-r2))
        dx = x1*r1**n1
        return n1+n2
    else:
        return n1+n2+(L-l1-l2)/dx

def edge(e0, e1):
    return [min(e0,e1), max(e0,e1)]

def findFace(faces, vl):
    for fid, f in enumerate(faces):
        if vl[0] in f and vl[1] in f and vl[2] in f and vl[3] in f:
            return fid, f
    return -1, []


# No comments. Just works.
def getEdgeDirections(block_print_out, dependent_edges):
    edgeDirections = [set() for i in dependent_edges]
    positiveBlockEdges = [[(0,1),(3,2),(7,6),(4,5)],[(0,3),(1,2),(5,6),(4,7)],[(0,4),(1,5),(2,6),(3,7)]]
    for i in range(1000):
        ready = True
        for ed, de in zip(edgeDirections,dependent_edges):
            if not len(ed)==len(de):
                ready = False
        if ready:
            break
        for bid, vl in enumerate(block_print_out):
            for es, edgeSet in enumerate(dependent_edges):
                for direction in range(3):
                    if edge(vl[positiveBlockEdges[direction][0][0]],vl[positiveBlockEdges[direction][0][1]]) in edgeSet:
                        if not edgeDirections[es]:
                            edgeDirections[es] = set([(vl[e[0]],vl[e[1]]) for e in positiveBlockEdges[direction]])
                        else:
                            simedges = edgeDirections[es].intersection([(vl[e[0]],vl[e[1]]) for e in positiveBlockEdges[direction]])
                            if simedges:
                                edgeDirections[es] |= set([(vl[e[0]],vl[e[1]]) for e in positiveBlockEdges[direction]])
                            else:
                                asimedges= set(edgeDirections[es]).intersection([(vl[e[1]],vl[e[0]]) for e in positiveBlockEdges[direction]])
                                if asimedges:
                                    edgeDirections[es] |= set([(vl[e[1]],vl[e[0]]) for e in positiveBlockEdges[direction]])

    return edgeDirections

def sortEdges(edges):
    sorted=[]
    # Find out if the edges form a loop
    edges1D=np.ravel(edges)
    occ=np.bincount(edges1D)
    # This is a loop, let's just start sorting anywhere (from first element here)
    if len(np.where(occ==1)[0])==0:
        sorted.append(edges[0][0])
    # This is not a loop, let's find the first or last element
    else:
        # Find a vertex which occurs only 1 and then it's place in 2D list
        firstidx1D=np.where(edges1D==np.where(occ==1)[0][0])[0][0]
        if firstidx1D % 2 == 0:
            sorted.append(edges[int(firstidx1D/2)][0])
        else:
            sorted.append(edges[int((firstidx1D-1)/2)][1])
    edgesTemp = []
    vertids = []
    for e in edges:
        vertids.append(e[0])
        vertids.append(e[1])
    vertids = list(set(vertids))
    vertid=sorted[0]
    edgesTemp=edges[:]
    for i in range(len(vertids)):
        for eid, e in enumerate(edgesTemp):
            if vertid in e:
                if e[0] == vertid:
                    sorted.append(e[1])
                else:
                    sorted.append(e[0])
                edgesTemp.pop(eid)
                vertid = sorted[-1]
                break
    return sorted

def obFromStructuredMesh(verts, dim, objName):
    context = bpy.context
    nx, ny, nz = dim
    edges = []
    faces = []
    boundary_verts = []
    boundary_mes = []
    boundary_verts.append(list(verts[0:nx*ny]))
    boundary_verts.append(verts[nx*ny*nz-nx*ny:])
    boundary_verts.append(verts[::nx])
    boundary_verts.append(verts[nx-1::nx])
    boundary_verts.append([])

    for sverts in range(0,nx*ny*nz,nx*ny):
        boundary_verts[-1].extend(verts[sverts:sverts+nx])

    boundary_verts.append([])
    for sverts in range(nx*ny-nx,nx*ny*nz,nx*ny):
        boundary_verts[-1].extend(verts[sverts:sverts+nx])

    verts = [v for bv in boundary_verts for v in bv]
    boundary_faces = []
    boundary_ij = [[nx,ny], [ny,nz], [nx,nz]]
    vert_idx = 0
    # With Numpy slicing?
    for ni, nj in boundary_ij:
        bf = []
        for j in range(nj-1):
            for i in range(ni-1):
                bf.append((i+j*ni,1+i+j*ni,1+i+(1+j)*ni,i+(1+j)*ni))

        boundary_faces.append(bf)
        boundary_faces.append(bf)
        # Blender face arrays do not work with np.ints
        faces.extend((np.array(bf)+vert_idx).tolist())
        vert_idx += ni*nj

        faces.extend((np.array(bf)+vert_idx).tolist())
        vert_idx += ni*nj


    boundary_mes = [bpy.data.meshes.new('boundary_%s'%i) for i in range(6)]
    for bm, bv, bf in zip(boundary_mes, boundary_verts, boundary_faces):
        bm.from_pydata(bv, [], bf)

    vol_me=bpy.data.meshes.new('internal')
    vol_me.from_pydata(verts, edges,faces)
    vol_me.update()

    ob = bpy.data.objects.new(objName,vol_me)
    bpy.context.collection.objects.link(ob)
    boundary_obs = []
    for i, bm in enumerate(boundary_mes):
        boundary_ob = bpy.data.objects.new(objName+ '_{}'.format(i), bm)
        boundary_ob.parent = ob
        # boundary_ob.show_all_edges = True
        # boundary_ob.show_wire = True
        bpy.context.collection.objects.link(boundary_ob)
        boundary_obs.append(boundary_ob)
    return ob


def getBlockFaces(verts):
    fids = [(0,1,5,4),(0,3,2,1),(3,7,6,2),(4,5,6,7),(0,4,7,3),(1,2,6,5)]
    faces = [(verts[f[0]],verts[f[1]],verts[f[2]],verts[f[3]]) for f in fids]
    return faces


# Utility functions
# -----------------

def collectEdges(bob, lengths):
    bob.select_set(True)
    bpy.context.view_layer.objects.active = bob
    bpy.ops.object.mode_set(mode='EDIT')
    # snap_vertices = get_snap_vertices(bob)
    bm = bmesh.from_edit_mesh(bob.data)
    layers = bm.edges.layers
    # snapIdl = layers.string.get('snapId')
    block_edges = dict()

    timel = layers.int.get('modtime')
    groupl = layers.int.get('groupid')
    x1l = layers.float.get('x1')
    x2l = layers.float.get('x2')
    r1l = layers.float.get('r1')
    r2l = layers.float.get('r2')
    cellsl = layers.int.get('cells')
    ratiol = layers.float.get("ratio")

    ncells = dict()
    times = dict()
    for e in bm.edges:
        if e[groupl] not in ncells:
            ncells[e[groupl]] = e[cellsl]
            times[e[groupl]] = e[timel]
        elif e[timel] > times[e[groupl]]:
            ncells[e[groupl]] = e[cellsl]
            times[e[groupl]] = e[timel]

    for e in bm.edges:
        be = dict()
        ev = list([e.verts[0].index,e.verts[1].index])
        if ev in lengths[0]:
            ind = lengths[0].index(ev)
            L = lengths[1][ind]
        else:
            L = (e.verts[0].co-e.verts[1].co).length
        be["type"] = bob.swiftBlock_MappingType
        be["x1"] = e[x1l]
        be["x2"] = e[x2l]
        be["r1"] = e[r1l]
        be["r2"] = e[r2l]
        be["N"] = ncells[e[groupl]]
        be["ratio"] = e[ratiol]
        be["L"] = L
        if not be["N"]:
            be["N"] = 10
        if not be["r1"]:
            be["r1"] = 1.
        if not be["r2"]:
            be["r2"] = 1.
        if not be["ratio"]:
            be["ratio"] = 1
        be = edgeMapping(be)
        block_edges[(e.verts[1].index,e.verts[0].index)] = be
        be = dict(be)
        be["x1"],be["x2"] = be["x2"],be["x1"]
        be["r1"],be["r2"] = be["r2"],be["r1"]
        be["ratio"] = 1./be["ratio"]
        be = edgeMapping(be)

        block_edges[(e.verts[0].index,e.verts[1].index)] = be
    return block_edges


# Build the mesh from already existing blocking
def writeMesh(ob, folder = ''):
    if not ob.swiftBlock_blocks:
        bpy.ops.swift_block.build_blocking('INVOKE_DEFAULT')

    verts = list(blender_utils.vertices_from_mesh(ob))
    bm = bmesh.from_edit_mesh(ob.data)

    # do not write polylines for hidden edges
    edges = []
    for e in bm.edges:
        if not e.hide:
            edges.append((e.verts[0].index, e.verts[1].index))

    bpy.ops.object.mode_set(mode='OBJECT')


    ob.select_set(False)
    if ob.swiftBlock_Autosnap and ob.swiftBlock_EdgeSnapObject:
        polyLines, polyLinesPoints, lengths = getPolyLines(verts, edges, ob)
    else:
        polyLines = []
        lengths = [[]]
    verts = []
    matrix = ob.matrix_world.copy()
    for v in ob.data.vertices:
        verts.append(matrix @ v.co)

    blocks = []
    block_names = []
    for b in ob.swiftBlock_blocks:
        if b.enabled:
            blocks.append(list(b.verts))
            if b.namedRegion:
                block_names.append(b.name)
            else:
                block_names.append('')

    edgeInfo = collectEdges(ob,lengths)

    bm = bmesh.from_edit_mesh(ob.data)
    detemp = []
    groupl = bm.edges.layers.int.get('groupid')
    ngroups = 0
    for e in bm.edges:
        detemp.append((e[groupl],e.verts[0].index,e.verts[1].index))
        ngroups = max(ngroups,e[groupl])

    block_edges = [[] for i in range(ngroups+1)]
    for e in detemp:
        block_edges[e[0]].append([e[1],e[2]])

    enabledl = bm.faces.layers.int.get('enabled')
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    projections = {'vert2surf':dict(),'edge2surf':dict(),'face2surf':dict(), 'geo':dict()}
    for p in ob.swiftBlock_projections:
        if p.type == 'vert2surf' and any([f[enabledl] for f in bm.verts[p.id].link_faces]):
            key = bm.verts[p.id].index
            if key in projections[p.type]:
                projections[p.type][key] += " {}".format(p.ob)
            else:
                projections[p.type][key] = p.ob
        elif p.type == 'edge2surf' and any([f[enabledl] for f in bm.edges[p.id].link_faces]):
            key = tuple(v.index for v in bm.edges[p.id].verts)
            if key in projections[p.type]:
                projections[p.type][key] += " {}".format(p.ob)
            else:
                projections[p.type][key] = p.ob
        elif p.type == 'face2surf' and bm.faces[p.id][enabledl]:
            key = tuple(v.index for v in bm.faces[p.id].verts)
            projections[p.type][key] = p.ob

    selected_edges = [e.select for e in ob.data.edges]

    boundaries = [{'name':mat.name, 'type':mat.boundary_type, 'faceVerts':[]} for mat in ob.data.materials]
    for f in bm.faces:
        if f[enabledl] == 1:
            boundaries[f.material_index]['faceVerts'].append([v.index for v in f.verts])
    for b in boundaries:
        if not b['faceVerts']:
            boundaries.remove(b)

    # return edge selection
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    for e,sel in zip(ob.data.edges,selected_edges):
        e.select = sel

    ### This is everything that is related to blockMesh so a new multiblock mesher could be introduced easily just by creating new preview file ###
    if ob.swiftBlock_Mesher == 'blockMeshMG':
        from . import blockMeshMG
        importlib.reload(blockMeshMG)
        if folder:
            mesh = blockMeshMG.PreviewMesh(folder)
        else:
            mesh = blockMeshMG.PreviewMesh()
        # projection_tris = writeProjectionObjects(project_verts,project_edges,project_faces, mesh.geomPath)
        if ob.swiftBlock_projections:
            geos = writeProjectionObjects(ob, mesh.geomPath)
            projections['geo'] = geos

        cells = mesh.writeBlockMeshDict(verts, 1, boundaries, polyLines, edgeInfo, block_names, blocks, block_edges, projections)
    ###############################################################
    elif ob.swiftBlock_Mesher == 'blockMeshBodyFit':
        from . import blockMeshBodyFit
        importlib.reload(blockMeshBodyFit)
        if folder:
            mesh = blockMeshBodyFit.PreviewMesh(folder)
        else:
            mesh = blockMeshBodyFit.PreviewMesh()
        writeProjectionObjects(ob, mesh.triSurfacePath, onlyFaces = True)
        cells = mesh.writeBlockMeshDict(verts, 1, boundaries, polyLines, edgeInfo, block_names, blocks, block_edges, projections, ob.swiftBlock_SearchLength)
    bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(False,True,False)")
    return mesh, cells


def changeMesher(self, context):
    ob = context.active_object
    if ob.swiftBlock_Mesher == "blockMeshMG":
        ob.swiftBlock_MappingType = "Geometric MG"
    elif ob.swiftBlock_Mesher == "blockMeshBodyFit":
        ob.swiftBlock_MappingType = "Geometric"

def showInternalFaces(self, context):
    ob = context.active_object
    hideFacesEdges(ob, ob.swiftBlock_ShowInternalFaces)

def hideFacesEdges(ob, showInternal = False):
    ob.data.update()
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()

    negl = bm.faces.layers.int.get('neg')
    posl = bm.faces.layers.int.get('pos')
    enabledl = bm.faces.layers.int.get('enabled')

    for f in bm.faces:
        if f[negl] != -1 and f[posl] != -1:
            if (not ob.swiftBlock_blocks[f[posl]].enabled and ob.swiftBlock_blocks[f[negl]].enabled) \
                    or (ob.swiftBlock_blocks[f[posl]].enabled and not ob.swiftBlock_blocks[f[negl]].enabled):
                # boundary face
                f.hide = False # = False
                f[enabledl] = 1
            elif not ob.swiftBlock_blocks[f[posl]].enabled and not ob.swiftBlock_blocks[f[negl]].enabled:
                # both blocks disabled
                f[enabledl] = False
                f.hide = True
            elif showInternal:
                # internal face
                f[enabledl] = 2
                f.hide = False
            else:
                # internal face
                f[enabledl] = 2
                f.hide = True
        elif (f[posl] == -1 and f[negl] != -1): #boundary face
            if ob.swiftBlock_blocks[f[negl]].enabled:
                # boundary face
                f.hide = False # = False
                f[enabledl] = 1
            else:
                # boundary block disabled
                f.hide = True
                f[enabledl] = False
        elif (f[posl] != -1 and f[negl] == -1): #boundary face
            if ob.swiftBlock_blocks[f[posl]].enabled:
                # boundary face
                f.hide = False
                f[enabledl] = 1
            else:
                # boundary block disabled
                f.hide = True
                f[enabledl] = False

    for e in bm.edges:
        edge_found = False
        for b in ob.swiftBlock_blocks:
            if b.enabled and e.verts[0].index in b.verts and e.verts[1].index in b.verts:
                edge_found = True
                e.hide = False
                continue
        if not edge_found:
            e.hide = True

    bpy.ops.swift_block.draw_edge_directions('INVOKE_DEFAULT',show=False)
    ob.data.update()

# Get all objects in current context
def getProjectionObjects(self, context):
    obs = []
    for ob in bpy.data.objects:
        if ob.type == "MESH" and not ob.swiftBlock_isblockingObject and not ob.swiftBlock_ispreviewObject and not ob.swiftBlock_isdirectionObject:
            obs.append((ob.name, ob.name, ''))
    return obs

def updateBoundaryColor(self, context):
    ob = context.active_object
    mat = bpy.data.materials[self.name]
    mat.diffuse_color = self.color

def updateBoundaryName(self, context):
    ob = context.active_object
    mat = bpy.data.materials[self.oldName]
    mat.name = self.name
    self.oldName = mat.name


# This function checks that the vert, edge or face is still there.
# Unfortunately, the projection ids might be wrong if verts, edges
# or faces have been deleted.
def updateProjections(ob):
    bm = bmesh.from_edit_mesh(ob.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    remove_projections = []
    for i, p in enumerate(ob.swiftBlock_projections):
        try:
            if p.type == 'vert2surf':
                bm.verts[p.id]
            elif p.type == 'edge2surf':
                bm.edges[p.id]
            elif p.type == 'face2surf':
                bm.faces[p.id]
        except IndexError:
            remove_projections.append(i)
    for pid in reversed(sorted(remove_projections)):
        ob.swiftBlock_projections.remove(pid)

# Boundary condition operators
def selectActiveBoundary(self, context):
    ob = context.active_object
    ob.active_material_index = ob.swiftBlock_boundary_index

    bm = bmesh.from_edit_mesh(ob.data)
    bpy.ops.mesh.select_all(action='DESELECT')

    for f in bm.faces:
        if f.material_index == ob.swiftBlock_boundary_index:
            f.select=True

def patchColor(patch_no):
    color = [(0.25,0.25,0.25,1), (1.0,0.,0.,1), (0.0,1.,0.,1), (0.0,0.,1.,1), \
             (0.707,0.707,0,1), (0,0.707,0.707,1), (0.707,0,0.707,1)]
    return color[patch_no % len(color)]

def writeProjectionObjects(ob, path, onlyFaces = False):
    blender_version = bpy.app.version[1]
    objects = []
    for p in ob.swiftBlock_projections:
        if onlyFaces and not p.type == 'face2surf':
            continue
        else:
            objects.append(p.ob)
    objects = set(objects)
    for o in objects:
        sob = bpy.data.objects[o]
        hide = sob.hide_get()
        blender_utils.activateObject(sob)
        bpy.ops.export_mesh.stl(filepath = path + '/{}.stl'.format(o), use_selection=True)
        sob.hide_set(hide)
    blender_utils.activateObject(ob)
    return objects


# Kalle's implementation
def getPolyLines(verts, edges, bob):
    polyLinesPoints = []
    polyLines = ''
    polyLinesLengths = [[], []]
    tol = 1e-6

    def isPointOnEdge(point, A, B):
        eps = (((A - B).magnitude - (point-B).magnitude) - (A-point).magnitude)
        return True if (abs(eps) < tol) else False

    # nosnap= [False for i in range(len(edges))]
    # for eid, e in enumerate(obj.data.edges):
        # nosnap[eid] = e.use_edge_sharp

    bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(True,False,False)")
    geoobj = bpy.data.objects[bob.swiftBlock_EdgeSnapObject]
    geo_verts = list(blender_utils.vertices_from_mesh(geoobj))
    geo_edges = list(blender_utils.edges_from_mesh(geoobj))
    geoobj.select_set(False) # avoid deletion

# First go through all vertices in the block structure and find vertices snapped to edges
# When found, add a vertex at that location to the polyLine object by splitting the edge
# Create a new Blender object containing the newly inserted verts. Then use Blender's
# shortest path algo to find polyLines.

    for vid, v in enumerate(verts):
        found = False
        for gvid, gv in enumerate(geo_verts):
            mag = (v-gv).magnitude
            if mag < tol:
                found = True
                break   # We have found a vertex co-located, continue with next block vertex
        if not found:
            for geid, ge in enumerate(geo_edges):
                if (isPointOnEdge(v, geo_verts[ge[0]], geo_verts[ge[1]])):
                    geo_verts.append(v)
                    geo_edges.append([geo_edges[geid][1],len(geo_verts)-1]) # Putting the vert on the edge, by splitting it in two.
                    geo_edges[geid][1] = len(geo_verts)-1
                    break # No more iteration, go to next block vertex

    mesh_data = bpy.data.meshes.new("deleteme")
    mesh_data.from_pydata(geo_verts, geo_edges, [])
    mesh_data.update()
    geoobj = bpy.data.objects.new('deleteme', mesh_data)
    bpy.context.collection.objects.link(geoobj)
    geo_verts = list(blender_utils.vertices_from_mesh(geoobj))
    geo_edges = list(blender_utils.edges_from_mesh(geoobj))
    bpy.context.view_layer.objects.active=geoobj

# Now start the search over again on the new object with more verts
    snapped_verts = {}
    for vid, v in enumerate(verts):
        for gvid, gv in enumerate(geo_verts):
            mag = (v-gv).magnitude
            if mag < tol:
                snapped_verts[vid] = gvid
                break   # We have found a vertex co-located, continue with next block vertex

    bpy.ops.wm.context_set_value(data_path="tool_settings.mesh_select_mode", value="(True,False,False)")
    for edid, ed in enumerate(edges):
        if ed[0] in snapped_verts and ed[1] in snapped_verts:# and not nosnap[edid]:
            geoobj.hide_set(False)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            geoobj.data.vertices[snapped_verts[ed[0]]].select=True
            geoobj.data.vertices[snapped_verts[ed[1]]].select=True
            bpy.ops.object.mode_set(mode='EDIT')
            try:
                bpy.ops.mesh.select_vertex_path(type='EDGE_LENGTH')
            except:
                bpy.ops.mesh.shortest_path_select()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.duplicate()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.mode_set(mode='OBJECT')
            polyLineobj = bpy.data.objects['deleteme.001']
            if len(polyLineobj.data.vertices) > 2:
                polyLineverts = list(blender_utils.vertices_from_mesh(polyLineobj))
                polyLineedges = list(blender_utils.edges_from_mesh(polyLineobj))
                for vid, v in enumerate(polyLineverts):
                    mag = (v-verts[ed[0]]).magnitude
                    if mag < tol:
                        startVertex = vid
                        break
                polyLineStr, vectors, length = sortedVertices(polyLineverts,polyLineedges,startVertex)
                polyLinesPoints.append([ed[0],ed[1],vectors])
                polyLinesLengths[0].append([min(ed[0],ed[1]), max(ed[0],ed[1])]) # write out sorted
                polyLinesLengths[1].append(length)
                polyLine = 'polyLine {} {} ('.format(*ed)
                polyLine += polyLineStr
                polyLine += ')\n'
                polyLines += polyLine

            geoobj.select_set(False)
            polyLineobj.select_set(True)
            bpy.ops.object.delete()
    geoobj.select_set(True)
    bpy.ops.object.delete()
    return polyLines, polyLinesPoints, polyLinesLengths

def sortedVertices(verts,edges,startVert):
    sorted = []
    vectors = []
    sorted.append(startVert)
    vert = startVert
    length = len(edges)+1
    for i in range(len(verts)):
        for eid, e in enumerate(edges):
            if vert in e:
                if e[0] == vert:
                    sorted.append(e[1])
                else:
                    sorted.append(e[0])
                edges.pop(eid)
                vert = sorted[-1]
                break

    polyLine = ''
    length = 0.
    for vid, v in enumerate(sorted):
        polyLine += '({} {} {})'.format(*verts[v])
        vectors.append(verts[v])
        if vid>=1:
            length += (vectors[vid] - vectors[vid-1]).magnitude
    return polyLine, vectors, length
