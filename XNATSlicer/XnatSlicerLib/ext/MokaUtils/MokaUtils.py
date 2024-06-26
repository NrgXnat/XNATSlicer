from __future__ import with_statement

__author__ = "Sunil Kumar (kumar.sunil.p@gmail.com)"
__credits__ = ["Sunil Kumar"]
__license__ = "GPL"
__version__ = "1.0.1"
__maintainer__ = "Sunil Kumar"
__email__ = "kumar.sunil.p@gmail.com"
__status__ = "Production"


# python
import os
import sys
import shutil
import gzip
import zipfile
import inspect
import datetime
import getopt
import tempfile
import re
from collections import OrderedDict





class MokaUtils(object):
    """
    MokaUtils is a set of utility classes and methods
    for python.  
    """

    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


    class list(object):
        """
        A subclass of MokaUtils pertaining to 'list' objects.
        """

        @staticmethod
        def uniqify(_list):
            """ 
            Returns only unique elements in a list, while 
            preserving order: 
            From: http://www.peterbe.com/plog/uniqifiers-benchmark
        
            @param _list: The list to modify.
            @type _list: list

            @return: The modified list.
            @rtype: list
            """
            seen = set()
            seen_add = seen.add
            return [ x for x in _list if x not in seen and not seen_add(x)]



        @staticmethod    
        def removeZeroLenStrVals( _list):
            """ 
            As stated.  Removes any string values with 
            zero length within a list.

            @param _list: The list to modify.
            @type _list: list

            @return: The modified list.
            @rtype: list
            """
            for listItem in _list: 
                if (len(listItem)==0):
                    _list.remove(listItem)
                    
            return _list




    class path(object):
        """
        A subclass of MokaUtils pertaining to 'path' objects.
        """                

        @staticmethod            
        def addSuffixToFileName(fileName, suffix):
            """ 
            Appends a string to a given filename by
            splitting at the '.' to preserve the extension.
            
            @param fileName: The filename to append the string to.
            @type fileName: string

            @param suffix: The string to append to the filename.
            @type suffix: string

            @return: The suffix-appended filename.
            @rtype: string
            """
            name = os.path.splitext(fileName)[0]
            ext = os.path.splitext(fileName)[1]
            return name + suffix + ext




        @staticmethod
        def backupFiles(srcDir, backupFolderName = None):
            """
            Backs up a set of files.
            
            @param srcDir: The directory to begin the backup on.
            @type srcDir: string

            @param backupFolderName: The directory to back up the files in.
            @type backupFolderName: string
            """


            if not backupFolderName:
                backupStr = "BACKUP"
                backupFolderName = backupStr + "_" 
                backupFolderName += MokaUtils.string.dateTime()


            def callback(src):
                # Construct src,dst
                if backupFolderName in src:
                    return
                if MokaUtils.SCRIPT_DIR in src:
                    return
                filename = os.path.basename(src)
                relPath = os.path.dirname(src).replace(srcDir, '')
                dst = (os.path.join("./", backupFolderName + "/" + 
                                    relPath + "/" + filename)).\
                    replace("\\", "/").replace("//", "/")   
                # make paths that don't exist
                if (not os.path.exists(os.path.dirname(dst))):
                    os.makedirs(os.path.dirname(dst))
                # copy files to backup
                print("\nBacking up:\n'%s'\nto\n'%s'"%(src, dst))
                shutil.copyfile(src, dst)

            MokaUtils.path.fileWalk(srcDir, callback)
            




        @staticmethod
        def abbreviatePath(path, maxLen = 50):
            """
            @param path: The path to abbreviate.
            @type path: str

            @param maxLen: The maximum length of the string.
            @type maxLen: number
            
            @return: The shortened string.
            @rtype: str
            """
            return MokaUtils.string.abbreviate(path, maxLen)




        @staticmethod                    
        def abbreviateFileName(fileName, maxLen = 20):
            """ 
            Shortens a given filename to a length provided
            in the argument.  Appends the file with "..." string.
            
            @param fileName: The filename to abbreviate.
            @type fileName: str

            @param maxLen: The maximum length of the string.
            @type maxLen: number
            
            @return: The shortened string.
            @rtype: str
            """
            basename = os.path.basename(fileName)
            pre = basename.rsplit('.', 1)[0]
            if len(pre) > maxLen:
                baseneme = pre[0:8] + "..." + pre[-8:] + "." + basename.split(".")[1]
            return basename




        @staticmethod            
        def moveDir(src, dst, deleteSrc = True):
            """ 
            Moves the contents of one directory to another.

            @param src: The source directory.
            @type src: string

            @param dst: The destination directory. 
            @type dst: string

            @param deleteSrc:
            @type deleteStr: bool

            @return: The newly moved file URIs.
            @rtype: list of strings

            @raise: Error whether src or dst is not a valid directory.
            @raise: Error if src doesn't exist.
            """
            
            newURIs = []

            if not os.path.isdir(src):
                raise Exception("MokaUtils.path.moveDir: Argument '%s' is not a directory!"%(src))
                return 
            if not os.path.isdir(dst):
                raise Exception("MokaUtils.path.moveDir: Argument '%s' is not a directory!"%(src))
                return 
            if not os.path.exists(src):
                raise Exception("MokaUtils.path.moveDir: Argument '%s' doesn't exist!"%(src))
                return                 


            
            #------------------
            # Make destination dir
            #------------------
            if not os.path.exists(dst): 
                os.mkdir(dst)

            
            
            #------------------
            # Walk through src path.     
            #------------------
            for root, subFolders, files in os.walk(src):
                for file in files:
                    #
                    # Construct src folder, current uri, and dst uri
                    #
                    srcFolder = os.path.basename(src)
                    currURI = os.path.join(root,file)
                    newURI = os.path.join(dst, file)
                    #
                    # Clean up the newURI path string.
                    #
                    try:
                        folderBegin = root.split(srcFolder)[-1] 
                        if folderBegin.startswith("\\"): 
                            folderBegin = folderBegin[1:] 
                        if folderBegin.startswith("/"): 
                            folderBegin = folderBegin[1:] 
                        #
                        # Make the new URIs of the sub directory.
                        #
                        newPath = None
                        if folderBegin and len(folderBegin) > 0:
                            newPath = os.path.join(dst, folderBegin)
                            if not os.path.exists(newPath):
                                os.mkdir(newPath)
                            newURI = os.path.join(newPath, file)
                    except Exception as e: 
                        errorStr = str(e)
                        print("RootSplit Error: " + errorStr)
                    #
                    # Move the file, and track it             
                    #
                    shutil.move(currURI, newURI)
                    newURIs.append(MokaUtils.path.adjustPathSlashes(newURI))

                 
                
            #------------------
            # If the src path is to be deleted...
            #------------------
            if deleteSrc and not src.find(dst) == -1 and os.path.exists(src):
                shutil.rmtree(src)
                
            return newURIs



        @staticmethod    
        def getAncestorUri(uri, ancestorName):
            """ 
            Returns an ancestor uri based on the provided uri and the name of the ancestor.
            
            @param uri: The uri to derive the ancestor from.
            @type uri: string
            
            @param ancestorName: The ancestor folder of the uri.
            @type dst: string
            
            @return: The ancestor uri.
            @rtype: string
            """ 
            uri = os.path.dirname(uri.replace('\\', '/'))
            pathLayers = uri.rsplit("/")        
            ancestorUri = ''
            for pathLayer in pathLayers:
                if pathLayer == ancestorName:
                    break
                ancestorUri += pathLayer + "/"
            return ancestorUri




        @staticmethod    
        def adjustPathSlashes(path):
            """  
            Replaces '\\' path.
            
            @param path: The path to adjust.
            @type: string

            @return: The adjusted path.
            @rtype: string
            """
            return path.replace("\\", "/").replace("//", "/")




        @staticmethod
        def fileWalk(path, callback = None):
            """
            Performs an os.walk on the given path, listing 
            the files.

            @param path: The path to walk through
            @type path: string

            @param callback: The callback to run.  Passes entire path of the file as an argument.
            @type callback: function
            """
            assert os.path.isdir(path), "'%s' is not a valid directory."%(path)

            for root, dirs, files in os.walk(path):
                for f in files:
                    filename = (f).replace('\\', "/") 
                    src = os.path.join(root, filename)
                    if callback:
                        callback(src)
        




    class file(object):
        """
        A subclass of MokaUtils pertaining to 'file' objects.
        """

        @staticmethod    
        def writeZip(src, dst = None, deleteFolders = False):
            """ 
            Writes a given path to a zip file based on the basename
            of the 'src' argument.
            
            from: http://stackoverflow.com/questions/296499/how-do-i-zip-the-contents-of-a-folder-using-python-version-2-5
            
            @param src: The source directory of the zip files.
            @type src: string
            
            @param dst: (Optional) The dst uri of the zip.  
                Defaults to '$parent_directory/$srcDirectoryName + .zip'
            @type dst: string

            @return: The dst file path.
            @rtype: string

            @raise: Whether the 'src' argument is a directory.
            """
            zipURI = src + ".zip"
            if not os.path.isdir(src):
                raise "MokaUtils.file.writeZip: The argument " + \
                    "'%s' must be a directory."%(src)
                return
            with closing(zipfile.ZipFile(zipURI, "w", zipfile.ZIP_DEFLATED))\
                 as z:
                for root, dirs, files in os.walk(src):
                    for fileName in files: #NOTE: ignore empty directories
                        absfileName = os.path.join(root, fileName)
                        # : relative path
                        zfileName = absfileName[len(src)+len(os.sep):] 
                        z.write(absfileName, zfileName)

            dst = zipUri if dst == None else dst
            shutil.move(src, dst)
            return dst



        @staticmethod 
        def extractAllFiles(fromFile, toDir):
            """
            Extracts files within a zip and writes them to a directory,
            disregarding the directory structure within the zip file.

            @param fromFile: The source path of the deompressible file.
            @type fromFile: string
            
            @param toDir: The dst directory of the file to decompress. 
                Disregards the file structure in 'fromFile'.
            @type dst: string
            """
            toDir = os.path.normpath(toDir)

            with zipfile.ZipFile(fromFile) as zip_file:
                for member in zip_file.namelist():
                    filename = os.path.basename(member)
                    # skip directories
                    if not filename:
                        continue
                    # copy file (taken from zipfile's extract)
                    source = zip_file.open(member)
                    
                    try:
                        os.makedirs(toDir)
                    except Exception as e:
                        #print(str(e))
                        pass

                    dstFile = os.path.join(toDir, filename)
                    with open(dstFile, 'wb') as f:
                        shutil.copyfileobj(source, f)





        @staticmethod    
        def decompress(src, dst = None):
            """ 
            Employs various methods to decompress a given file
            based on the file extension.  
            
            @param src: The source path of the deompressible file.
            @type src: string
            
            @param dst: (Optional) The dst uri of the file to decompress.  
                Defaults to '$src_parent_directory/$src_name_without_extension'
            @type dst: string

            @raise: Whether the 'src' argument exists and is a file.
            """

            if not dst: 
                dst = os.path.dirname(src)


            if not os.path.isfile(src):
                errorStr = "MokaUtils.file.decompress: The src argument"
                errorStr += "'%s' must be a file!"%(src)
                raise Exception(errorStr)
                return
                     

            if src.endswith(".zip"):
                z = zipfile.ZipFile(src)      
                z.extractall(dst)
    

            elif src.endswith(".gz"):
                a = gzip.GzipFile(src, 'rb')
                content = a.read()
                a.close()                                          
                f = open(src.split(".gz")[0], 'wb')
                f.write(content) 
                f.close()





    class string(object):
        """
        A subclass of MokaUtils pertaining to 'string' objects.
        """
        ILLEGAL_CHARS = '@!#$%[&^*()+=<>/{}[\]~`].*|;:"\'?'

        @staticmethod
        def randomAlphaNumeric(length=12):
            """
            From: http://stackoverflow.com/questions/18319101/whats-the-
                best-way-to-generate-random-strings-of-a-specific-length-in-
                python
            @param length: The length of the string.
            @type length: number

            @return: The random string.
            @rtype: str
            """
            import string
            import random
            return ''.join(random.choice(string.ascii_uppercase) \
                    for i in range(length))


        @staticmethod
        def removeNonAlphanumeric(string):
            """
             @param string: The string to adjust.
            @type string: str

            @return: The modified string.
            @rtype: str
            """
            return re.sub(r'[^a-zA-Z0-9\[\]]',' ', string)
            

        @staticmethod
        def splitAtCaps(string):
            """
            @param string: The string to adjust.
            @type string: str

            @return: The modified string.
            @rtype: str
            """
            assert isinstance(string, str), \
                    'Invalid string: %s'%(string)

            capstart = string[0].isupper()
            if not capstart:
                string = string[0].upper() + string[1:]

            splitList = re.findall('[A-Z][^A-Z]*', string)
            
            if not capstart:
                splitList[0] = splitList[0][0].lower() + splitList[0][1:]

            return splitList


            

        @staticmethod
        def toCamelCase(string):
            """
            @param string: The string to adjust.
            @type string: str

            @return: The modified string.
            @rtype: str
            """
            assert isinstance(string, str), \
                    'Invalid string: %s'%(string)

            string = ' '.join(MokaUtils.string.splitAtCaps(string))
            string = re.sub('[\W_]', r' ', string).title().replace(' ', '')
            string = string[0].lower() + string[1:]
            #MokaUtils.debug.lf(string)
            return string



        @staticmethod
        def toTitleCase(string):
            """
            @param string: The string to adjust.
            @type string: str

            @return: The modified string.
            @rtype: str
            """

            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', string)
            return re.sub('([a-z0-9])([A-Z])', r'\1 \2', s1).title()



        @staticmethod
        def abbreviate(string, maxLen = 20):
            """
            @param string: The string to adjust.
            @type string: str
            """
            abbrevStr = '...'
            if len(string) > maxLen:
                return abbrevStr + string[-maxLen + len(abbrevStr):]
            return string




        @staticmethod
        def cleanExtension(string):
            """
            @param string: The extension to clean
            @type string: str
            
            @return: The cleaned extension in <i>.ext</i> format.
            @rtype: str
            """
            if string.startswith('*'): 
                string = string[1:]
            if not string.startswith('.'): 
                string = '.' + string
            return string
                    


        @staticmethod
        def unQuote(string):
            """
            @param string:
            @type string:

            @return: The stripped string.
            @rtype: string
            """

            if string.startswith('"') and string.endswith('"'):
                string = string[1:-1]
                
            elif string.startswith("'") and string.endswith("'"):
                string = string[1:-1]

            return string



        @staticmethod
        def isValid(string, spacesValid = True):
            """
            @param string: The string to check.
            @type string: str
            
            @return: Whether the string is valid, and the message.
            @rtype: bool, str
            """
            illChars = MokaUtils.string.ILLEGAL_CHARS
            if not spacesValid:
                illChars += ' '
            for char in illChars:
                if char in string:
                    return False
            return True



        @staticmethod
        def getInvalidMessage(spacesValid = True):
            """
            @param string: The string to check.
            @type string: str
            
            @return: Whether the string is valid, and the message.
            @rtype: bool, str
            """
            badChars = MokaUtils.string.ILLEGAL_CHARS
            if not spacesValid: badChars += ' '
            return "The following characters are not allowed: '%s'"%(badChars)




        @staticmethod 
        def dateTime():
            """ 
            Returns the Date and time as string in a more palattable / readable
            format.
            
            @return: The the date and time currently.
            @rtype: string
            """
            
            return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S").\
                replace(':','_').replace(" ", "__").strip()




        @staticmethod    
        def replaceForbidden(_str, replaceStr = '_', moreForbiddenChars = []):
            """
            Replaces the forbidden characters of a string.

            @param _str: The string to replace.
            @type str: string

            @param replaceStr: The string to replace the forbidden characters 
                with.
            @type replaceStr: string

            @return: The modified string.
            @rtype: string
            """
            _str = str(_str)
            replaceStr = str(replaceStr)

            _str = _str.replace(".", replaceStr)
            _str = _str.replace("/", replaceStr)
            _str = _str.replace("\\", replaceStr)
            _str = _str.replace(":", replaceStr)
            _str = _str.replace("*", replaceStr)
            _str = _str.replace("?", replaceStr)
            _str = _str.replace("\"", replaceStr)
            _str = _str.replace("<", replaceStr)
            _str = _str.replace(">", replaceStr)
            _str = _str.replace("|", replaceStr)


            if len(moreForbiddenChars) > 0:
                for fChar in moreForbiddenChars:
                    _str = _str.replace(str(fChar), replaceStr)

            return _str





    class debug(object):
        """
        A subclass of MokaUtils pertaining to debugging.
        """

        @staticmethod    
        def lf(*messages):
            """
            For debugging purposes.  Returns the current line number and function
            that calls on this method.
            
            @param messages: The messages to include.

            @return: The output string.
            @rtype: string
            """

            #---------------------------
            # Acquire the necessary parameters from
            # where the function is called.
            #---------------------------
            frame, filename, line_number, function_name, lines, index = inspect.getouterframes(inspect.currentframe())[1]
            returnStr = "\n"
            
            #
            # Construct a string based on the 
            # above parameters.
            #
            msg = ''
            for message in messages:
                msg += str(message) + " "
            returnStr = "%s (%s) %s: %s"%(os.path.basename(filename), function_name, line_number, msg)
            
            print(returnStr)





    class convert(object):
        """
        A subclass of MokaUtils pertaining to converting certain numerical types.
        """

        @staticmethod
        def bytesToMB(_bytes, decimalPlaces = 2):
            """ 
            Converts bytes to MB.  Returns a float of the MB up to two 
            decimal places.

            @param _bytes: The bytes to convert.
            @type _bytes: int

            @param decimalPlaces: The decimal places for the MB conversion.  
                Defaults to 2.
            @type decimalPlaces: int

            @return: The bytes converted to MB.
            @rtype: float
            """
            assert isinstance(decimalPlaces, int), "%s " + \
            "is an invalid decimal place."%(decimalPlaces)

            _bytes = int(_bytes)
            mb = str(_bytes/(1024*1024.0)).split(".")[0]            

            if decimalPlaces > 0:
                mb += '.' + str(_bytes/(1024*1024.0)).\
                      split(".")[1][:int(decimalPlaces)]
            return float(mb)





    class Events(object):
        """
        
        """

        def __init__(self, __eventTypes):
            """
            @param __eventTypes: The event types.
            @type __eventTypes: str
            """
            assert isinstance(__eventTypes, list), "Must have " + \
                                 "a string list for event types!"
            self.__eventTypes = __eventTypes
            self.eventCallbacks__ = {}
            self.__suspendedEvents = []
            for eventType in self.__eventTypes:
                self.eventCallbacks__[str(eventType)] = []



        @property
        def EVENT_TYPES(self):
            """
            @return: The stored event types.
            @rtype: str
            """
            return self.__eventTypes



        def suspendEvent(self, eventKey):
            """
            Suspend on event.

            @param eventKey: The eventKey descriptor. 
            @type eventKey: string
            """
            if not eventKey in self.__eventTypes:
                raise Exception("MokaUtils.Events (onEvent): " + \
                                "invalid event type '%s'"%(eventKey))
            if not eventKey in self.__suspendedEvents:
                self.__suspendedEvents.append(eventKey)




        def suspendEvents(self, suspend):
            """
            Suspend all events.

            @param suspend: Toggle event suspsension.
            @type suspend: bool
            """
            self.__suspendedEvents = []
            if suspend:
                for eventKey in self.__eventTypes:
                    self.__suspendedEvents.append(eventKey)                    




        def onEvent(self, eventKey, callback):
            """
            Adds a callback for a given event.  
            Callbacks are strored internally as a dictionary of 
            arrays in Xnat.callbacks.

            @param eventKey: The eventKey descriptor for the callbacks 
                stored in Xnat.callbacks.  Refer
                to self.__eventTypes for the list.
            @type eventKey: string

            @param callback: The callback function to enlist.
            @type callback: function

            @raise: Error if 'eventKey' argument is not a valid event type.
            """

            if not eventKey in self.__eventTypes:
                raise Exception("MokaUtils.Events (onEvent): " + \
                                "invalid event type '%s'"%(eventKey))

            elif eventKey in self.__eventTypes and \
                 not eventKey in self.eventCallbacks__:
                #MokaUtils.debug.lf("Warning: dynamically added " + \
                #                   "event key %s"%(eventKey))
                self.eventCallbacks__[eventKey] = []
                
            self.eventCallbacks__[eventKey].append(callback)




        def runEventCallbacks(self, event, *args):
            """
            Private function that runs the callbacks based on the provided 
            'event' argument.

            @param event: The event descriptor for the callbacks stored in 
                Xnat.callbacks.  Refer to self.__eventTypes for the list.
            @type event: string

            @param *args: The arguments that are necessary to run the event 
                callbacks.

            @raise: Error if 'event' argument is not a valid event type.
            """

            if not event in self.__eventTypes:
                raise Exception("XnatIo (onEvent): invalid event " + \
                    "type '%s'.  Options are: %s"%(event, self.__eventTypes))
            for callback in self.eventCallbacks__[event]:
                #print(f"EVENT CALLBACK {event}")
                if not event in self.__suspendedEvents:
                    callback(*args)




        def clearEvents(self, eventKey = None):
            """
            Clears the event callbacks associated with the 'eventKey' argument.  
            If 'eventKey' is not specified, clears all of the event callbacks.

            @param eventKey: The event key to clear.
            @type eventKey: string
            """
            if not eventKey:
                for key in self.eventCallbacks__:
                    self.eventCallbacks__[key] = []
                return

            if not eventKey in self.__eventTypes:
                raise Exception("%s (clearEvents): " + 
                "invalid event type '%s'"%(self.__class__.__name__, eventKey))

            else:
                self.eventCallbacks__[eventKey] = []





    class ops(object):
        """
        
        """
        OPERATIONS = [
            'FindAndReplace',
            'InjectInclude',
            'ListFiles'
        ]  

        @staticmethod
        def opFactory(optDict):
            """
            Calls on the MokaUtils operation based on the optDict.

            @param optDict: The argument dictionary.
            @type: dict(str, str)

            @return: The relevant MokaUtils.ops.Operation subclass.
            @rtype: MokaUtils.ops.Operation
            """

            op = optDict['operation'].lower()

            if op == 'FindAndReplace'.lower():
                return MokaUtils.ops.FindAndReplace(optDict)

            elif op == 'ListFiles'.lower():
                return MokaUtils.ops.ListFiles(optDict)

            elif op == 'InjectInclude'.lower():
                return MokaUtils.ops.InjectInclude(optDict)

            else:
                errorStr = "Invalid MokaUtils operation type: '%s'." + \
                "  Options are: %s "%(optDict['operation'],', '.\
                                      join(MokaUtils.ops.OPERATIONS))
                raise Exception(errorStr)




        class Operation(object):
            """
            
            """
            def __init__(self, optDict):
                """
                """
                self.optDict = optDict
                self.__cleanOpts()




            def __cleanOpts(self):
                """
                Cleans the options.
                """
                # unquote stuff 
                for name in [val['name']  for key, val in MokaUtils.cmd.ARG_TYPES.items()]:
                    if name in self.optDict:
                        self.optDict[name] = MokaUtils.string.unQuote(self.optDict[name])

                if 'extension' in self.optDict:
                    self.optDict['extension'] = MokaUtils.string.cleanExtension(self.optDict['extension'])
                    
                


            def validateOpts(self, opts):
                """
                @param opts: The options to evaluate.
                @type opts: str or list(str)
                """
                if isinstance(opts, str):
                    opts = [opts]                
                assert isinstance(opts, list), "%s is an invalid option list."%(opts)

                #
                # Check existence
                #
                for opt in opts:
                    if not opt in self.optDict:
                        raise Exception("Need a '%s' (-%s) argument for %s."%(opt, MokaUtils.cmd.argByName(opt), self.__class__.__name__))
                
                

            def run(self):
                """
                """
                print("PARENT RUN")
                pass




        class ListFiles(Operation):
            """
            
            """
            def __init__(self, optDict):
                """
                """
                super(MokaUtils.ops.ListFiles, self).__init__(optDict)
                self.validateOpts(['directory'])


            def run(self):
                """
                """
                super(MokaUtils.ops.ListFiles, self).run()
                def callback(src): 
                    if 'extension' in self.optDict:
                        if src.endswith(self.optDict['extension']):
                            print(src)
                    else:
                        print(src)
                MokaUtils.path.fileWalk(self.optDict['directory'], callback)




        class InjectInclude(Operation):
            """
            
            """

            def __init__(self, optDict):
                """
                """
                super(MokaUtils.ops.FindAndReplace, self).__init__(optDict)
                self.validateOpts(['directory', 'finder', 'injector', 'extension']) 



            def __checkAndInject(src, finder, injector):
               """
               """
               # read the file line by line, store it.
               if os.path.exists(src):
                   lines = [line for line in open(src)]
                   newLines = lines
                   for l in lines:
                       if finder in l:
                           newLines = [injector + '\n'] + newLines
                           print("Injecting '%s' into '%s'"%(injector, src))
                           break


                   try:
                       fl = open(src, 'w')
                       for item in newLines:
                           fl.write("%s" % item)
                       fl.close()
                       
                   except ValueError as e:
                        print(str(e))



            def run(self):
                """
                """
                MokaUtils.path.backupFiles(self.optDict['directory'])

                finder = self.optDict['finder']
                injector = self.optDict['replacer']
                
                def callback(src):
                    if src.endswith(self.optDict['extension']) and not MokaUtils.SCRIPT_DIR in src:
                        self.__checkAndInject(src, finder, injector)
    
                MokaUtils.path.fileWalk(self.optDict['directory'], callback)





        class FindAndReplace(Operation):
            """
            
            """
            def __init__(self, optDict):
                """
                """
                super(MokaUtils.ops.FindAndReplace, self).__init__(optDict)
                self.validateOpts(['directory', 'finder', 'replacer', 'extension'])     
      


            def printReplace(self, src, finder, replacer, lineNum, oldLine, newLine):
                """
                """
                print("In %s, replaced\n'%s' with '%s', in line: %i\n\n%s%s\n"%(MokaUtils.path.abbreviatePath(src), 
                                                                                finder, 
                                                                                replacer, 
                                                                                lineNum, oldLine, newLine))

            def __replaceInFile(self, src, finder, replacer):
                """
                @param src: The source file.
                @type src: string

                @param finder: The string to find.
                @type finder: string

                @param replacer: The string to replace.
                @type replacer: string
                """

                if os.path.exists(src) and os.path.isfile(src):

                    changedLinesCount = 0
                    oldLines = [line for line in open(src)]
                    newLines = []



                    #------------------------------------
                    # Generate a new line, store it
                    #------------------------------------
                    for i in range(0, len(oldLines)):
                        oldLine = oldLines[i]
                        newLine = oldLine.replace(finder, replacer)
                        if newLine != oldLine:
                            changedLinesCount += 1
                            self.printReplace(src, finder, replacer, i, oldLine, newLine)
                        newLines.append(newLine)


                    #------------------------------------
                    # Write the new lines to file ONLY if there are
                    # changes
                    #------------------------------------   
                    try:
                        if changedLinesCount:
                            newFile = open(src, 'w')
                            for line in newLines:
                                newFile.write("%s" % line)
                            newFile.close()

                    except ValueError as e:
                        print("File write error: %s %s"%(str(ValueError), str(e)))




            
            def run(self):
                """
                """
                MokaUtils.path.backupFiles(self.optDict['directory'])

                finder = self.optDict['finder']
                replacer = self.optDict['replacer']
            
                def callback(src):
                    if src.endswith(self.optDict['extension']) and not MokaUtils.SCRIPT_DIR in src:
                        self.__replaceInFile(src, finder, replacer)
    
                MokaUtils.path.fileWalk(self.optDict['directory'], callback)
                





    class cmd(object):
        """
        The command-line class for MokaUtils.py.  Handles command-line
        options for running MokaUtils operations specified in the MokaUtils.cmd.OPERATIONS
        property.
        """


        ARG_TYPES = OrderedDict([
            ('o', {
                'name': 'operation',
                'desc': 'The operation to perform:'
            }),

            ('d' , {
                'name': 'directory',
                'desc': 'The directory to preform the operation on.'
            }),

            ('b' , {
                'name': 'backup',
                'desc': 'The backup directory - automatically created if none entered.'
            }),

            ('f' , {
                'name': 'finder',
                'desc': 'The string to find.'
            }),

            ('r' , {
                'name': 'replacer',
                'desc': "The string to replace 'finder' with."
            }),

            ('e' , {
                'name': 'extension',
                'desc': 'Perform operations only on files with this extension.  (Defaults to all)'
            }),

            ('i' , {
                'name': 'injector',
                'desc': 'The injector string.'
            })
        ])
        



        @staticmethod
        def argByName(name):
            """
            Returns the shorthand argument by its name.

            @param name: The name to get the argument from.
            @type name: str

            @return: The argument string.
            @rtype: string

            @raise: Error if name is not found.
            """

            for k,v in MokaUtils.cmd.ARG_TYPES.items():
                if v['name'].lower() == name.lower():
                    return k            
            raise Exception("'%s' is not a valid MokaUtils.cmd.ARG_TYPE name"%(name))




        @staticmethod
        def hint():
            """
            Displays the MokaUtils command line options.

            @return: A string of the options:
            @rtype: string
            """
            
            #
            # Append the operations list to the argument
            # description.
            #
            tabber = '\n\t\t\t\t\t' 
            MokaUtils.cmd.ARG_TYPES['o']['desc'] += tabber
            MokaUtils.cmd.ARG_TYPES['o']['desc'] += tabber.join(MokaUtils.ops.OPERATIONS)


            #
            # Construct the argument description.
            #
            hintStr = '\nMokaUtils command line options:\n'
            for key, val in MokaUtils.cmd.ARG_TYPES.items():
                optName = '-%s (%s) '%(key, val['name'])
                maxSpace = 25
                spacerLen = maxSpace if len(optName) < maxSpace else len(optName) + 1
                spacer = ' '.join(['' for i in range(0, spacerLen - len(optName))])
                hintStr += '\t%s:%s%s\n'%(optName, spacer, val['desc'])
            hintStr += '\n'
            print(hintStr)
            

    

        @staticmethod
        def processArgs(args):
            """
            Processes the command line arguments into a data structure.

            @param args: The arguments to process.
            @type args: list(str)

            @return: The arguments and their values as a dictionary.
            @rtype: dict(str, str)
            """

            optDict = {key: None for key in MokaUtils.cmd.ARG_TYPES}
            longhandArgDict = {}
            argOpts = ':'.join([key for key in MokaUtils.cmd.ARG_TYPES])
            argNames = [val['name']  for key, val in MokaUtils.cmd.ARG_TYPES.items()]


            try:
                opts, args = getopt.getopt(args, argOpts)

            except getopt.GetoptError as err:
                print('\n%s\n'%(str(err)))
                MokaUtils.cmd.hint()
                sys.exit(2)

            for opt, arg in opts:
                _opt = opt.strip('-')
                optDict[_opt] =  arg
                longhandArgDict[MokaUtils.cmd.ARG_TYPES[_opt]['name']] =  arg

            return optDict, longhandArgDict




            
            



#---------------------
# Setup function for 
# MokaUtils as a command line tool.
#---------------------
if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) == 0:
        MokaUtils.cmd.hint()
    else:
        optDict, longhandArgDict = MokaUtils.cmd.processArgs(sys.argv[1:])
        operation = MokaUtils.ops.opFactory(longhandArgDict)
        operation.run()
