# this makefile runs cmake to build the project and then copies the resulting .so file to the correct location for use as a LV2 plugin


all:
	mkdir -p build
	cd build && cmake  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=~/.lv2 ..
	cd build && cmake --build .
	cd build && cmake --install .