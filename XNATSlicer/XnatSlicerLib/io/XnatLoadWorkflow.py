from XnatUtils import *
from __main__ import vtk, ctk, qt, slicer

import os
import sys



from XnatLoader import *
from XnatLoader_Analyze import *
from XnatLoader_Dicom import *
from XnatLoader_File import *
from XnatLoader_Mrb import *
from XnatPopup import *



comment = """
XnatLoadWorkflow is effectively a factory for various loader classes.  
Loader types are determined by the treeViewItem being clicked in the 
XnatLoadWorkflow function 'beginWorkflow'.  

TODO:
"""




class XnatLoadWorkflow(object):
    """ Parent Load workflow class to: XnatDicomLoadWorkflow, 
        XnatMrbLoadWorkflow, and XnatFileLoadWorkflow.
    """

    
    def __init__(self, MODULE):
        """ Parent init.
        """
        self.MODULE = MODULE       
        self.loadFile = None
        self.newMRMLFile = None
        self.currRemoteHost = None


        self.skipEmptySceneCheck = False
        self._src = None


        
        #--------------------------------
        # Popups
        #--------------------------------
        self.areYouSureDialog = qt.QMessageBox()
        self.areYouSureDialog.setIcon(4)
        self.areYouSureDialog.setText("You are about to load all readable scans from '**HERE**'.\n" +  
                                      "This may take several minutes.\n" +
                                      "Are you sure you want to continue?")
        self.areYouSureDialog.addButton(qt.QMessageBox.Yes)
        self.areYouSureDialog.addButton(qt.QMessageBox.No)
        self.areYouSureDialog.connect('buttonClicked(QAbstractButton*)', self.beginWorkflow)



        self.XnatDownloadPopup = XnatDownloadPopup()
        
        self.clearScenePopup = XnatClearScenePopup()
        self.clearScenePopup.connect('buttonClicked(QAbstractButton*)', self.clearSceneButtonClicked) 

        self.preDownloadPopup = XnatTextPopup('Checking files...')
        self.postDownloadPopup = XnatTextPopup('Processing.  Data will load automatically.')


        self.setIOCallbacks()



    def setIOCallbacks(self):
        """
        """
        
        #--------------------------------
        # XnatIO Callbacks
        #--------------------------------

        # Download cancelled
        def downloadCancelled(_xnatSrc):
            zeroCount = 0
            for key, state in self.downloadState.iteritems():
                if state == 0: zeroCount += 1
            if zeroCount == len(self.downloadState):
                self.XnatDownloadPopup.hide()
            slicer.app.processEvents()
        self.MODULE.XnatIo.setCallback('downloadCancelled', downloadCancelled)


        # Downloading
        def downloading(_xnatSrc, size = 0):
            self.XnatDownloadPopup.updateDownload(_xnatSrc.split('?format=zip')[0], size)
            slicer.app.processEvents()
        self.MODULE.XnatIo.setCallback('downloading', downloading)


        # download start
        def downloadStarted(_xnatSrc, size = 0):
            self.XnatDownloadPopup.setSize(_xnatSrc.split('?format=zip')[0], size)
            slicer.app.processEvents()
        self.MODULE.XnatIo.setCallback('downloadStarted', downloadStarted)

        # download finished
        def downloadFinished(_xnatSrc):
            self.XnatDownloadPopup.setComplete(_xnatSrc.split('?format=zip')[0])
            slicer.app.processEvents()
        self.MODULE.XnatIo.setCallback('downloadFinished', downloadFinished)


        
        
    
    def terminateLoad(self, warnStr):
        """ Notifies the user that they will terminate the load.
            Reenables the viewer UI.
        """
        qt.QMessageBox.warning( None, warnStr[0], warnStr[1])




    def clearSceneButtonClicked(self, button):
        """
        """
        if 'yes' in button.text.lower():
            self.MODULE.XnatView.sessionManager.clearCurrentSession()
            slicer.app.mrmlScene().Clear(0)
            self.skipEmptySceneCheck = True
            self.beginWorkflow()

            

    def beginWorkflow(self, src = None):
        """ This function is the first to be called
            when the user clicks on the "load" button (right arrow).
            The class that calls 'beginWorkflow' has no idea of the
            workflow subclass that will be used to load
            the given XNAT node.  Those classes (which inherit from
            XnatLoadWorkflow) will be called on in this function.
        """


        if not self._src:
            self._src = src


            
        #------------------------
        # Show clearSceneDialog
        #------------------------
        if '/scans/' in self._src:
            splitter = self._src.split('/scans/')
            self._src = splitter[0] + '/scans/' + splitter[1].split('/')[0] + '/files'


            
        #------------------------
        # Show clearSceneDialog
        #------------------------
        if not XnatUtils.isCurrSceneEmpty() and not self.skipEmptySceneCheck:
            self.clearScenePopup.show()
            return


    
        #------------------------    
        # Clear download queue
        #------------------------
        self.MODULE.XnatIo.clearDownloadQueue()

        

        #------------------------
        # Set Download finished callbacks
        #------------------------        
        downloadFinishedCallbacks = []
        def runDownloadFinishedCallbacks():
            self.XnatDownloadPopup.hide()
            self.postDownloadPopup.show()
            for callback in downloadFinishedCallbacks:
                print "DOWNLOAD FINISHED!"
                callback()
                slicer.app.processEvents()
            self.postDownloadPopup.hide()

        
        #------------------------
        # Show download popup
        #------------------------  
        print "Initializing download..."
        self.preDownloadPopup.show()


        
        #------------------------
        # Get loaders, add to queue
        #------------------------  
        for loader in self.loaderFactory(self._src):
            self.MODULE.XnatIo.addToDownloadQueue(loader.loadArgs)
            downloadFinishedCallbacks.append(loader.load)             


        #------------------------
        # Run loaders
        #------------------------ 
        self.preDownloadPopup.hide()
        self.XnatDownloadPopup.show()
        self.MODULE.XnatIo.startDownloadQueue(onQueueFinished = runDownloadFinishedCallbacks)
      
            
        #------------------------
        # Enable XnatView
        #------------------------
        self.MODULE.XnatView.setEnabled(True)
        self.lastButtonClicked = None
    


        
    def loaderFactory(self, _src):
        """ Returns the appropriate set of loaders after analyzing the
            '_src' argument.

            Arguments:
            _src The URI to create loaders from.

            Returns:
            A loader list.
            
        """

        print "\n\nLOADER FACTORY"
        loaders = []


        
        #------------------------
        # Open popup
        #------------------------
        if '/scans/' in _src or '/files/' in _src:
            print "OPENING POPUP ROW", _src
            self.XnatDownloadPopup.addDownloadRow(_src)
            


            
            
        #------------------------
        # '/files/' LEVEL 
        #------------------------
        if '/files/' in _src:
            
            # MRB
            if '/Slicer/files/' in _src:
                print "FOUND SLICER FILE"
                loaders.append(XnatLoader_Mrb(self.MODULE, _src))
                



        #------------------------
        # '/scans/' LEVEL 
        # 
        # Basically, look at the contents of the scan folder
        # and return the appropriate loader
        #------------------------
        elif '/scans/' in _src:

            # uri manipulation
            splitScan =  _src.split('/scans/')   
            scanSrc = splitScan[0] + '/scans/' + splitScan[1].split('/')[0] + '/files'
            print "SPLIT SCAN:", splitScan, '\n\t',scanSrc
            # query xnat for folder contents
            contentUris = self.MODULE.XnatIo.getFolderContents(scanSrc, metadataTags = ['URI'])['URI']
            print "CONTENT URIS", contentUris
            # get file uris and sort them by type
            loadables = XnatUtils.sortLoadablesByType(contentUris)
            print "LOADABLES", loadables
            # cycle through the loadables and
            # create the loader for each loadable list.
            for loadableType, loadableList in loadables.iteritems():
                if len(loadableList) > 0:
                    if loadableType == 'analyze':
                        loaders.append(XnatLoader_Analyze(self.MODULE, _src, loadables[loadableType]))
                    if loadableType == 'dicom':      
                        loaders.append(XnatLoader_Dicom(self.MODULE, _src, loadables[loadableType]))
                    if loadableType == 'misc':
                        loaders.append(XnatLoader_File(self.MODULE, _src, loadables[loadableType]))


                        
        #------------------------
        # '/experiments/' LEVEL 
        #
        # Basically, recurse this function after querying for the 
        # scans in it.
        #------------------------
        elif '/experiments/' in _src and not '/scans/' in _src and not '/resources/' in _src:

            # Uri manipulation
            splitExpt = _src.split('/experiments/')
            exptSrc = splitExpt[0] + '/experiments/' + splitExpt[1].split('/')[0] + '/scans'
            print "SPLIT Expt:", splitExpt, '\n\t',exptSrc
            # Query for Scan IDs from XNAT.
            contents = self.MODULE.XnatIo.getFolderContents(exptSrc, metadataTags = ['ID'])
            print "SCAN IDS", contents
            # Recurse this function for every scan.
            for scanId in contents['ID']:
                scanSrc = exptSrc + '/' + scanId + '/files'
                print "\n\nLOADING SCAN SOURCE", scanSrc
                loaders += self.loaderFactory(scanSrc)

            # Return loaders
            return loaders
                
            
        return loaders
