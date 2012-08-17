import oauth2 as oauth
import urlparse
import yql
import json
from urllib import urlencode
from yql.storage import FileTokenStore
import os

KEY = "dj0yJmk9TU9pcUhubWRNdEFvJmQ9WVdrOWJVeDZSVTVXTkhVbWNHbzlNVEU1TkRJeE5qWXkmcz1jb25zdW1lcnNlY3JldCZ4PTY2"
SECRET = "51941abecc25b4bd159329860103fdd5fde7b490"

class QueryManager:
    """
    Go get me some damn fantasy stats
    """

    def __init__(self):
        # Create your consumer with the proper key/secret.
        self.consumer = oauth.Consumer(key=KEY, secret=SECRET)
        self.yql_manager = yql.ThreeLegged(KEY, SECRET)

        # Request token URL for Yahoo.
        self.client = None
        self.auth_token = None
        
        self.get_token()

    def get_token(self):
        """
        Login and all that crap
        """
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'cache'))
        token_store = FileTokenStore(path, secret='WRNdEFvJmQ9WVdrOWJVeDZSV')

        stored_token = token_store.get('fantasy')

        if not stored_token:
            # Do the dance
            request_token, auth_url = self.yql_manager.get_token_and_auth_url()
            print "Visit url %s and get a verifier string" % auth_url
            verifier = raw_input("Enter the code: ")
            self.auth_token = self.yql_manager.get_access_token(request_token, verifier)
            token_store.set('fantasy', self.auth_token)
        else:
            # Check access_token is within 1hour-old and if not refresh it
            # and stash it
            self.auth_token = self.yql_manager.check_token(stored_token)
            if self.auth_token != stored_token:
                token_store.set('fantasy', self.auth_token)

        # Create our client.
        self.client = oauth.Client(self.consumer, self.auth_token)

    def run_yql_query(self, query):
        """
        Function to run simple queries for testing
        """
        params = self.yql_manager.get_query_params(query, None)
        query_string = urlencode(params)
        return self.run_url_query('%s?%s' % (self.yql_manager.uri, query_string))

    def run_url_query(self, query_url):
        """
        Function to run simple queries for testing
        """
        self.get_token()
        return self.client.request(query_url, "GET")

    def decode_query(self, query_obj):
        """
        Decode out the query object into python native format
        
        @param query_obj: Object returned from run_*_query
        """
        header, result = query_obj
        decoded_result = json.loads(result)
        return decoded_result
