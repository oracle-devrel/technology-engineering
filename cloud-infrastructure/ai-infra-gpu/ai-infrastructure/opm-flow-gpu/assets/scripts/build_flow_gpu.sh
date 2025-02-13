#!/bin/bash

for repo in opm-common opm-grid
do
    git clone https://github.com/OPM/$repo.git
    mkdir $repo/build && cd $repo/build
    cmake ..
    make -j 8
    cd ../..
done

git clone https://github.com/OPM/opm-simulators.git
mkdir opm-simulators/build && cd opm-simulators/build
cmake .. -DUSE_GPU_BRIDGE=OFF
make -j 8
cd ../..

git clone https://github.com/OPM/opm-upscaling.git
mkdir opm-upscaling/build && cd opm-upscaling/build
cmake ..
make -j 8
cd ../..



/usr/include/c++/11/bits/std_function.h:435:145: error: parameter packs not expanded with ‘...’:
  435 |         function(_Functor&& __f)
      |                                                                                                                                                 ^
/usr/include/c++/11/bits/std_function.h:435:145: note:         ‘_ArgTypes’
/usr/include/c++/11/bits/std_function.h:530:146: error: parameter packs not expanded with ‘...’:
  530 |         operator=(_Functor&& __f)
      |                                                                                                                                                  ^
/usr/include/c++/11/bits/std_function.h:530:146: note:         ‘_ArgTypes’
make[2]: *** [CMakeFiles/opmsimulators.dir/build.make:2680: CMakeFiles/opmsimulators.dir/opm/simulators/linalg/gpuistl/detail/vector_operations.cu.o] Error 1
make[2]: *** Waiting for unfinished jobs....
make[1]: *** [CMakeFiles/Makefile2:530: CMakeFiles/opmsimulators.dir/all] Error 2
make: *** [Makefile:146: all] Error 2