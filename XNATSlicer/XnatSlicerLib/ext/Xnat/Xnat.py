__author__ = "Sunil Kumar (kumar.sunil.p@gmail.com)"
__copyright__ = "Copyright 2014, Washington University in St. Louis"
__credits__ = ["Sunil Kumar", "Tim Olsen", "Dan Marcus", "Rick Herrick"]
__license__ = "XNAT Software License Agreement " + \
              "(see: http://xnat.org/about/license.php)"
__version__ = "1.0.0"
__maintainer__ = "Rick Herrick"
__email__ = "herrickr@mir.wustl.edu"
__status__ = "Production"

from __main__ import qt

import os
import sys
import base64
import json
import requests
import threading


class Xnat(object):
    """ 
    The Xnat suite for python.

    @author: Sunil Kumar (sunilk@mokacreativellc.com)
    @contact: Sunil Kumar (sunilk@mokacreativellc.com), 
        Dan Marcus (dmarcus@wustl.edu)
    @organization: Moka Creative, LLC in collaboration wtih 
        The Neuroinformatics Research Group (NRG) 
        and The National Alliance for Medial Computing (NA-MIC)
    @copyright: 2014 Washington University, All Rights Reserved
    @license: XNAT Software License Agreement

       Copyright 2005 Harvard University / Howard Hughes Medical Institute 
        (HHMI) / Washington University
       All rights reserved.

       Redistribution and use in source and binary forms, with or without 
       modification, are permitted provided that the following conditions are 
       met:

       Redistributions of source code must retain the above copyright notice, 
       this list of conditions and the following disclaimer.
       Redistributions in binary form must reproduce the above copyright 
       notice, this list of conditions and the following disclaimer in the 
       documentation and/or other materials provided with the distribution.
       Neither the names of Washington University, Harvard University and HHMI 
       nor the names of its contributors may be used to endorse or promote 
       products derived from this software without specific prior written 
       permission.
       THIS SOFTWARE IS PROVIDED BY The COPYRIGHT HOLDERS AND CONTRIBUTORS "AS 
       IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED 
       TO, The IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A 
       PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL The COPYRIGHT 
       HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, 
       SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED 
       TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR 
       PROFITS; OR BUSINESS INTERRUPTION) 
       HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, 
       STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING 
       IN ANY WAY OUT OF The USE OF THIS SOFTWARE, EVEN IF ADVISED OF The 
       POSSIBILITY OF SUCH DAMAGE.
    """



    class io(object):
        """
        XnatIo is a lightweight communicator class to XNAT. XnatIo uses REST 
        calls to 
        send/receive commands and files to XNAT. Since input is usually 
        string-based, there are 
        several utility methods in this class to clean up strings.  Its primary
        communicator classes are http.client and urllib.request.

        Example Usage:

        >>> from Xnat import *
        >>> xnat = Xnat.io('http://central.xnat.org', 'testUser', \
            'testUserPassword')
        >>> contents = xnat.getFolder('projects')
        >>> print(contents['111']['ID'])
        'XNATSlicerTest'    
        """

        EVENT_TYPES = [
            'downloadCancelled',
            'downloading',
            'downloadStarted',
            'downloadFinished',
            'downloadQueueFinished',
            'downloadQueueStarted',
            'downloadFailed',
            'jsonError'
        ] 

        def __init__(self, host, username, password):
            """ 
            Initializes the internal variables. 

            @param host: The XNAT host to interact with.  NOTE: Full domain 
                name needed.
            @type host: string

            @param username: The username for the XNAT host.
            @type username: string

            @param password: The password for the XNAT host.
            @type password: string        
            """
            
            self.downloadQueue = []        


            #-------------------
            # Set relevant variables (all required)
            #-------------------
            self.projectCache = None
            self.host = host if host.endswith('/') else host + '/'
            self.username = username
            self.password = password


                

            #-------------------
            # Make tracking dictionary for download modal.
            #-------------------
            self.downloadTracker = {
                'totalDownloadSize': {'bytes': None, 'MB': None},
                'downloadedSize': {'bytes': None, 'MB': None},
            }


            #-------------------
            # Make relevant variables for __httpsRequests
            #-------------------
            base64string = base64.encodebytes(f'{self.username}:{self.password}'.encode())
            self.authHeader = { 'Authorization' : 'Basic %s' %(base64string) }
            self.auth = (self.username, self.password)
            self.session = requests.Session()
            self.session.auth = self.auth
            self.fileDict = {}
            self.response = None

            # Popups
            self.exceptionPopup = qt.QMessageBox()
            self.exceptionPopup.setIcon(4)




        def getFolder(self, folderUris, metadata = None, queryArgs = None):   
            """ 
            Returns the contents of a given folder provided in the arguments
            'folderUris'.  Returns an object based on the 'metadata' argument
            which filters the return contents.  The 'queryArgs' parameter
            deals generally with further fitering of certain contents within a 
            given folder. 
            For instance, to get projects only the user has access to, the URI 
            needs to be appended with '?accessible=True'.

            @param folderUris: A string or list of URIs to retrieve the 
                contents from.
            @type folderUris: string | list.<string>

            @param metadata: A list of metadata attributes to include in the 
                return dict.  Default is all metadata.
            @type metadata: list.<string>

            @param queryArgs: A string or list of query argument suffixes to 
                apply (i.e. the '?queryArg=arg' suffixes). 
                See XNAT documentation for more details.  Default is no suffix. 
            @type queryArgs: string | list.<string>

            @return: A list of dicts describing the contents of the folders, 
                with metadata as keys.
            @rtype: list.<dict>
            """

            returnContents = {}



            #-------------------- 
            # Force the relevant argumets to lists
            #-------------------- 
            if isinstance(folderUris, str):
               folderUris = [folderUris]
            if isinstance(queryArgs, str):
               queryArgs = [queryArgs]



            #-------------------- 
            # Acquire contents via 'self.__getJson'
            #-------------------- 
            contents = []
            for folderUri in folderUris:

                #
                # Apply query arguments, if any.
                #
                if queryArgs:
                    folderUri = Xnat.path.applyQueryArguments(folderUri, 
                                                              queryArgs)


                #
                # Get the JSON
                #
                folderUri = Xnat.path.makeXnatUrl(self.host, folderUri)
                json = self.__getJson(folderUri)

                #
                # If json is null we have a login error.
                # Return out.
                #
                if json == None:
                    return None
                #
                # Otherwise, concatenate to rest of contents.
                #
                contents =  contents + json

                #
                # If we want the projects, store projects in a dictionary. 
                # 'self.projectCache' is reset if the user logs into a new 
                # host or logs in a again.
                #
                if folderUri.endswith('/projects'):
                    self.projectCache = contents
                #print(f"CONTENTS {contents}")
            #-------------------- 
            # Exit out if there are non-Json or XML values.
            #-------------------- 
            if str(contents).startswith("<?xml"): return [] 
            # We don't want text values



            #-------------------- 
            # Get other attributes with the contents 
            # for metadata tracking.
            #-------------------- 
            for content in contents:
                if metadata:
                    for metadataTag in metadata:
                        if metadataTag in content:
                            #
                            # Create the object attribute if not there.
                            #
                            if not metadataTag in returnContents:
                                returnContents[metadataTag] = []
                            returnContents[metadataTag].append(\
                                                    content[metadataTag])
                else:
                    returnContents = contents


            #-------------------- 
            # Track projects and files in global dict
            #-------------------- 
            for folderUri in folderUris:
                folderUri = folderUri.replace('//', '/')
                if folderUri.endswith('/files'):
                    for content in contents:
                        # create a tracker in the fileDict
                        #print(f"\n\nCONTENT {content} {folderUri}")
                        self.fileDict[content['Name']] = content
                    #print("%s %s"%(, self.fileDict))
                elif folderUri.endswith('/projects'):
                    self.projectCache = returnContents



            #-------------------- 
            # Return the contents of the folder as a
            # dictionary of lists
            #-------------------- 
            return returnContents




        def getFile(self, _src, _dst): 
            """ 
            Downloads a file from a given XNAT host.

            @param _src: The source XNAT URL to download from.
            @type: string

            @param _dst: The local dst to download to.
            @type: string
            """

            #--------------------
            # Reset total size of downloads for all files
            #-------------------------
            self.downloadTracker['totalDownloadSize']['bytes'] = 0
            self.downloadTracker['downloadedSize']['bytes'] = 0
            downloadFolders = []

            #-------------------------
            # Remove existing dst files from their local URI
            #-------------------------
            if os.path.exists(_dst):
                os.remove(_dst)
            self.__getFile_requests(_src, _dst)




        def getResources(self, folder):
            """ 
            Gets the contents of a 'resources' folder
            in a given XNAT host.  'resources' folders 
            demand a bit more specifity in the metadata manipulation.
            Furthermore, 'resources' folders are frequently accessed
            as part of the Slicer file location within an 'experiment'.

            @param folder: The folder to retrieve the 'resources' folder 
                contents from.
            @type folder: string
            """

            #-------------------- 
            # Get the resource JSON
            #-------------------- 
            folder += "/resources"
            resources = self.__getJson(folder)
            #print("%s %s"%(, folder))
            #print(" Got resources: '%s'"%(str(resources)))



            #-------------------- 
            # Filter the JSONs
            #-------------------- 
            resourceNames = []
            for r in resources:
                if 'label' in r:
                    resourceNames.append(r['label'])
                    #print("FOUND RESOURCE ('%s') : %s"%(folder, r['label']))
                elif 'Name' in r:
                    resourceNames.append(r['Name'])
                    #print("FOUND RESOURCE ('%s') : %s"%(folder, r['Name']))

                return resourceNames



        def getFileSize(self, _uri):
            """ 
            Retrieves a tracked file's size and 
            converts it to MB based on the 'self' variable
            'fileDict' which contains the raw byte size 
            of the given file.

            @param _uri: The file URI to retrieve the size from.
            @type _uri: string

            @return: The size in MB of the file.
            @rtype: integer
            """            
            totalBytes = 0
            fileName = os.path.basename(_uri)

            if fileName in self.fileDict:
                # Get size from fileDict log if it exists
                totalBytes = int(self.fileDict[fileName]['Size'])
            elif '/scans' in _uri:
                # Add all files for scan if it is a scan uri
                files = self.__getJson(_uri.replace('zip', 'json'))

                for f in files:
                    totalBytes += int(f['Size'])

            totalSize = {
                "bytes": (totalBytes),
                "MB" : Xnat.utils.bytesToMB(totalBytes)
            }
            return totalSize 



        def putFolder(self, _dst):
            """ 
            Function for adding a folder to a given XNAT host.
            @param _dst: The uri of the folder to put into the XNAT host.
            @type _dst: string
            """
            if not _dst.startswith(self.host + '/data'):
                if not _dst.startswith('/'):
                    _dst = '/' + _dst
                _dst = self.host + '/data' + _dst
            #print(f"\n\nXNAT 1 {_dst}")
            _dst = str(Xnat.path.cleanUri(_dst)).encode('ascii', 'ignore')
            #print(f"fXNAT 2 {_dst} \n\n")
            response = self.__httpsRequest('PUT', _dst)
            return response




        def putFile(self, _src, _dst, delExisting = True):
            """ 
            Upload a file to an XNAT host.  Utilizes the internal
            method __httpsRequest.

            @param _src: The local source file to upload to.
            @type: string

            @param _dst: The XNAT dst to upload to.
            @type: string      

            @param delExisting: Delete the exsting _dst if it exists in the 
                XNAT host.   Defaults to 'True'.
            @type: boolean   
            """

            #-------------------- 
            # Delete existing _dst from XNAT host.
            #-------------------- 
            if delExisting:
                r = self.__httpsRequest('DELETE', _dst)
            #print("%s Uploading\nsrc: '%s'\n_dst: '%s'"%(_src, _dst))



            #-------------------- 
            # Clean '_dst' string and endcode
            #-------------------- 
            _dst = Xnat.path.makeXnatUrl(self.host, _dst)
            _dst = str(_dst).encode('ascii', 'ignore')



            #-------------------- 
            # Put the file in XNAT using the internal '__httpsRequest'
            # method.
            #-------------------- 
            with open(_src, 'rb') as f:
                response = self.__httpsRequest('PUT', _dst, files={'file': f}, 
                    headers={'Content-Type': 'application/octet-stream'}, stream=True)

            return response



        def delete(self, _uri):
            """ 
            Deletes a given file or folder from an XNAT host.

            @param _uri: The XNAT URI to run the "DELETE" method on.
            @type: string
            """
            print("Deleting '%s'"%(_uri))
            response =  self.__httpsRequest('DELETE', _uri, '')




        def exists(self, _uri):
            """ 
            Determines whether a file exists
            on an XNAT host based on the '_uri' argument.

            @param _uri: The xnat uri to check if it exists on the XNAT host.
            @type _uri: string

            @return: Whether the file exists.
            @rtype: boolean
            """
            #print("%s %s"%(_uri))


            #-------------------- 
            # Query logged files before checking
            #-------------------- 
            if (os.path.basename(_uri) in self.fileDict):
                return True



            #-------------------- 
            # Clean string
            #-------------------- 
            xnatUrl = Xnat.path.makeXnatUrl(self.host, _uri)
            parentDir = Xnat.path.getUriAt(xnatUrl, 'files')
            for i in self.__getJson(parentDir):
                if os.path.basename(xnatUrl) in i['Name']:
                    return True   
            return False




        def search(self, searchString):
            """ 
            Utilizes the XNAT search query function
            on all three XNAT levels (projects, subjects and experiments) 
            based on the provided 'searchString' argument.  Searches through 
            the available columns as described below. CASE INSENSITIVE.

            @param searchString: The search query string.
            @type searchString: string

            @return: A dictionary of the results where the key is the XNAT 
                level (projec, subject or experiment).
            @rtype: dict.<string, string>
            """
            resultsDict = {}



            #-------------------- 
            # Projects, subjects, experiments
            #-------------------- 
            levelTags = {}
            levelTags['projects'] = ['ID', 
                                     'secondary_ID',
                                     'name', 'pi_firstname', 
                                     'pi_lastname', 
                                     'description']
            levelTags['subjects'] = ['ID', 'label']
            levelTags['experiments'] = ['ID', 'label']



            #-------------------- 
            # Looping through all of the levels,
            # constructing a searchQuery for each based
            # on the relevant columns.
            #--------------------       
            levels = ['projects', 'subjects', 'experiments']
            for level in levels:
                resultsDict[level] = []
                for levelTag in levelTags[level]:
                    searchStr = '/%s?%s=*%s*'%(level, levelTag, searchString)
                    #
                    # Experiments: only search folders with images
                    #
                    if level == 'experiments':
                        searchStr2 = searchStr + '&xsiType=xnat:mrSessionData'
                        searchStr = searchStr + '&xsiType=xnat:petSessionData'
                        resultsDict[level] = resultsDict[level] + \
                                             self.__getJson(searchStr2)
                    resultsDict[level] = resultsDict[level] + \
                                         self.__getJson(searchStr)



            return resultsDict




        def onEvent(self, eventKey, callback):
            """
            Adds a callback for a given event.  
            Callbacks are strored internally as a dictionary of arrays in 
            Xnat.callbacks.

            @param eventKey: The eventKey descriptor for the callbacks stored 
                in Xnat.callbacks.  Refer to self.EVENT_TYPES for the list.
            @type eventKey: string

            @param callback: The callback function to enlist.
            @type callback: function

            @raise: Error if 'eventKey' argument is not a valid event type.
            """

            #-------------------- 
            # Construct callback dict if it doesn't exist.
            #--------------------
            if not hasattr(self, 'eventCallbacks__'):
                self.eventCallbacks__ = {}
                for eventType in self.EVENT_TYPES:
                    self.eventCallbacks__[str(eventType)] = []


            if not eventKey in self.EVENT_TYPES:
                raise Exception("Xnat.io (onEvent): invalid event type '%s'"%(eventKey))
            self.eventCallbacks__[eventKey].append(callback)





        def runEventCallbacks(self, event, *args):
            """
            Private function that runs the callbacks based on the provided 
            'event' argument.

            @param event: The event descriptor for the callbacks stored in 
                Xnat callbacks.  Refer
              to self.EVENT_TYPES for the list.
            @type event: string

            @param *args: The arguments that are necessary to run the event 
                callbacks.

            @raise: Error if 'event' argument is not a valid event type.
            """

            if not event in self.EVENT_TYPES:
                raise Exception("XnatIo (onEvent): invalid event type '%s'"%(\
                                                                    event))
            if not hasattr(self, 'eventCallbacks__'):
                print('self has no attribute eventCallbacks__')
                return

            for callback in self.eventCallbacks__[event]:
                #print(f"EVENT CALLBACK {event}")
                callback(*args)




        def clearEvents(self, eventKey = None):
            """
            Clears the event callbacks associated with the 'eventKey' 
            argument.  
            If 'eventKey' is not specified, clears all of the event callbacks.

            @param eventKey: The event key to clear.
            @type eventKey: string
            """
            if not eventKey:
                for key in self.eventCallbacks__:
                    self.eventCallbacks__[key] = []
                return

            if not eventKey in self.EVENT_TYPES:
                raise Exception("%s (clearEvents): invalid event type '%s'"%(\
                                            self.__class__.__name__, eventKey))

            else:
                self.eventCallbacks__[eventKey] = []




        def addToDownloadQueue(self, _src, _dst):
            """
            Adds a file to the download queue.

            @param _src: The source XNAT URL to download form.
            @type: string

            @param _dst: The local dst to download to.
            @type: string
            """
            self.downloadQueue.append({'src': _src, 'dst': _dst})



        def clearDownloadQueue(self):
            """
            Clears the download queue.
            """
            #print("CLEAR DOWNLOAD QUEUE")
            self.downloadQueue = []
            self.clearEvents()




        def startDownloadQueue(self):
            """
            Begins the the download queue.
            """

            self.runEventCallbacks('downloadQueueStarted') 
            while len(self.downloadQueue):
                if self.downloadQueue[0]['dst'] != None:
                    self.getFile(self.downloadQueue[0]['src'], 
                                 self.downloadQueue[0]['dst'])
            self.runEventCallbacks('downloadQueueFinished') 
            self.clearDownloadQueue()





        def inDownloadQueue(self, _src):
            """
            Determines whether a given source is in the download queue.

            @param _src: The source XNAT URL to check if it's in the download 
                queue.
            @type: string

            @return: boolean
            @rtype: string
            """
            for dl in self.downloadQueue:
                if _src in dl['src']:
                    return True
            return False




        def removeFromDownloadQueue(self, _src):
            """
            Removes a given source from the download queue.

            @param _src: The source XNAT URL to remove from the download queue.
            @type: string
            """
            for dl in self.downloadQueue:
                if _src in dl['src']:
                    self.downloadQueue.pop(self.downloadQueue.index(dl))
                    return



        def cancelDownload(self, _src):
            """ 
            Cancels a download.

            Set's the download state to 0.  The open buffer in the 'GET' method
            will then read this download state, and cancel out.

            @param _src: The source XNAT URL to cancel the download from.
            @type: string
            """
            print("\n\nCancelling download of '%s'"%(_src))

            #-------------------- 
            # Pop from queue
            #--------------------
            self.removeFromDownloadQueue(_src) 


            #-------------------- 
            # Callbacks
            #-------------------- 
            self.runEventCallbacks('downloadCancelled', _src) 


            #-------------------- 
            # Clear queue if there is nothing
            # left in it.
            #-------------------- 
            if len(self.downloadQueue) == 0:
                self.clearDownloadQueue()





        def __httpsRequest(self, method, _uri, body='', files=None, headers={}, stream=False):
            """ 
            Makes httpsRequests to an XNAT host.

            @param method: The request method to run ('GET', 'PUT', 'POST', 
                'DELETE').
            @type: string

            @param _uri: The XNAT uri to run the request on.
            @type: string      

            @param body: The body contents of the request.  Defaults to an 
                empty string.
            @type: string

            @param headerAdditions: The additional header dictionary to add 
                to the request.
            @type: dict
            """

            #-------------------- 
            # Make the request arguments
            #--------------------
            url = Xnat.path.makeXnatUrl(self.host, _uri)
            print(f"{method} XNAT URL: {url}")
            if (body):
                print(body)

            #-------------------- 
            # Conduct REST call
            #-------------------- 
            # self.__requests_worker(method, url, body, files, headers, stream)
            t = threading.Thread(
                target=self.__requests_worker, 
                args=(method, url, body, files, headers, stream,))
            t.start()
            t.join()
                
            return self.response
            

        def __requests_worker(self, method, url, body, files, headers, stream):
            try:
                if method == 'POST':
                    self.response = self.session.post(url, headers=headers)
                elif method == 'GET':
                    self.response = self.session.get(url, stream=stream)
                elif method == 'PUT':
                    self.response = self.session.put(url, files=files, stream=stream)
                elif method == 'DELETE':
                    self.response = self.session.delete(url)
            except Exception as e:
                print(e)
                self.exceptionPopup.setText(str(e))
                self.exceptionPopup.show()


        def __downloadFailed(self, _src, _dst, dstFile, message):
            """ 
            Opens a QMessageBox informing the user
            of the failed download.

            @param _src: The source of the download file.
            @type _src: string

            @param _dst: The destination of the download file.
            @type _dst: string

            @param dstFile: The destination file that has been opened already.
            @type dstFile: file

            @param message: The message to indicated that the download failed.
            @type message: string
            """
            self.removeFromDownloadQueue(_src)
            dstFile.close()
            os.remove(dstFile.name)
            print("\nFailed to download '%s'.  Error: %s"%(_src, message))
            self.runEventCallbacks('downloadFailed', _src, _dst, message)




        def __getFile_httplib(self, _src, _dst):
            """
            NOT the preferred method for getting files from XNAT.

            This method exists as a backup to the urllib.request-based '__getFile' 
            function of Xnat.  It's currently not utilized by Xnat.

            urllib.request.urlopen + reponse.read is the preferred method for getting 
                files because 
            files can be downloaded in chunks (to allow for a progress
            indicator) as opposed to one grab, which http.client.HTTPSConnection 
            does.

            @param _src: The _src url to run the GET request on.
            @type _src: string

            @param _dst: The destination path of the GET (for getting files).
            @type _dst: string

            @param dstFile: The python 'file' classType to run the write the 
                file to.
            @type dstFile: file
            """

            #-------------------- 
            # Pre-download callbacks
            #-------------------- 
            self.runEventCallbacks('downloadStarted', _src, -1)
            self.runEventCallbacks('downloading', _src, 0)



            #-------------------- 
            # Download
            #-------------------- 
            response = self.__httpsRequest('GET', _src)
            data = response.read()  
            with open(_dst, 'wb') as f:
                f.write(data)     



            #-------------------- 
            # Post-download callbacks
            #--------------------     
            self.removeFromDownloadQueue(_src)
            self.runEventCallbacks('downloadFinished', _src)






        def __getFile_urllib(self, _src, _dst):
            """ 
            This method is in place for the main purpose of downlading
            a given source in packets (buffers) as opposed to one large file.

            It should be noted that the urllib.request manager-based convention of 
            authentication returns a 401 error if the server does not follow 
            the HTTP authentication standard (some CNDA machines are like this):

                #-------------------- 
                # RETURNS AN ERROR
                #-------------------- 
                >>> passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                >>> passman.add_password(None, _xnatSrc, self.user, \
                    self.password)
                >>> authhandler = urllib.request.HTTPBasicAuthHandler(passman)
                >>> opener = urllib.request.build_opener(authhandler)
                >>> urllib.request.install_opener(opener)
                >>> response = urllib.request.urlopen(_xnatSrc)


            A workaround was found for this issue.  It simply includes the 
            authentication header in the request, and we use urllib.request to open 
            the request.

                #-------------------- 
                # WORKS
                #-------------------- 
                >>> request = urllib.request.Request(xnatUrl)
                >>> request.add_header("Authorization", \
                    self.authHeader['Authorization'])
                >>> response = urllib.request.urlopen(request)



            @see:
            U{http://www.voidspace.org.uk/python/articles/authentication.shtml}
            U{http://blog.oneiroi.co.uk/python/python-urllib.request-basic-http-
                 authentication/}
            U{http://stackoverflow.com/questions/5131403/http-basic-
                 authentication-doesnt-seem-to-work-with-urllib.request-in-python}
            U{http://stackoverflow.com/questions/635113/python-urllib.request-
                 basic-http-authentication-and-tr-im/4188709#4188709}


            @param _src: The _src url to run the GET request on.
            @type _src: string

            @param _dst: The destination path of the GET (for getting files).
            @type _dst: string         
            """

            #-------------------- 
            # Open the local destination file 
            # so that it can start reading in the buffers.
            #-------------------- 
            try:
                dstDir = os.path.dirname(_dst)        
                if not os.path.exists(dstDir):
                    os.makedirs(dstDir)
                dstFile = open(_dst, "wb")
            except Exception as e:
                self.__downloadFailed(_src, _dst, dstFile, str(e))
                return



            #-------------------- 
            # Construct the request and authentication handler
            #-------------------- 
            xnatUrl = Xnat.path.makeXnatUrl(self.host, _src)
            request = urllib.request.Request(xnatUrl)
            request.add_header("Authorization", 
                               self.authHeader['Authorization'])



            #-------------------- 
            # Get the response from the XNAT host.
            #-------------------- 
            try:
                response = urllib.request.urlopen(request)




            #-------------------- 
            # If the urllib.request version fails then use http.client.
            # See get_http.client for more details.
            #-------------------- 
                #except urllib.request.HTTPError, e:
            except Exception as e:
                #print(str(e))
                #print(f"{_src} {_dst}")
                #print(d)
                self.__downloadFailed(_src, _dst, dstFile, str(e))
                return


            #-------------------- 
            # Get the content size, first by checking log, then by reading 
            # header
            #-------------------- 
            self.downloadTracker['downloadedSize']['bytes'] = 0   
            self.downloadTracker['totalDownloadSize'] = \
                                                self.getFileSize(xnatUrl)
            if not self.downloadTracker['totalDownloadSize']['bytes']:
                # If not in log, read the header
                if response.headers and "Content-Length" in response.headers:
                    self.downloadTracker['totalDownloadSize']['bytes'] = \
                                    int(response.headers["Content-Length"])  
                    self.downloadTracker['totalDownloadSize']['MB'] =  \
                            Xnat.utils.bytesToMB(\
                            self.downloadTracker['totalDownloadSize']['bytes'])


            #-------------------- 
            # Start the buffer reading cycle by
            # calling on the buffer_read function above.
            #-------------------- 
            bytesRead = self.__bufferRead(xnatUrl, dstFile, response)
            dstFile.close()




        def __getFile_requests(self, _src, _dst):
            """ 
            Replaces urllib and httplib __getFile methods

            @param _src: The _src url to run the GET request on.
            @type _src: string

            @param _dst: The destination path of the GET (for getting files).
            @type _dst: string         
            """

            #-------------------- 
            # Get the content size from scan json
            #-------------------- 
            self.downloadTracker['downloadedSize']['bytes'] = 0   
            self.downloadTracker['totalDownloadSize'] = self.getFileSize(_src)

            #-------------------- 
            # Pre-download callbacks
            #-------------------- 
            size = self.downloadTracker['totalDownloadSize']['bytes'] \
                   if self.downloadTracker['totalDownloadSize']['bytes'] else -1
            self.runEventCallbacks('downloadStarted', _src, size)
            self.runEventCallbacks('downloading', _src, 0)

            #-------------------- 
            # Open the local destination file 
            # so that it can start reading in the buffers.
            #-------------------- 
            try:
                dstFile = _dst
                dstDir = os.path.dirname(_dst)        
                if not os.path.exists(dstDir):
                    os.makedirs(dstDir)
                # print("dstFile: {}".format(dstFile))
            except Exception as e:
                print(e)
                self.__downloadFailed(_src, _dst, dstFile, str(e))
                self.exceptionPopup.setText(str(e))
                return

            #-------------------- 
            # Construct the request
            #-------------------- 
            url = Xnat.path.makeXnatUrl(self.host, _src)
            r = self.__httpsRequest('GET', url, stream=True)
            f = open(dstFile, 'wb')

            for chunk in r.iter_content(chunk_size=1024*1024):
                # Check for cancel event
                if not self.inDownloadQueue(_src):
                    f.close()
                    os.remove(f.name)
                    self.runEventCallbacks('downloadCancelled', _src)
                    break

                f.write(chunk)

                self.downloadTracker['downloadedSize']['bytes'] += len(chunk)
                self.runEventCallbacks('downloading', _src, 
                            self.downloadTracker['downloadedSize']['bytes'])

            r.close()
            f.close()

            #-------------------- 
            # Post-download callbacks
            #--------------------     
            self.removeFromDownloadQueue(_src)
            self.runEventCallbacks('downloadFinished', _src)



        def __bufferRead(self, _src, dstFile, response, bufferSize=8192):
            """
            Downloads a file by a constant buffer size.

            @param _src: The _src url to run the GET request on.
            @type _src: string

            @param dstFile: The open python file to write the buffers to.
            @type dstFile: file  

            @param response: The urllib.request response to read buffers from.
            @type response: A file-like object. 
                @see: U{http://docs.python.org/2/library/urllib.request.html}

            @param bufferSize: Buffer size to read.  Defaults to the standard 
                8192.
            @type bufferSize: integer

            @return: The total downloaded bytes.  
            @rtype: intengerhttp://docs.python.org/2/library/urllib.request.html
            """


            #--------------------
            # Pre-download callbacks
            #--------------------
            size = self.downloadTracker['totalDownloadSize']['bytes'] \
                   if self.downloadTracker['totalDownloadSize']['bytes'] else -1
            self.runEventCallbacks('downloadStarted', _src, size)



            #--------------------
            # Define the buffer read loop
            #--------------------
            while 1:     

                #
                # If DOWNLOAD CANCELLED
                #              
                if not self.inDownloadQueue(_src):
                    print("Cancelling download of '%s'"%(_src))
                    dstFile.close()
                    os.remove(dstFile.name)
                    self.runEventCallbacks('downloadCancelled', _src)
                    break


                #
                # If DOWNLOAD FINISHED
                #
                buffer = response.read(bufferSize)
                if not buffer: 
                    # Pop from the queue
                    self.removeFromDownloadQueue(_src)
                    self.runEventCallbacks('downloadFinished', _src)
                    break


                #
                # Otherwise, Write buffer chunk to file
                #
                dstFile.write(buffer)

                #
                # And update progress indicators
                #
                self.downloadTracker['downloadedSize']['bytes'] += len(buffer)
                self.runEventCallbacks('downloading', _src, 
                            self.downloadTracker['downloadedSize']['bytes'])


            return self.downloadTracker['downloadedSize']['bytes']





        def __getJson(self, _uri):
            """ 
            Returns a json object from a given XNAT URI using
            the internal method '__httpsRequest'.

            @param _uri: The xnat uri to retrieve the JSON object from.
            @type _uri: string

            @return: A dictionary of the JSON result.
            @rtype: dict
            """

            #-------------------- 
            # Add explicit format=json if not already there
            #--------------------  
            if 'format=json' not in _uri:
                if '?' in _uri:
                    _uri += '&format=json'
                else:
                    _uri += '?format=json'


            #-------------------- 
            # Get the response from httpRequest
            #--------------------     
            xnatUrl = Xnat.path.makeXnatUrl(self.host, _uri)
            r = self.__httpsRequest('GET', xnatUrl)

            #-------------------- 
            # Try to load the response as a JSON...
            #-------------------- 
            try:
                return r.json()['ResultSet']['Result']
            except Exception as e:
                self.exceptionPopup.setText(str(e))
                self.runEventCallbacks('jsonError', self.host.encode(),
                                       self.username.encode(), r)



    class utils(object):
        """
        Utility methods for Xnat.
        """   
        @staticmethod
        def bytesToMB(bytes):
            """ 
            Converts bytes to MB, retaining the number type.
            
            @param bytes: The bytes to convert to MB.
            @type: number (integer)
            
            @return: The numerical value of bytes converted to MB.
            @rtype: float
            """
            bytes = int(bytes)
            mb = str(bytes/(1024*1024.0)).split(".")[0] + "." + \
                 str(bytes/(1024*1024.0)).split(".")[1][:2]
            return float(mb)



    class path(object):
        """
        URI/URL methods specific to XNAT interaction.
        """                
    
        QUERY_FILTERS = {
            'accessible' : 'accessible=true',
            'imagesonly' : 'xsiType=xnat:imageSessionData',
        }

        DEFAULT_LEVELS =  [
            'projects', 
            'subjects', 
            'experiments',
            'scans', 
            'slicer', 
            'files'
        ]
        
        DEFAULT_PATH_DICT = dict((level, None) for level in DEFAULT_LEVELS)
        DEFAULT_PATH_DICT['resources'] = None
        
        HIGHEST_FOLDER_ADD_LEVEL  = 'experiments'



        @staticmethod
        def modifySrcDstForZipDownload(src, dstBase):   
            """
            Modifies the variables src and dstBase to create a new src and a dst
            for downloading a zipped set of files form XNAT.  

            @param src: The source URI to modify.
            @type src: str

            @param dstBase: The base destination URI to create the appropriate 
                dst from.
            @type dstBase: str

            @returns: The modified src, dst as tuples
            @rtypes: str, str
            """ 

            src = src + "?format=zip"
            dst = os.path.join(dstBase , 'projects' + 
                               src.replace('?format=zip', '').\
                        split('projects')[1].split('/files')[0] + '/files.zip')
            return src, dst




        @staticmethod
        def getUriAt(_uri, level):
            """ 
            Returns the XNAT path from '_uri' at the 
            provided 'level' by splicing '_uri' accordingly 
            and then adding 'level' as the suffix.
            
            @param _uri: The xnat uri to retrieve the JSON object from.
            @type _uri: string
            
            @param level: The the XNAT level to splice _uri at, then append to
                the spliced string.
            @type level: string

            @return: The spliced uri with 'level' as a suffix.
            @rtype: string
            
            @raise: Error if level is not found in the _uri.
            """
            #print("%s %s"%(, _uri, level))
            if not level.startswith('/'):
                level = '/' + level
            if level in _uri:
                return  _uri.split(level)[0] + level
            else:
                raise Exception("Invalid get level '%s' parameter: %s"%(\
                                                            _uri, level))



        @staticmethod
        def cleanUri(uri):
            """ 
            Removes any double-slashes
            with single slashes.  Removes the 
            last character if the string ends
            with a '/'
            
            @param uri: The xnat URL to clean.
            @type uri: string

            @return: The cleaned uri.
            @rtype: string            
            """
            if not uri.startswith("/") and not uri.startswith('http'):
                uri = "/" + uri

            if 'http://' in uri or 'https://' in uri:
                uri = uri.split('://')[0] + '://' + \
                      uri.split('://')[1].replace("//", "/")
            else:
                uri = uri.replace("//", "/")

            if uri.endswith("/"):
                uri = uri[:-1]

            return uri



        @staticmethod
        def applyQueryArguments(_uri, queryArgs):
            """ 
            Using the  Xnat.QUERY_FILTERS,
            appends the relevant arguments to a given queryURI.  Usually
            for 'xsiType' calls and modifications to query URIs specific
            to a given XNAT level.
            
            @param _uri: The partial or full XNAT query uri
            @type _uri: string

            @param queryArgs: The list of query argument suffixes to apply.
            @type queryArgs: list.<string>
            
            @return: The XNAT query uri with the arguments added to it.
            @rtype: string
            """
            queryArgStr = ''
            for i in range(0, len(queryArgs)):
                queryArgStr += '?' if i == 0 else '&'
                queryArgStr += str(Xnat.path.QUERY_FILTERS[queryArgs[i].\
                                                           lower()])
            return _uri + queryArgStr



        @staticmethod
        def makeXnatUrl(host, _url):
            """
            Adds the necessary prefixes to the _url argument
            so as to produce a full XNAT url.
            
            @param _url: The partial or full XNAT query uri
            @type _url: string
            
            @return: The full XNAT url to run the query on.
            @rtype: string
            """

            if isinstance(_url, bytes):
                _url = _url.decode(sys.getdefaultencoding())
        
            if _url.startswith('/'):
                _url = _url[1:]

            if not _url.startswith(host):
                if _url.startswith('data/'):
                    _url = requests.compat.urljoin(host, _url)
                else:
                    prefixUri = requests.compat.urljoin(host, 'data/archive/')
                    _url = requests.compat.urljoin(prefixUri, _url)


            #--------------------
            # Remove double slashes
            #--------------------
            _url = _url.replace('//', '/')
            if 'http:/' in _url:
                _url = _url.replace('http:/', 'http://')
            elif 'https:/' in _url:
                _url = _url.replace('https:/', 'https://')

            return _url




    class xsi(object):
        """
        Methods and varables for XNAT xsi experiment types.
        """
        DEFAULT_TYPES =  {
            'MR Session': 'xnat:mrSessionData',
            'PET Session': 'xnat:petSessionData',
            'CT Session' : 'xnat:ctSessionData'
        }


    class metadata(object):
        """
        Methods and varables for managing and retrieving XNAT metadata.
        """

        DEFAULT_TAGS =  {
         'LABELS' : [
             'ID',
             'id',
             'name',
             'Name',
             'label',
         ],
         'projects' : [
             'last_accessed_497',
             'ID',
             'id',
             'insert_user',
             'pi',
             'insert_date',
             'description',
             'secondary_ID',
             'pi_lastname',
             'pi_firstname',
             'project_invs',    
             'project_access_img',    
             'user_role_497',    
             'quarantine_status'
             'URI',
         ],
         'subjects' : [
             'ID',
             'label',
             'insert_date',
             'insert_user',
             'totalRecords'
             'project',
             'URI',
         ],
         'experiments' : [
             'ID',
             'label',
             'insert_date',
             'totalRecords',
             'date',
             'project',
             'xsiType',
             'xnat:subjectassessordata/id',
             'URI',
         ],
         'scans' : [
             'series_description',
             'note',
             'type',
             'xsiType',
             'quality',
             'xnat_imagescandata_id',
             'URI',
             'ID'
         ],
         'resources' : [
             'element_name',
             'category',
             'cat_id',
             'xnat_abstractresource_id',
             'cat_desc'
         ],
         'files' : [
             'Size',
             'file_format',
             'file_content',
             'collection',
             'file_tags',
             'cat_ID',
             'URI',
             'Name'
         ],
         'slicer' : [
             'Size',
             'file_format',
             'file_content',
             'collection',
             'file_tags',
             'cat_ID',
             'URI',
             'Name'
         ]
        }


        DEFAULT_TAGS_LITE = {
            'projects' : [
                'last_accessed_497',
            ],
            'subjects' : [
                'label',
            ],
            'experiments' : [
                'date',
            ],        
            'scans' : [
                'series_description',
                'type',
                'quality',
            ],
            'resources' : [
                'element_name',
            ],
            'files' : [
                'Size',
            ],
            'slicer' : [
                'Size',
            ]
        }

        DEFAULT_DATE_TAGS =  [ 'last_accessed_497', 'insert_date']  

        @staticmethod
        def getTagsByLevel(xnatLevel):
            """ 
            Returns the appropriate tag list by the given
            'xnatLevel' argument.

            @param xnatLevel: The pertinent XNAT level to 
                get the default metadat from.
            @type xnatLevel: string

            @rtype: An array of strings referring to the XNAT metadata tags.
            @returns: The relevant XNAT metadata tags for the provided level. 

            @raise If the value of 'xnatLevel' doesn't exist within the default
                XNAT metadata hierarchy.
            """
            xnatLevel = xnatLevel.lower()
            if not xnatLevel in Xnat.metadata.DEFAULT_TAGS:
                raise Exception("Invalid XNAT level: %s"%(xnatLevel))
            return Xnat.metadata.DEFAULT_TAGS[xnatLevel]



  





