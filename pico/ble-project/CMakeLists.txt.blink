cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)

project(test_project C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
# Setting the device to Pico-W
set(PICO_BOARD pico_w)

pico_sdk_init()

# Note: The space between the name and the file is CRITICAL; can cause a blank unable to find file error
#add_executable(test test.c)
add_executable(blink blink.c)

#pico_enable_stdio_usb(test 1)
#pico_enable_stdio_uart(test 1)

pico_enable_stdio_usb(blink 1)
pico_enable_stdio_uart(blink 1)

#pico_add_extra_outputs(test)
pico_add_extra_outputs(blink)

#target_link_libraries(test pico_stdlib)
target_link_libraries(blink pico_stdlib pico_cyw43_arch_none)
