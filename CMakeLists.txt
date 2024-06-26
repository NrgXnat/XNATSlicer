cmake_minimum_required(VERSION 2.8.9)

#-----------------------------------------------------------------------------
if(NOT Slicer_SOURCE_DIR)
  set(EXTENSION_NAME XNATSlicer)
  set(EXTENSION_HOMEPAGE "https://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/XNATSlicer")
  set(EXTENSION_CATEGORY "Remote")
  set(EXTENSION_CONTRIBUTORS "Rick Herrick (Washington University in St. Louis), Sunil Kumar (Moka Creative LLC, Washington University in St. Louis), Dan Marcus (Washington University in St. Louis), Steve Pieper (Isomics)")
  set(EXTENSION_DESCRIPTION "Secure GUI-based IO with any XNAT server.")
  set(EXTENSION_ICONURL "https://raw.github.com/NrgXnat/XNATSlicer/master/XNATSlicer/Resources/Icons/XNATSlicer-MarketIcon.png")
  set(EXTENSION_SCREENSHOTURLS "https://raw.github.com/NrgXnat/XNATSlicer/master/XNATSlicer/Resources/Images/UserDesc_MainPanel.png")
endif()

#-----------------------------------------------------------------------------
if(NOT Slicer_SOURCE_DIR)
  find_package(Slicer REQUIRED)
  include(${Slicer_USE_FILE})
endif()

#-----------------------------------------------------------------------------
add_subdirectory(XNATSlicer)

#-----------------------------------------------------------------------------
if(NOT Slicer_SOURCE_DIR)
  include(${Slicer_EXTENSION_CPACK})
endif()
