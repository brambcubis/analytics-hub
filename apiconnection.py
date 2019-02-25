# -*- coding: utf-8 -*-
"""
Created on Mo Feb 25 2019
LastModified on Mo Feb 25 2019

@author: Bram Buysschaert

25/02:
- Defining the ConnectSacHub class (v0.1)
- Defining the .connect() method (v0.1)
- Defining the .updateNewReport() method (v0.1; no workaround for timestamp issue)


"""

# Include packages
from oauthlib import oauth2
from requests_oauthlib import OAuth2Session
import csv
import time, datetime

# Set the logging
import logging

# Create extra functionality

# Function to see status code
# Function to test status code
#


# Generate the class
class ConnectSacHub:
    """
    Class that provides the interaction with the SAC Hub API that you wish for this POC.
    It has various methods, that each have a specific function / purpose
    """
    def __init__(self, credFile, tokenFile):
        """Initialize the ConnectSacHub class"""
        self.credFile = credFile
        self.tokenFile = tokenFile
        self.cred = {}
        self.token = {}
        self.base = ''
        self.client = None
        self.xcsrf = ''
        self.headers = {'x-csrf-token': 'fetch', 'Content-Type': 'application/json'}
        self.currentTime = time.time()      #Get the current Unix time stamp (it is implied to be UTC) in seconds!

    # =========================================================
    #Methods that you would call
    # =========================================================
    def connect(self):
        """
        Establish a connection through Python with the API of SAC Hub
        It uses the credFile and tokenFile as input and might generate a new token, if needed
        """
        print('Trying to establish a connection with the API')
        self.readCred()
        self.readToken()
        try:
            self.getClient()      # Create oauth client
            # Test connection
            if self.testClient():
                print(f'\tConnection established with info from "{self.tokenFile}"')
                pass
        except:
            self.newToken()      # Create new token
            self.writeToken()      # Write token out
            self.getClient()      # Create oauth client
            # Test connection
            if self.testClient():
                print(f'\tConnection established with updated token')
                pass
            else:
                raise SystemError('Could not create a login token!')
        # Give the user feedback on how long the token remains valid
        timediff_token = datetime.datetime.utcfromtimestamp(self.token['expires_at']) - datetime.datetime.utcfromtimestamp(self.currentTime)
        print('\tToken expires in {:.2f}h'.format(timediff_token.seconds / 3600))
        # Get a new X-CSRF-Token
        self.fetchXcsrf()

    def updateNewReport(self, timeDiffMax = 14.):
        """
        Update the NewReport lov for all assets in the SAC Hub store
        Assets are considered "new" when the last change happened less than timeDiffMax days ago!
        timeDiffMax: time difference in *days*
        """
        print('Updating the "NewReport" lov of your *live* store')
        self.getLiveStore()
        # Test the age of each report
        newAsset = []
        print('\tDANGER:Look into the code: explicit wrong equation for debugging!')
        for timeMod in self.lastModified: # Need explicit for-loop, since datetime does not allow for list input
            timediff = (datetime.datetime.utcfromtimestamp(self.currentTime) -
            datetime.datetime.utcfromtimestamp(timeMod)).days   # Could still use the hours to round up, but not enabled
            if timediff < 1: #WARNING WARNING WARNING FOR DEBUGGING ONLY
                newAsset.append('Yes')
            else:
                newAsset.append('No')
        # Loop over the assets and update the assets
        for asset, id, newAsset in zip(self.store, self.assetid, newAsset):
            lovFields = asset['lovFields'].items()
            for key_lovo, val_lovo in lovFields:
                for key_lovi, val_lovi in val_lovo.items():
                    if val_lovi == 'New Report':
                        print(key_lovo, key_lovi, val_lovi)
                print(key_lovo, val_lovo)


    # =========================================================
    # Methods that are called by other methods for functionality
    # =========================================================
    def readCred(self):
        """Get the login credentials from the credFile"""
        # WARNING: no header allowed in input file!
        print(f'\tReading credentials file "{self.credFile}"')
        with open(self.credFile) as csvfile:
            reader = csv.reader(csvfile)
            self.cred = {rows[0]:rows[1] for rows in reader}
        # Get the base explicit for easier referencing
        self.base = self.cred['base_url']

    def readToken(self):
        """Get the access token from the tokenFile"""
        # WARNING: no header allowed in input file!
        print(f'\tReading token file "{self.tokenFile}"')
        with open(self.tokenFile) as csvfile:
            reader = csv.reader(csvfile)
            self.token = {rows[0]:rows[1] for rows in reader}
        self.token['scope'] = [''] # Not explictly saved and likely not needed!
        self.token['expires_at'] = float(self.token['expires_at'])

    def newToken(self):
        """
        Update the access token, because the token from the tokenFile has expired or is unreadable
        Requires the user to go to the website, authorize the token and provide the response
        """
        self.client = OAuth2Session(client_id=self.cred['client_id'], redirect_uri=self.cred['redirect_uri'])
        authorization_url, state = self.client.authorization_url(self.cred['authorize_url'])
        # Ask the user to authorize with the created url (and their login cred)
        print(f'Please following the following link and authorize to generate a token\n{authorization_url}')
        # Ask the response of the authorization request
        authorization_response = input('\nEnter the full callback / response URL from authorization\n')
        print('\tNow generating a token')
        # Fetch the token itself
        self.token = self.client.fetch_token(self.cred['token_url'], authorization_response=authorization_response, client_id=self.cred['client_id'],  client_secret=self.cred['client_secret'])

    def writeToken(self):
        """Write out the access token, because you generated a new token"""
        print(f'\tUpdating token file "{self.tokenFile}"')
        with open(self.tokenFile, 'w', encoding = 'UTF-8', newline='') as file:
            writer = csv.writer(file)
            for key, value in self.token.items():
                if key != 'scope':
                    writer.writerow((key, value))

    def getClient(self):
        """Create the oauthlib client for the connection"""
        self.client = OAuth2Session(client_id=self.cred['client_id'], redirect_uri=self.cred['redirect_uri'],
                                    token=self.token)

    def testClient(self):
        """Test the oauthlib connection to the client with a get request to the user profile and return boolean for success"""
        r = self.client.get(self.base + 'profile')
        return r.ok

    def fetchXcsrf(self):
        """Fetch a new X-CSRF-token from a get request to the user profile and update the header"""
        print('\tFetching a new X-CSRF-Token')
        r = self.client.get(self.base + 'profile', headers=self.headers)
        if r.ok:
            self.xcsrf = r.headers['x-csrf-token']
            self.headers['x-csrf-token'] = self.xcsrf
            print('\tX-CSRF-Token updated')

    def getLiveStore(self):
        """Retrieve the full information of your live assets in your SAC Hub store"""
        print('\tGETting the information of your live store')
        r = self.client.get(self.base + 'asset/recent', headers=self.headers)
        self.store = r.json()
        self.assetid = []
        self.created = []
        self.lastModified = []
        for asset in self.store:
            self.assetid.append(asset['id'])
            self.created.append(asset['created'])
            try:
                self.lastModified.append(asset['lastModified'] / 1000.) # Unix timestamp in seconds, was milliseconds!
            except: # In case there was no lastModified tag (unsure if this can actually happen!)
                self.lastModified.append(asset['created'] / 1000.) # Unix timestamp in seconds, was milliseconds!





if __name__ == '__main__':
    # Call the class to generate a token
    my_connection = ConnectSacHub('./credits.dat', './token.dat')
    my_connection.connect()
    my_connection.updateNewReport()
    # Peform update of newDraft
