cmake_minimum_required(VERSION 3.28.0...3.28.0 FATAL_ERROR)

project(SlicerICHTriage)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/LoveTechwCat/ich-triage/tree/main/services/slicer-ich-triage")
set(EXTENSION_CONTRIBUTORS "LoveTechwCat (ich-triage)")
set(EXTENSION_DESCRIPTION "Radiologist module of the ICH (intracerebral hemorrhage) AI triage system.")
# TODO: set before the extension is published.
set(EXTENSION_ICONURL "")
set(EXTENSION_SCREENSHOTURLS "")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(ICHTriage)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
