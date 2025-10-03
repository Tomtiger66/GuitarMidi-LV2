
add_executable(frugal_test main.cpp)
find_package(OpenMP REQUIRED)
if (OpenMP_CXX_FOUND)
    target_link_libraries(frugal_test PRIVATE ${OpenMP_CXX_LIBRARIES})
    target_compile_options(frugal_test PRIVATE ${OpenMP_CXX_FLAGS})
endif()
target_link_libraries(frugal_test PRIVATE fdeep)