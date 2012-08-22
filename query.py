import oauth2 as oauth
import urlparse
import yql
import json
from urllib import urlencode
from yql.storage import FileTokenStore
import os
import time
import re
from secret import KEY, SECRET, TOKEN_SECRET

class QueryManager:
    """
    Go get me some damn fantasy stats
    """

    def __init__(self, **kwargs):
        # Create your consumer with the proper key/secret.
        self.consumer = oauth.Consumer(key=KEY, secret=SECRET)
        self.yql_manager = yql.ThreeLegged(KEY, SECRET)

        # Request token URL for Yahoo.
        self.client = None
        self.auth_token = None
        
        self.get_token()

        self._next_query = time.time()
        self._time_between_queries = int(kwargs.get('sleep', 10))

    def set_sleep(self, interval):
        """
        Change sleep time between queries
        """
        self._time_between_queries = interval

    def get_token(self):
        """
        Login and all that crap
        """
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'cache'))
        token_store = FileTokenStore(path, secret=TOKEN_SECRET)

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

    def run_yql_query(self, query, **kwargs):
        """
        Function to run simple queries for testing
        """
        params = self.yql_manager.get_query_params(query, None)
        query_string = urlencode(params)
        retry = kwargs.get('retry', True)
        result = None
        while not result:
            raw_result = self.run_url_query('%s?%s&diagnostics=true' % (self.yql_manager.uri, query_string))
            if retry:
                result = self.__class__.decode_query(raw_result).get('query').get('results')
            else:
                result = True
            if not result:
                print 'No result returned, retrying query'
        return raw_result

    def run_url_query(self, query_url):
        """
        Function to run simple queries for testing
        """
        current_time = time.time()
        if current_time < self._next_query:
            time.sleep(self._next_query - current_time)
        self._next_query = time.time() + self._time_between_queries
        self.get_token()
        return self.client.request(query_url, "GET")

    def batch_query(self, query, value_list, **kwargs):
        """
        Method to auto-iterate DB while packing queries together to reduce
        the amount of hits to yahoo

        @param query: Query string to use on database. Use @value where you
            want items to be substituted
        @param value_list: List of values to substitute into queries
        """
        query_re = re.compile(r'(value)')

        block_size = kwargs.get('block_size', 10)
        index = kwargs.get('start', 0)
        end = kwargs.get('end', len(value_list))

        while index < end:
            escaped_list = ["'%s'" % str(value) for value in value_list[index:(index + block_size)]]
            join_str = ', '
            value_str = join_str.join(escaped_list)
            ret_query = self.run_yql_query(query_re.sub(value_str, query))
            key, results = self.__class__.decode_query(ret_query).get('query').get('results').popitem()
            if isinstance(results, dict):
                yield results
            else:
                for result in results:
                    yield result
            index = index + block_size

    @staticmethod
    def decode_query(query_obj):
        """
        Decode out the query object into python native format
        
        @param query_obj: Object returned from run_*_query
        """
        try:
            header, result = query_obj
            decoded_result = json.loads(result)
        except ValueError:
            print query_obj, result
            raise
        diag = decoded_result.get("query").get("diagnostics").get("url")
        if isinstance(diag, list):
            diag = diag.pop()
        if diag.get("http-status-code") == '999':
            raise ValueError("%s: %s" % (diag.get("http-status-code"), diag.get('http-status-message')))
        return decoded_result
