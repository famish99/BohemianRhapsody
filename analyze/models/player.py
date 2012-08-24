"""
Player info management
"""
from utils.query import QueryManager
from django.db import models
import os
import pickle

class Player(models.Model):
    """
    Player data model, contains just generic information about player
    """

    player_key = models.CharField(max_length=16)
    position = models.CharField(max_length=16)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    team_key = models.CharField(max_length=16)
    team_name = models.CharField(max_length=32)
    bye_week = models.CharField(max_length=8)

    query_manager = QueryManager()

    def __init__(self, *args, **kwargs):
        self._raw_info = None
        super(Player, self).__init__(*args, **kwargs)

    def load_raw(self, p_id, **kwargs):
        """
        Load player data from file
        """
        filename = os.path.join(kwargs.get('directory'), p_id)
        with open(filename, 'r') as fread:
            self._raw_info = pickle.load(fread)

    def load_db(self, **kwargs):
        """
        Load data from raw files into db
        """
        join_str = ','

        self.player_key = self._raw_info.get('player_key') 
        position = self._raw_info.get('eligible_positions').get('position')
        if isinstance(position, list):
            position = join_str.join(position)
        self.position = position
        self.first_name = self._raw_info.get('name').get('first')
        self.last_name  = self._raw_info.get('name').get('last')
        self.team_key   = self._raw_info.get('editorial_team_key')
        self.team_name  = self._raw_info.get('editorial_team_full_name')
        self.bye_week   = self._raw_info.get('bye_weeks').get('week')

    def eligible_player(self, **kwargs):
        """
        Search for eligible players for your league. For example, defensive
        players aren't used in standard formats.
        """
        eligible_positions = kwargs.get('positions', ('O', 'K'))
        position_type = self._raw_info.get('position_type', 'X')
        return position_type in eligible_positions

    @classmethod
    def find_all(cls, **kwargs):
        """
        Since Yahoo is a bitch, go scrub the db and find which player ids
        actually exist
        """

        start = kwargs.get('start', 0)
        end = kwargs.get('end', 25000)
        filename = kwargs.get('filename', 'player.log')
        game = kwargs.get('game', 'nfl')
        with open(filename, 'w') as output:
            for player_id in range(start, end):
                if player_id < 10000:
                    player_id = '%s.p.%04d' % (game, player_id)
                else:
                    player_id = '%s.p.%d' % (game, player_id)
                query_str = "select * from fantasysports.players where player_key='%s'" % player_id
                results = QueryManager.decode_query(cls.query_manager.run_yql_query(query_str, retry=False)).get('query').get('results')
                if results:
                    results = results.get('player')
                    print '%s: True' % player_id
                    output.write('%s\n' % player_id)
                    cls.store_raw_info(player_id, results, **kwargs)
                else:
                    print '%s: False' % player_id
                output.flush()

    @classmethod
    def store_raw_info(cls, p_id, result, **kwargs):
        """
        Grab player info from yahoo and store it locally so that I don't have to rape
        my damn rate limits any time I want some new information
        """
        filename = os.path.join(kwargs.get('directory'), p_id)
        with open(filename, 'w') as output:
            pickle.dump(result, output)

    class Meta:
        """ Metadata class for Player """
        app_label = 'analyze'

