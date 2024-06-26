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
from __main__ import qt

# external
from Xnat import *
from MokaUtils import *

# module
from Timer import *
from SlicerUtils import *
from XnatSlicerUtils import *
from SessionManager import *




class View(object):
    """
    View is the class that handles all of the UI interactions 
    to the XnatIo.  It is meant to serve as a parent
    class to various View schemes such as View_Tree.
    
    @todo:  Consider sending more functions from View_Tree
    here. 
    """

    EVENT_TYPES = [
        'nodeChanged',
    ] 


    def __init__(self, MODULE = None, Setting = None):
        """ 
        @param MODULE: The XNATSlicer module
        @type MODULE: XnatSlicerWidget
        """
        
        self.MODULE = MODULE
        self.Setting = Setting

        self.sessionManager = SessionManager(self.MODULE)
        self.setup()


        
        #--------------------
        # Events
        #--------------------
        self.Events = MokaUtils.Events(self.EVENT_TYPES)

        
        
        
    def loadProjects(self):
        """ 
        To be inherited by child class.
        """
        pass


    
    
    def begin(self, skipAnim = False, hardReset = False):
        """ 
        Begins the the View communication process, 
        first by retrieving the projects from the XNAT server 
        based on the user's credentials.
        
        Displays error message boxes accordingly (server communication issues,
        or credential issues.)

        @param skipAnim: Whether to skip the animation.
        @type skipAnim: bool

        @param hardReset: Whether to do a hard reset.
        @type hardReset: bool
        """

        #MokaUtils.debug.lf("BEGIN", skipAnim, hardReset)
        #----------------------
        # Check projects
        #----------------------
        projectContents = None
        if hardReset or self.MODULE.XnatIo.projectCache == None:
            #MokaUtils.debug.lf()
            self.clear()
            projectContents = None

            try:
                projectContents = self.MODULE.XnatIo.\
                                  getFolder('projects', 
                                  Xnat.metadata.DEFAULT_TAGS['projects'], 
                                            'accessible')

            #
            # Error: SERVER ISSUES
            #
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.showError("Server error", "Server error for " + 
                               "'HOST_NAME' (HOST_URL):\n%s" %(str(e)))
                return
                
            #
            # Error: LOGIN
            #
            if projectContents == None:
                self.showError("Login error", 
                    "Login failed on XNAT host 'HOST_NAME' (HOST_URL)." + 
                    "Please check your username and password")
                return


            
        #----------------------
        # Load projects ino View.
        #----------------------
        if not skipAnim:
            self.MODULE.onLoginSuccessful()
        self.loadProjects(filters = None, projectContents = projectContents)
        slicer.app.processEvents()
        self.MODULE.Buttons.setEnabled(buttonKey='addFolder', enabled=True) 




    def showError(self, title, msg):
        """
        Displays an error message box.

        @param title: The message box title.
        @type title: str

        @param msg: The error message.
        @type msg: str
        """
        hostName = self.MODULE.LoginMenu.hostDropdown.currentText
        hostUrl = self.MODULE.SettingsFile.getAddress(hostName)
        qt.QMessageBox.warning( None, title, 
                                msg.replace('HOST_NAME', hostName).\
                                replace('HOST_URL', hostUrl))
        self.MODULE.onLoginFailed()





