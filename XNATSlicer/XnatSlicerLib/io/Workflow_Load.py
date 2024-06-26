__author__ = "Sunil Kumar (kumar.sunil.p@gmail.com)"
__copyright__ = "Copyright 2014, Washington University in St. Louis"
__credits__ = ["Sunil Kumar", "Steve Pieper", "Dan Marcus"]
__license__ = "XNAT Software License Agreement " + \
              "(see: http://xnat.org/about/license.php)"
__version__ = "2.1.1"
__maintainer__ = "Rick Herrick"
__email__ = "herrickr@mir.wustl.edu"
__status__ = "Production"


# application
from __main__ import qt, slicer

# external
from MokaUtils import *
from Xnat import Xnat

# module
from Loader import *
from Loader_Analyze import *
from Loader_Dicom import *
from Loader_Mrb import *
from Popup import *
from SlicerUtils import *
from XnatSlicerUtils import *




class Workflow_Load(object):
    """ 
    Workflow_Load is effectively a factory for various loader classes.  
    Loader types are determined by the View item being clicked in the 
    Workflow_Load function 'beginWorkflow'.  
    
    Parent Load workflow class to: XnatDicomWorkflow_Load, 
    XnatMrbWorkflow_Load, and XnatFileWorkflow_Load.
    """

    
    def __init__(self, MODULE):
        """ 
        @param MODULE: The XNATSlicer module.
        @type MODULE: XnatSlicerWidget
        """
        self.MODULE = MODULE       
        self.loadFile = None
        self.newMRMLFile = None
        self.currRemoteHost = None


        self.skipEmptySceneCheck = False
        self._src = None
        self.loaders = {}

        
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
        self.XnatDownloadPopup.setCancelCallback(self.MODULE.XnatIo.cancelDownload)
        
        self.clearScenePopup = XnatClearScenePopup()
        self.clearScenePopup.connect('buttonClicked(QAbstractButton*)', self.__clearSceneButtonClicked) 

        # self.preDownloadPopup = XnatTextPopup('<b>Checking files...</b>')
        self.preDownloadPopup = qt.QMessageBox()
        self.areYouSureDialog.setIcon(4)
        self.preDownloadPopup.setText("Checking files...")
        self.postDownloadPopup = XnatTextPopup('<b>Processing.  Data will load automatically.</b>')



    def __sortLoadablesByType(self, fileUris):
        """
        Sorts a list of file uris by XNATSlicer loadable types.  Generally used 
        when multi-folder downloading is in effect.

        @param fileUris: The list of iles to sort..
        @type: list(string)

        @return: A dictionary where each key specifies the loadable type.
        @rtype: dict
        """
        
        filesByType = {
            'analyze': [],
            'dicom': [],
            'misc': [],
            'unknown': []
        }

        for fileUri in fileUris:
            if XnatSlicerUtils.isAnalyze(fileUri):
                filesByType['analyze'].append(fileUri)
            elif XnatSlicerUtils.isDICOM(fileUri):
                filesByType['dicom'].append(fileUri)
            elif XnatSlicerUtils.isMiscLoadable(fileUri):
                filesByType['misc'].append(fileUri)
            else:
                filesByType['unknown'].append(fileUri)

        return filesByType




    def __resetIOCallbacks(self):
        """ 
        Clears and sets the IO callbacks for the MODULE.XnatIO.
        Callbacks labeleled accordingly.
        """

        #--------------------------------
        # Clear IO Download queue
        #--------------------------------
        self.MODULE.XnatIo.clearDownloadQueue()



        #--------------------------------
        # START
        #--------------------------------
        def downloadStarted(_xnatSrc, size = 0):
            #print "\n\nDOWNLOAD START", self.XnatDownloadPopup.downloadRows, "\n\n"
            #if size > 0:
            self.XnatDownloadPopup.setSize(_xnatSrc.split('?format=zip')[0], size)
            slicer.app.processEvents()
        self.MODULE.XnatIo.onEvent('downloadStarted', downloadStarted)

        

        #--------------------------------
        # Downloading
        #--------------------------------
        def downloading(_xnatSrc, size = 0):
            self.XnatDownloadPopup.updateDownload(_xnatSrc.split('?format=zip')[0], size)
            slicer.app.processEvents()
        self.MODULE.XnatIo.onEvent('downloading', downloading)

        

        #--------------------------------
        # FINISHED
        #--------------------------------
        def downloadFinished(_xnatSrc):
            #
            # Update the popup
            #
            self.XnatDownloadPopup.setFinished(_xnatSrc.split('?format=zip')[0])
            slicer.app.processEvents()
        self.MODULE.XnatIo.onEvent('downloadFinished', downloadFinished)



        #--------------------------------
        # CANCELLED
        #--------------------------------
        def downloadCancelled(_xnatSrc, *args):
            
            #
            # Update the popup
            #
            self.XnatDownloadPopup.setCancelled(_xnatSrc.split('?format=zip')[0])

            #
            # Set loader to None if it pertains to the 
            # cancelled download
            #
            for key, loader in self.loaders.items():
                if loader and _xnatSrc in loader.loadArgs['src']:
                    self.loaders[key] = None

            if len(self.MODULE.XnatIo.downloadQueue) == 0:
                self.XnatDownloadPopup.hide()
                slicer.app.processEvents()
        self.MODULE.XnatIo.onEvent('downloadCancelled', downloadCancelled)


        #--------------------------------
        # FAILED (same as CANCELLED)
        #--------------------------------
        self.MODULE.XnatIo.onEvent('downloadFailed', downloadCancelled)

        
        
    
    def terminateLoad(self, *warnStrs):
        """ 
        Notifies the user that they will terminate the load.
        Reenables the viewer UI.

        @params: The warning strings (title, and message).
        """
        qt.QMessageBox.warning( None, warnStrs[0], warnStrs[1])




    def __clearSceneButtonClicked(self, button):
        """
        Callback for when the clear scene button is clicked.

        @param button: The button in the dialog that was clicked.
        @type button. qt.QAbstractButton
        """
        if 'yes' in button.text.lower():
            self.MODULE.View.sessionManager.clearCurrentSession()
            slicer.app.mrmlScene().Clear(0)
        
        self.clearScenePopup.hide()
        self.skipEmptySceneCheck = True
        self.beginWorkflow()
            

            

    def beginWorkflow(self, src = None):
        """ 
        This function is the first to be called
        when the user clicks on the "load" button (right arrow).
        The class that calls 'beginWorkflow' has no idea of the
        workflow subclass that will be used to load
        the given XNAT node.  Those classes (which inherit from
        Workflow_Load) will be called on in this function.

        @param src: The optional src file 
        @type src: str
        """


        if not self._src:
            self._src = src
        self._src = Xnat.path.makeXnatUrl(self.MODULE.XnatIo.host, self._src)

            
        #------------------------
        # Show clearSceneDialog
        #------------------------
        if '/scans/' in self._src:
            splitter = self._src.split('/scans/')
            self._src = splitter[0] + '/scans/' + splitter[1].split('/')[0] + '/files'


            
        #------------------------
        # Show clearSceneDialog
        #------------------------
        if not SlicerUtils.isCurrSceneEmpty() and not self.skipEmptySceneCheck:
            self.clearScenePopup.show()
            return


    
        #------------------------    
        # Clear download queue
        #------------------------
        self.__resetIOCallbacks()

        

        #------------------------
        # Set Download finished callbacks
        #------------------------        
        def onDownloadFinished():
            self.XnatDownloadPopup.hide()
            self.postDownloadPopup.show()
            for key, loader in self.loaders.items():
                #print "DOWNLOAD FINISHED!"
                if loader:
                    loader.load()
                    slicer.app.processEvents()
                    self._src = None
            self.postDownloadPopup.hide()
            self.MODULE.XnatIo.clearDownloadQueue()
            self.loaders = {}

            
        
        #------------------------
        # Show download popup
        #------------------------  
        #print "Initializing download..."
        self.preDownloadPopup.show()


        
        #------------------------
        # Get loaders, add to queue
        #------------------------  
        for loader in self.loaderFactory(self._src):
            if not loader.useCached:
                self.MODULE.XnatIo.addToDownloadQueue(loader.loadArgs['src'], loader.loadArgs['dst'])
            self.loaders[loader.loadArgs['src']] = loader
                         


            
        #------------------------
        # Run loaders
        #------------------------ 
        self.preDownloadPopup.hide()
        self.XnatDownloadPopup.show()
        self.MODULE.XnatIo.onEvent('downloadQueueFinished', onDownloadFinished)
        self.MODULE.XnatIo.startDownloadQueue()
      

        
        #------------------------
        # Enable View
        #------------------------
        self.MODULE.View.setEnabled(True)
        self.lastButtonClicked = None
    


        
    def loaderFactory(self, _src):
        """ 
        Returns the appropriate set of loaders after analyzing the
        '_src' argument.
        
        @param _src: The URI to create loaders from.
        @type _src: str
        
        @return: The loader list.
        @rtype: list(Loader)
            
        """

        #print "\n\nLOADER FACTORY"
        loaders = []


        
        #------------------------
        # Open popup
        #------------------------
        if '/scans/' in _src or '/files/' in _src:
            #print "OPENING POPUP ROW", _src
            self.XnatDownloadPopup.addDownloadRow(_src)
            #print self.XnatDownloadPopup.downloadRows
            


            
            
        #------------------------
        # '/files/' LEVEL 
        #------------------------
        if '/files/' in _src:
            
            # MRB
            if '/Slicer/files/' in _src:
                #print "FOUND SLICER FILE"
                loaders.append(Loader_Mrb(self.MODULE, _src))
                



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
            #print "SPLIT SCAN:", splitScan, '\n\t',scanSrc
            # query xnat for folder contents
            scan_uri = self.MODULE.XnatIo.getFolder(scanSrc, metadata= ['URI'])
            if not scan_uri:
                print('Scan has no files')
                self.preDownloadPopup.setText('No files found. Verify scan resources on XNAT.')
                return []
            contentUris = self.MODULE.XnatIo.getFolder(scanSrc, metadata= ['URI'])['URI']
            #print "CONTENT URIS", contentUris
            # get file uris and sort them by type
            loadables = self.__sortLoadablesByType(contentUris)
            #print "LOADABLES", loadables
            # cycle through the loadables and
            # create the loader for each loadable list.
            for loadableType, loadableList in loadables.items():
                if len(loadableList) > 0:
                    if loadableType == 'analyze':
                        loaders.append(Loader_Analyze(self.MODULE, _src, loadables[loadableType]))
                    if loadableType == 'dicom':      
                        loaders.append(Loader_Dicom(self.MODULE, _src, loadables[loadableType]))
                    if loadableType == 'misc':
                        loaders.append(Loader_File(self.MODULE, _src, loadables[loadableType]))


                        
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
            #print "SPLIT Expt:", splitExpt, '\n\t',exptSrc
            # Query for Scan IDs from XNAT.
            contents = self.MODULE.XnatIo.getFolder(exptSrc, metadata = ['ID'])
            #print "SCAN IDS", contents
            # Recurse this function for every scan.
            
            if 'ID' in contents:
                for scanId in contents['ID']:
                    scanSrc = exptSrc + '/' + scanId + '/files'
                    #print "\n\nLOADING SCAN SOURCE", scanSrc
                    loaders += self.loaderFactory(scanSrc)

            # Return loaders
            return loaders
                
            
        return loaders
