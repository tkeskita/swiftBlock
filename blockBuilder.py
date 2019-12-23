import mathutils
import time
import importlib
import numpy as np
# from . import cycleFinderNumba
# importlib.reload(cycleFinderNumba)

def removedup(seq):
    checked = []
    for e in seq:
        if e not in checked:
            checked.append(e)
    return checked

def edge(e0, e1):
    return [min(e0,e1), max(e0,e1)]

def couple_edges(dependent_edges):
    for es0, edgeSet0 in enumerate(dependent_edges):
        for edge in edgeSet0:
            for es1, edgeSet1 in enumerate(dependent_edges):
                if edge in edgeSet1 and es0 != es1:
                    for e in edgeSet0:
                        edgeSet1.append(e)
                    dependent_edges.pop(es0)
                    return True
    return False



def findFace(faces, vl):
    for fid, f in enumerate(faces):
        if vl[0] in f and vl[1] in f and vl[2] in f and vl[3] in f:
            return fid, f
    return -1, []


def cycleFinder(edges,verts):
# Credit: Adam Gaither, An Efficient Block Detection Algorithm For
# Structured Grid Generation. Proc. 5th Int. Conf. Num. Grid
# Generation in Comp. Field Simulations, pp. 443-451 (1996).

    verticesId = verts
    edgeVisited = np.zeros(len(edges), dtype=bool)
    faces = []
    facesEdges = []
    no_edges = 0

    v_in_edge = [[] for i in range(len(verts))]
    for v in verts:
        for eid, e in enumerate(edges):
            if v in e:
                v_in_edge[v].append(eid)
    v_in_edges = np.array(v_in_edge)

    for v in verticesId:
        currentCycle = [v]
        currentCycleEdges = []
        buildFourEdgeFaces(v, v_in_edge, edgeVisited, edges, no_edges, currentCycle, currentCycleEdges, faces, facesEdges)

    faces = np.reshape(faces,(-1,4))
    temp, u = np.unique(np.sort(faces), axis=0, return_index=True)
    faces = faces[u]
    facesP = [list(map(np.asscalar,f)) for f in faces]

    facesEdges = np.reshape(facesEdges,(-1,4))
    facesEdges = facesEdges[u]
    facesEdgesP = [list(map(np.asscalar,f)) for f in facesEdges]

    return facesP, facesEdgesP

def buildFourEdgeFaces(v, v_in_edge, edgeVisited, edges, no_edges, currentCycle, currentCycleEdges, faces, facesEdges):
    for eid in v_in_edge[v]:
        if not edgeVisited[eid]:
            e = edges[eid]
            no_edges += 1
            edgeVisited[eid] = True
            opposite_v = e[0]
            if opposite_v == v: # seems the other vertex is in e[1]!
                opposite_v = e[1]
            currentCycle.append(opposite_v)
            currentCycleEdges.append(eid)
            if currentCycle[0] == currentCycle[-1]: # First equals last -> we have a face
                if len(currentCycle) == 5:
                    faces.extend(currentCycle[0:4])
                if len(currentCycleEdges) == 4:
                    facesEdges.extend(currentCycleEdges[0:4])
            else:
                if no_edges < 4:
                    buildFourEdgeFaces(opposite_v, v_in_edge, edgeVisited, edges, no_edges, currentCycle, currentCycleEdges, faces, facesEdges)
            no_edges -= 1
            currentCycle.pop()
            currentCycleEdges.pop()
            edgeVisited[eid] = False


def blockFinder(edges, vertices_coord, logFileName='', debugFileName='', disabled = [], numba=False):
    if len(logFileName) > 0:
        logFile = open(logFileName,'w')
    else:
        logFile = ''

    # Use the cycle finder class to find all edges forming quad faces
    if numba:
        from . import cycleFinderNumba
        tmp_v,tmp_e = cycleFinderNumba.cycleFinder(edges,range(len(vertices_coord)))
    else:
        tmp_v,tmp_e = cycleFinder(edges,range(len(vertices_coord)))

    faces_as_list_of_vertices = []
    faces_as_list_of_nodes = []
    faces_as_list_of_edges = []
    for ii, i in enumerate(tmp_v): # get rid of possible triangles
        if len(i) == 4:
            faces_as_list_of_vertices.append([vertices_coord[i[0]], vertices_coord[i[1]], vertices_coord[i[2]], vertices_coord[i[3]]])
            faces_as_list_of_nodes.append(i)
            faces_as_list_of_edges.append(tmp_e[ii])
    # Create a wavefront obj file showing all the faces just found
    if len(debugFileName) > 0:
        debugFile = open(debugFileName,'w')
        for v in vertices_coord:
            debugFile.write('v {} {} {}\n'.format(*v))
        for f in faces_as_list_of_nodes:
            debugFile.write('f ')
            for n in f:
                debugFile.write('{} '.format(n+1))
            debugFile.write('\n')
        debugFile.close()

    # Store some info for the faces in a dict
    face_info = {}
    for fid, f in enumerate(faces_as_list_of_vertices):
        normal = mathutils.geometry.normal(f[0],f[1],f[2],f[3])
        facecentre = mathutils.Vector((0,0,0))
        for v in f:
            facecentre += 0.25*v
        face_info[fid] = {}
        face_info[fid]['normal'] = normal
        face_info[fid]['pos'] = []
        face_info[fid]['neg'] = []
        face_info[fid]['centre'] = facecentre

    connections_between_faces = []
    # Find connections between faces, i.e. they share one edge
    for fid1, f1 in enumerate(faces_as_list_of_edges):
        for e in f1:
            for fid2, f2 in enumerate(faces_as_list_of_edges):
                if e in f2 and not fid1 == fid2:
                    if not [min(fid1,fid2),max(fid1,fid2)] in connections_between_faces:
                        connections_between_faces.append([min(fid1,fid2),max(fid1,fid2)])

    #this is the most time consuming step
    # Use these connections to find cycles of connected faces; called faceLoops
    if numba:
        faceLoops_as_list_of_faces, faceLoops_as_list_of_connections = cycleFinderNumba.cycleFinder(connections_between_faces,range(len(faces_as_list_of_vertices)))
    else:
        faceLoops_as_list_of_faces, faceLoops_as_list_of_connections = cycleFinder(connections_between_faces,range(len(faces_as_list_of_vertices)))
    # faceLoops_as_list_of_faces, faceLoops_as_list_of_connections = blockBuilder2.cycleFinder(connections_between_faces,range(len(faces_as_list_of_vertices)))


    # Dig out block structures from these face loops
    block_as_faceLoop = []
    for qf in faceLoops_as_list_of_faces:
        qf_is_a_block = True
        for n in faces_as_list_of_nodes[qf[0]]:
            if n in faces_as_list_of_nodes[qf[2]]: #if any of the vertices in face 0 is in face 2, this is not a block
                qf_is_a_block = False
        if qf_is_a_block:
            block_as_faceLoop.append(qf)
    # Get rid of block dublets - there are plenty
    faceLoops_nodes = [[] for i in range(len(block_as_faceLoop))]
    for qfid, qf in enumerate(block_as_faceLoop):
        for f in qf:
            for n in faces_as_list_of_nodes[f]:
                if not n in faceLoops_nodes[qfid]:
                    faceLoops_nodes[qfid].append(n)
    for qf in faceLoops_nodes:
        qf.sort()
    tmp = []
    potentialBlocks = [] # Each block is identified several times. Condense and put in potentialBlocks (list of vertices index)
    for qfid, qf in enumerate(faceLoops_nodes):
        if not qf in tmp:
            tmp.append(qf)
            if len(qf) == 8:
                potentialBlocks.append(block_as_faceLoop[qfid])
    offences = []
    block_centres = []
    formalBlocks = []
    dependent_edges = []
    all_edges = []
    if len(logFileName) > 0:
        logFile.write('number of potential blocks identified = ' + str(len(potentialBlocks)) + '\n')

    for b in potentialBlocks:
        is_a_real_block = True  # more sanity checks soon...
        block = []
        for n in faces_as_list_of_nodes[b[0]]:
            block.append(n)
        for n in faces_as_list_of_nodes[b[2]]:
            block.append(n)
        q2start = None
        for e in edges: # Locate the vertex just above block[0]. Store as q2start
            if block[0] == e[0]:
                if e[1] in block[4:8]:
                    q2start = block.index(e[1])
            if block[0] == e[1]:
                if e[0] in block[4:8]:
                    q2start = block.index(e[0])
        if q2start == None: # if not found above - this is not a complete block.
            q1nodes = block[0:4]
            q2nodes = block[4:-1]
            if len(logFileName) > 0:
                logFile.write('one block found was incomplete! ' + str(q1nodes) + str(q2nodes) + '\n')
            continue
            q2start = 0 #just set it to something. block wont be printed anyway
        quad1 = block[0:4]
        quad2 = []
        for i in range(4):
            quad2.append(block[(i + q2start) % 4 + 4])
        q1verts = [vertices_coord[quad1[0]],vertices_coord[quad1[1]],vertices_coord[quad1[2]],vertices_coord[quad1[3]]]
        q2verts = [vertices_coord[quad2[0]],vertices_coord[quad2[1]],vertices_coord[quad2[2]],vertices_coord[quad2[3]]]

        blockcentre = mathutils.Vector((0,0,0))
        for n in block:
            blockcentre += 0.125*vertices_coord[n]
        q1fid, tmp = findFace(faces_as_list_of_nodes, quad1)
        q2fid, tmp = findFace(faces_as_list_of_nodes, quad2)

        normal1 = mathutils.geometry.normal(*q1verts)
        normal2 = mathutils.geometry.normal(*q2verts)

        facecentre1 = face_info[q1fid]['centre']
        facecentre2 = face_info[q2fid]['centre']
        direction1 = blockcentre-facecentre1
        direction2 = blockcentre-facecentre2

        v04 = q2verts[0] - q1verts[0]
        scalarProd1 = direction1.dot(normal1)
        scalarProd2 = direction2.dot(normal2)
        scalarProd3 = normal1.dot(v04)

        if scalarProd1*scalarProd2 > 0.: # make quad1 and quad2 rotate in the same direction
            quad2 = [quad2[0], quad2[-1], quad2[-2], quad2[-3]]
            normal2 *= -1.0

        if scalarProd3 < 0.: # Maintain righthanded system in each block
            tmp = list(quad2)
            quad2 = list(quad1)
            quad1 = tmp

        for nid,n in enumerate(quad1): #check that all edges are present
            if not (([n,quad2[nid]] in edges) or ([quad2[nid],n] in edges)):
                if len(logFileName) > 0:
                    logFile.write('one block did not have all edges! ' + str(quad1) + str(quad2) + '\n')
                is_a_real_block = False
                break
        if not is_a_real_block:
            continue
   # more sanity...
        scale = v04.magnitude * normal1.magnitude
        if (abs(scalarProd3/scale) < 0.01): # abs(sin(alpha)) < 0.01, where alpha is angle for normal1 and v04
            if len(logFileName) > 0:
                logFile.write('flat block ruled out!' + str(quad1) + str(quad2) + '\n')
            continue

        if is_a_real_block: # this write-out only works if blenders own vertex numbering starts at zero!! seems to work...
            offences.append(0)
            block_centres.append(blockcentre)

            vl = quad1 + quad2
            formalBlocks.append(vl) # list of verts defining the block in correct order
# formalBlocks are blocks that hava formal block structure and are not flat. Still in an O-mesh there are more formal
# blocks present than what we want. More filtering...

    for bid, vl in enumerate(formalBlocks):
        fs = []
        fs.append(vl[0:4])
        fs.append(vl[4:8])
        fs.append([vl[0], vl[1], vl[5], vl[4]])
        fs.append([vl[1], vl[2], vl[6], vl[5]])
        fs.append([vl[2], vl[3], vl[7], vl[6]])
        fs.append([vl[3], vl[0], vl[4], vl[7]])
        blockcentre = block_centres[bid]
        for f in fs:
            fid, tmp = findFace(faces_as_list_of_nodes, f)
            normal = face_info[fid]['normal']
            facecentre = face_info[fid]['centre']
            direction = normal.dot((blockcentre-facecentre))
            if direction >= 0.:
                face_info[fid]['pos'].append(bid)
            else:
                face_info[fid]['neg'].append(bid)
    for f in face_info:  # Not more than two blocks on each side of a face. If a block scores too high in 'offences' it will be ruled out
        if len(face_info[f]['pos'])>1:
            for bid in face_info[f]['pos']:
                offences[bid] += 1
        if len(face_info[f]['neg'])>1:
            for bid in face_info[f]['neg']:
                offences[bid] += 1
    block_print_out = []
    for bid, vl in enumerate(formalBlocks):
        if offences[bid] <= 3 and not all( v in disabled for v in vl ):
            block_print_out.append(vl)
            i_edges = [edge(vl[0],vl[1]), edge(vl[2],vl[3]), edge(vl[4],vl[5]), edge(vl[6],vl[7])]
            j_edges = [edge(vl[1],vl[2]), edge(vl[3],vl[0]), edge(vl[5],vl[6]), edge(vl[7],vl[4])]
            k_edges = [edge(vl[0],vl[4]), edge(vl[1],vl[5]), edge(vl[2],vl[6]), edge(vl[3],vl[7])]
#            i_edges = [[vl[0],vl[1]], [vl[2],vl[3]], [vl[4],vl[5]], [vl[6],vl[7]]]
#            j_edges = [[vl[1],vl[2]], [vl[3],vl[0]], [vl[5],vl[6]], [vl[7],vl[4]]]
#            k_edges = [[vl[0],vl[4]], [vl[1],vl[5]], [vl[2],vl[6]], [vl[3],vl[7]]]
            dependent_edges.append(i_edges) #these 4 edges have the same resolution
            dependent_edges.append(j_edges) #these 4 edges have the same resolution
            dependent_edges.append(k_edges) #these 4 edges have the same resolution
            for e in range(4):
                if not i_edges[e] in all_edges:
                    all_edges.append(i_edges[e])
                if not j_edges[e] in all_edges:
                    all_edges.append(j_edges[e])
                if not k_edges[e] in all_edges:
                    all_edges.append(k_edges[e])
        else:  # Dont let non-allowed blocks to stop definition of patch names
            for f in face_info:
                if bid in face_info[f]['pos']:
                    ind = face_info[f]['pos'].index(bid)
                    face_info[f]['pos'].pop(ind)
                if bid in face_info[f]['neg']:
                    ind = face_info[f]['neg'].index(bid)
                    face_info[f]['neg'].pop(ind)
    # stime = time.time()
    #this is the second most time consuming step
    still_coupling = True
    while still_coupling:
        still_coupling = couple_edges(dependent_edges)
    # blockBuilder2.couple_edges(dependent_edges)
    # print('still coupling, t',time.time() - stime)

    for es, edgeSet in enumerate(dependent_edges): # remove duplicates in lists
        dependent_edges[es] = removedup(edgeSet)
    return logFile, block_print_out, dependent_edges, face_info, all_edges, faces_as_list_of_nodes
