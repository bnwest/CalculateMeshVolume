# Mesh volume code challenge

Here are the tasks:

1. Write a function that takes a mesh array (described below) and calculates the mesh's volume.
2. Write a unit test for the volume function in #1.
3. Write the title and text for a pull request you would open to merge this code.
4. Appropriately document the functions, modules, etc. you write as part of this code challenge.
5. Develop this code in a git repository.

When you are finished with this challenge, compress (tar, zip, etc.) the directory containing the git repo in which you developed the code and send the compressed file back. You can include the pull request writeup as a plain text file in the compressed repo. You don't need to include the sample mesh data in this repo, but you can if you like.

Three mesh arrays are included in this challenge; these are by way of example so you have some test data. The three arrays (and some information about them):

Filename = Robot_Maker_Faire_65pc.npy
Volume = 43677.42582662092

Filename: shell.npy
Volume = 3.6586764273115655

Filename: unit_cube_qppp.npy
Volume = 1.0

A [mesh](https://en.wikipedia.org/wiki/Polygon_mesh) is a way to represent a polyhedron with an arbitrary number of faces in memory. A mesh includes vertices, edges (connections between vertices), and facets (polygons comprising the surface defined by the mesh). The data included with this challenge are triangular meshes: i.e. all of the facets are triangles.

The mesh array is a numpy array with 3 axes. Each element along the 0th axis represents a facet of the mesh. The order of the facets is arbitrary. The elements along the 1st axis of the mesh represent a facet's vertices. The facet normal is defined by a right-handed traversal of the vertices: if you were to curl your right hand along the vertices as they are listed, your thumb would point in the direction of the facet normal. Finally, each vertex is a 3-vector pointing from the origin to the position of the vertex.

For example, the following numpy array would define a unit square on the x-y plane:

```python
import numpy as np

mesh = np.array([
    [[0, 0, 0],
    [1, 0, 0],
    [1, 1, 0]],

    [[0, 0, 0],
    [1, 1, 0],
    [0, 1, 0]]])
```

Two files are included for each mesh: the .npy file is in numpy array format. You should be able to use `numpy.load` to import the data. Also included is a file `unit_sq.npy` which is the same as the `mesh` array above. You can view the .stl files using [meshlab](http://meshlab.sourceforge.net/), or on their online viewer [meshlabjs](http://www.meshlabjs.net/). You do not need to write a parser for the STLs, they are just there so you can visualize the meshes you are working with.

You can (and should) leverage numpy and scipy functionality where you can. In other words, there's no need to re-implement a cross product function, data I/O functionality, etc.

The following versions of numpy and scipy are known to work with the included data:

Numpy: 1.10.2
Scipy: 0.16.0
