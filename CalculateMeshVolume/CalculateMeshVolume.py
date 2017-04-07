import numpy as np
from datetime import datetime
from threading import Thread
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing import Process, Queue
import os


# Puthon 2.7 (64 bit, Anaconda full distro)
# numby 1.11.3
# scipy 0.18.1


from enum import Enum
class CalculationTechniques(Enum): 
    LIST_COMPREHENSION = 1
    FOR_LOOP = 2 
    FOUR_POOL_THREADS = 3
    FOUR_THREADS = 4
    FOUR_PROCESSES = 5


def calculate_mesh_volume_per_facet(facet):
    """
    Calculate the mesh volume for one facet.  Build for fine-grained thread parallellism.
    """
    return facet[0].dot(np.cross(facet[1], facet[2]))


def calculate_mesh_volume_per_core(mesh, vol_per_facet, start=0, step=1):
    """
    Calculate the mesh volume for a subset of the mesh. Build for large-grained thread parallellism.
    """
    facet_count = mesh.shape[0]

    for idx in range(start, facet_count, step):
        facet = mesh[idx]
        vol_per_facet[idx] = facet[0].dot(np.cross(facet[1], facet[2]))


def calculate_mesh_volume_per_core_no_shared_memory(mesh, queue, start=0, step=1):
    """
    Calculate the mesh volume for a subset of the mesh. Build for large-grained process parallellism.
    """
    facet_count = mesh.shape[0]
    vol_per_facet = [0.0] * facet_count

    for idx in range(start, facet_count, step):
        facet = mesh[idx]
        vol_per_facet[idx] = facet[0].dot(np.cross(facet[1], facet[2]))

    queue.put(vol_per_facet)


def calculate_mesh_volume(mesh, technique, description=None, expected_answer=None):
    """
    Using the algorith discussed here:

    EFFICIENT FEATURE EXTRACTION FOR 2D/3D OBJECTS
    IN MESH REPRESENTATION
    Cha Zhang and Tsuhan Chen
    """
    facet_count = mesh.shape[0]
    volume = 0.0

    if technique is CalculationTechniques.LIST_COMPREHENSION:
        # list comprehension!
        vol_per_facet = [facet[0].dot(np.cross(facet[1], facet[2])) for facet in mesh]
        volume = sum(vol_per_facet) / 6.0

    elif technique is CalculationTechniques.FOR_LOOP:
        # express in a less dense fashion and comment where parallization would be possible
        vol_per_facet = [0.0] * facet_count
        for idx, facet in enumerate(mesh):
            # each loop iteration can be done in parallel. we are on the python side of the fence,
            # so it is unclear if the same set of efficiencies that are on the C/C++ sife of the fence can be reached.

            # if the target processor has a vector unit, the below code is implemented in C/C++ and the target compiler recognizes the vector op, 
            # the below dot and cross products executed on a vector unit should be faster
            vol_per_facet[idx] = facet[0].dot(np.cross(facet[1], facet[2]))

        volume = sum(vol_per_facet) / 6.0

    elif technique is CalculationTechniques.FOUR_POOL_THREADS:
        # create 4 threads
        # each thread will be feed a facet at a time, until all factes have been processed
        # likely this is too fine-grained 
        vol_per_facet = [0.0] * facet_count
        pool = ThreadPool(4)
        vol_per_facet = pool.map(calculate_mesh_volume_per_facet, mesh)
        pool.close()
        pool.join()
        # vol_per_facet should have the same members as above (but order may be different?)
        volume = sum(vol_per_facet) / 6.0

    elif technique is CalculationTechniques.FOUR_THREADS:
        vol_per_facet = [0.0] * facet_count
        # create 4 large-grained threads, each will handle 1/4 of the mesh
        step = 4
        start = 0
        t1 = Thread(target=calculate_mesh_volume_per_core, args=(mesh, vol_per_facet, start, step))
        start = 1
        t2 = Thread(target=calculate_mesh_volume_per_core, args=(mesh, vol_per_facet, start, step))
        start = 2
        t3 = Thread(target=calculate_mesh_volume_per_core, args=(mesh, vol_per_facet, start, step))
        start = 3
        t4 = Thread(target=calculate_mesh_volume_per_core, args=(mesh, vol_per_facet, start, step))

        t1.start()
        t2.start()
        t3.start()
        t4.start()

        t1.join()
        t2.join()
        t3.join()
        t4.join()

        volume = sum(vol_per_facet) / 6.0

    elif technique is CalculationTechniques.FOUR_PROCESSES:
        # I read it on The Internet:
        #   "CPython can use threads only for I\O waits due to GIL. 
        #   If you want to benefit from multiple cores for CPU-bound tasks, use multiprocessing."

        # explore large-grained parallellism via having four processes, each will handle 1/4 of the mesh

        # processes do not share data directly with each other.  
        # use the Queue object to communicate (via a hidden pipe), from the child to the parent process.

        vol_per_facet = [0.0] * facet_count

        step = 4

        queue1 = Queue()
        start = 0
        p1 = Process(target=calculate_mesh_volume_per_core_no_shared_memory, args=(mesh, queue1, start, step))

        queue2 = Queue()
        start = 1
        p2 = Process(target=calculate_mesh_volume_per_core_no_shared_memory, args=(mesh, queue2, start, step))

        queue3 = Queue()
        start = 2
        p3 = Process(target=calculate_mesh_volume_per_core_no_shared_memory, args=(mesh, queue3, start, step))

        queue4 = Queue()
        start = 3
        p4 = Process(target=calculate_mesh_volume_per_core_no_shared_memory, args=(mesh, queue4, start, step))

        p1.start()
        p2.start()
        p3.start()
        p4.start()

        # wait on the queue.put() which is at the end of calculate_mesh_volume_per_core
        vol_per_facet1 = queue1.get();
        vol_per_facet2 = queue2.get();
        vol_per_facet3 = queue3.get();
        vol_per_facet4 = queue4.get();

        p1.join()
        p2.join()
        p3.join()
        p4.join()

        for idx in range(0, facet_count):
            vol_per_facet[idx] = vol_per_facet1[idx] or vol_per_facet2[idx] or vol_per_facet3[idx] or vol_per_facet4[idx]

        volume = sum(vol_per_facet) / 6.0

    print '{0} via {1}:\n\tFacet count is {2}.\n\tExpected answer is {3}.\n\tCalculate mesh volume is {4}.\n\n'.format(description, str(technique), facet_count, expected_answer, volume)


inputs = [{'file':os.path.join('.', 'input', 'unit_sq.npy') ,               'description':'mesh volume of a unit square',            'expected_volume':0.0},
          {'file':os.path.join('.', 'input', 'unit_cube_qppp.npy'),         'description':'mesh volume of a unit cube',              'expected_volume':1.0},
          {'file':os.path.join('.', 'input', 'shell.npy'),                  'description':'mesh volume of a shell',                  'expected_volume':3.6586764273115655},
          {'file':os.path.join('.', 'input', 'Robot_Maker_Faire_65pc.npy'), 'description':'mesh volume of a Robot Maker Faire 65pc', 'expected_volume':43677.42582662092}]


if __name__ == '__main__':
    for input in inputs:
        mesh = np.load(input['file'])

        for technique in CalculationTechniques:
            start_time = datetime.now()
            calculate_mesh_volume(mesh, technique, input['description'], input['expected_volume'])
            stop_time = datetime.now()
            print 'elapsed time is {0}.\n\n'.format(stop_time - start_time)

