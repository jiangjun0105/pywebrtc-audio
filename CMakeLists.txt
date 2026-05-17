cmake_minimum_required(VERSION 3.15)
project(pywebrtc_audio LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_subdirectory(vendor/webrtc_audio)

find_package(pybind11 CONFIG REQUIRED)
pybind11_add_module(_webrtc_audio bindings/webrtc_audio_bindings.cpp)
target_link_libraries(_webrtc_audio PRIVATE webrtc_audio_static)
target_include_directories(_webrtc_audio PRIVATE vendor/webrtc_audio)

install(TARGETS _webrtc_audio DESTINATION pywebrtc_audio)
