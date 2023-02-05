import tempfile
import os
import numpy as np
import subprocess
import shutil
import itertools
import glob
from . import utils
class PreviewMesh():
    def __init__(self, folder=None):
        #if not shutil.which('blockMesh'):
        #    # raise RuntimeError('ERROR: Could not find blockMesh! Please source OpenFOAM in terminal and start Blender from that terminal so that BlockMeshMG finds blockMesh command.')
        #else:
        #    self.blockMeshbin = 'blockMesh'
        if folder:
            if os.path.isfile(folder):
                folder = os.path.dirname(folder)
            print("Exporting to directory " + str(folder))
            if not os.path.isdir(folder):
                os.mkdir(folder)
            if not os.path.isdir(os.path.join(folder, 'constant')):
                os.mkdir(os.path.join(folder, 'constant'))
            if not os.path.isdir(os.path.join(folder, 'constant', 'geometry')):
                os.mkdir(os.path.join(folder, 'constant', 'geometry'))
            if not os.path.isdir(os.path.join(folder, 'system')):
                os.mkdir(os.path.join(folder, 'system'))
            self.blockMeshDictPath = os.path.join(folder, 'system', 'blockMeshDict')
            self.geomPath = os.path.join(folder, 'constant', 'geometry')
            # blockMesh requires controlDict, create one if there is none
            if not os.path.isfile(os.path.join(folder, 'system', 'controlDict')):
                cd = open(os.path.join(folder, 'system', 'controlDict'), 'w')
                cd.write(self.header())
        else:
            self.tempdir = tempfile.mkdtemp()
            self.blockMeshDictPath = os.path.join(self.tempdir, 'system', 'blockMeshDict')
            os.mkdir(os.path.join(self.tempdir, 'constant'))
            os.mkdir(os.path.join(self.tempdir, 'constant', 'polyMesh'))
            self.geomPath = os.path.join(self.tempdir, 'constant', 'geometry')
            os.mkdir(self.geomPath)
            os.mkdir(os.path.join(self.tempdir, 'system'))
            os.mkdir(os.path.join(self.tempdir, '0'))
            cd = open(os.path.join(self.tempdir, 'system', 'controlDict'), 'w')
            cd.write(self.header())
            print('OpenFOAM temp directory: {}'.format(self.tempdir))

    def writeBlockMeshDict(self, verts, convertToMeters, boundaries, polyLines, edgeInfo, blockNames, blocks, dependent_edges,\
            projections):
        bmFile = open(self.blockMeshDictPath,'w')
        bmFile.write(self.header())
        bmFile.write('\ngeometry\n{\n')
        for g in projections['geo']:
            bmFile.write('   {geo}\n   {{\n      type triSurfaceMesh;\n      file "{geo}.stl";\n   }}\n'.format(geo=g))

        bmFile.write("}\nvertices\n(\n")
        for i,v in enumerate(verts):
            if i in projections['vert2surf']:
                bmFile.write('    project ({} {} {}) ({})\n'.format(*v,projections['vert2surf'][i]))
            else:
                bmFile.write('    ({} {} {})\n'.format(*v))

        bmFile.write(");\nedges\n(\n")
        for key, value in projections['edge2surf'].items():
            bmFile.write('    projectCurve {} {} ({})\n'.format(*key, value))
        for pl in polyLines:
            bmFile.write(pl)

        bmFile.write(");\nfaces\n(\n")
        for key, value in projections['face2surf'].items():
            # for v in value:
            bmFile.write('    project ({} {} {} {}) {}\n'.format(*key,value))

        bmFile.write(");\nblocks\n(\n")


        NoCells = 0
        for bid, (vl, blockName) in enumerate(zip(blocks, blockNames)):
            edges = [(vl[e[0]],vl[e[1]]) for e in [(0,1),(3,2),(7,6),(4,5),(0,3),(1,2),(5,6),(4,7),(0,4),(1,5),(2,6),(3,7)]]
            gradingStr = ""
            for ei in edges:
                e = edgeInfo[ei]
                gradingStr+='\n(\n ({:.6g} {:.6g} {:.6g}) ({:.6g} {:.6g} {:.6g}) ({:.6g} {:.6g} {:.6g}) '.format(
                e["l1"],e["n1"],e["ratio1"],\
                e["dL"],e["nL"],1,\
                e["l2"],e["n2"],1/e["ratio2"]) + '\n)'
            ires = edgeInfo[edges[0]]["N"]
            jres = edgeInfo[edges[4]]["N"]
            kres = edgeInfo[edges[8]]["N"]

            NoCells += ires*jres*kres
            bmFile.write('// block id {} \nhex ({} {} {} {} {} {} {} {}) '.format(bid,*vl) \
                       + blockName + ' ({} {} {}) '.format(ires,jres,kres)\
                       + 'edgeGrading (' + gradingStr + '\n)\n' )
        bmFile.write(');\n\npatches\n(\n')
        for b in boundaries:
            bmFile.write('     {} {}\n    (\n'.format(b['type'],b['name'] ))
            for v in b['faceVerts']:
                bmFile.write('        ({} {} {} {})\n'.format(*v))
            bmFile.write('    )\n')
        bmFile.write(');')
        bmFile.close()
        return NoCells


    def readHeader(self,dicfile):
        numberOfFields = 0
        startLine = False
        with open(dicfile) as fin:
            for lidx,line in enumerate(fin):
                if not numberOfFields:
                    try:
                        numberOfFields = int(line)
                    except ValueError:
                        pass
                if '(' in line:
                    startLine = lidx + 1
                    break
        return startLine, numberOfFields

    def readBoundaries(self,files):
        data = []
        readingField = False
        for line in files:
            if not line.strip():
                continue
            if not readingField and line.strip() == '{':
                readingField = True
            elif not readingField:
                temp = dict()
                temp['name']= line.strip()
            elif readingField and 'type' in line:
                temp['type'] = line.strip().split()[1][:-1]
            elif readingField and 'nFaces' in line:
                temp['nFaces'] = int(line.strip().split()[1][:-1])
            elif readingField and 'startFace' in line:
                temp['startFace'] = int(line.strip().split()[1][:-1])
            elif readingField and line.strip() == '}':
                data.append(temp)
                readingField = False
            elif not readingField and line.strip() == ')':
                break
        return data

    def getPoints(self,faces=None):
        pointsFile = os.path.join(self.tempdir, 'constant', 'polyMesh', 'points')
        startLine, numberofLines = self.readHeader(pointsFile)
        convertfnc1 = lambda x: float(x[1:])
        convertfnc2 = lambda x:float(x[:-1])
        with open(pointsFile,'rb') as fin:
            points = np.genfromtxt(itertools.islice(fin,startLine,startLine+numberofLines),\
                converters={0:convertfnc1,2:convertfnc2},dtype=float)
        if faces!=None:
            pidxs = np.unique(np.ravel(faces))
            points = points[pidxs]
        points=points.tolist()
        return points

    def getFaces(self):
        facesFile = os.path.join(self.tempdir, 'constant', 'polyMesh', 'faces')
        startLine, numberofLines = self.readHeader(facesFile)
        convertfnc1 = lambda x: int(x[2:])
        convertfnc2 = lambda x: int(x[:-1])
        with open(facesFile,'rb') as fin:
            faces = np.genfromtxt(itertools.islice(fin,startLine,startLine+numberofLines),\
                converters={0:convertfnc1,3:convertfnc2},dtype=int)
        faces = faces.tolist()
        return faces

    def getBCFaces(self,internalCells):
        faces = self.getFaces()
        bcifaces = faces
        bcfaces = faces
        if not internalCells:
            boundaryFile = os.path.join(self.tempdir, 'constant', 'polyMesh', 'boundary')
            startLine, boundaries = self.readHeader(boundaryFile)
            with open(boundaryFile) as fin:
                fields = self.readBoundaries(itertools.islice(fin,startLine,None))
            self.fields = fields
            bcifaces = []
            bcfaces=[]
            for bc in sorted(fields, key=lambda k: k['startFace']):
                bcfaces.extend(faces[bc['startFace']:bc['startFace']+bc['nFaces']])
            bcifaces = np.array(bcfaces,dtype=int)
            bcifaces = np.unique(bcifaces.ravel(),return_inverse=True)[1].reshape(bcifaces.shape)
            bcifaces = bcifaces.astype(int).tolist()
        return bcfaces,bcifaces

#this is faster
    def getBCFaces2(self,internalCells):
        facesFile = os.path.join(self.tempdir, 'constant', 'polyMesh', 'faces')
        startLine, numberofLines = self.readHeader(facesFile)
        faces = open(facesFile).readlines()
        faces = faces[startLine:startLine+numberofLines]
        subs = lambda s: list(map(int,s.__getitem__(slice(2,-2)).split()))
        faces = list(map(subs, faces))
        boundaryFile = os.path.join(self.tempdir, 'constant', 'polyMesh', 'boundary')
        startLine, boundaries = self.readHeader(boundaryFile)
        with open(boundaryFile) as fin:
            fields = self.readBoundaries(itertools.islice(fin,startLine,None))
        self.fields = fields
        bcifaces = []
        bcfaces=[]
        for bc in sorted(fields, key=lambda k: k['startFace']):
            bcfaces.extend(faces[bc['startFace']:bc['startFace']+bc['nFaces']])
        bcifaces = np.array(bcfaces,dtype=int)
        bcifaces = np.unique(bcifaces.ravel(),return_inverse=True)[1].reshape(bcifaces.shape)
        bcifaces = bcifaces.astype(int).tolist()
        return bcfaces,bcifaces

    def runBlockMesh(self):
        subprocess.call([self.blockMeshbin,'-case',self.tempdir],stdout=subprocess.PIPE)

    def runMesh(self,runBlockMesh=True,internalCells=False):
        if not shutil.which('blockMesh'):
            return [], []
        if runBlockMesh:
            self.blockMeshbin = 'blockMesh'
            print('running blockMesh')
            self.runBlockMesh()
        faces, bcifaces=self.getBCFaces2(internalCells)
        points=self.getPoints(faces)
        shutil.rmtree(self.tempdir)
        return points, bcifaces

    def header(self):
        return \
        '''
/*--------------------------------*- C++ -*----------------------------------*/

// File was generated by SwiftBlock, a Blender 3D addon.

FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

deltaT          1;

writeInterval   1;



// ************************************************************************* //

'''
