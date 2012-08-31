"""
Player info management
"""
from utils.query import QueryManager
from django.db import models
import os
import pickle
import numpypy

class Player(models.Model):
    """
    Player data model, contains just generic information about player
    """

    player_key = models.CharField(max_length=16, unique=True)
    position = models.CharField(max_length=16)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=32)
    team_key = models.CharField(max_length=16)
    team_name = models.CharField(max_length=32)
    bye_week = models.CharField(max_length=8)
    season_points = models.FloatField(default=0.0, null=False)

    query_manager = QueryManager()

    def __init__(self, *args, **kwargs):
        super(Player, self).__init__(*args, **kwargs)
        self._raw_info = None
        self._points = None

    def __unicode__(self):
        return '%s: %s %s' % (self.player_key, self.first_name, self.last_name)

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

    def get_points(self, **kwargs):
        """
        Return a list of the points scored
        """
        raw_points = [ stat.total_points() for stat in self.stats.exclude(
            week_num=int(self.bye_week))
            ]
        if kwargs.get('raw'):
            self._points = raw_points
        else:
            self._points = filter(lambda x: x != 0, raw_points)
        return self._points

    def _season_points(self, **kwargs):
        """
        Calculate points for the whole season
        """
        if not self._points:
            self.get_points()
        return numpypy.sum(self._points)

    def mean_points(self, **kwargs):
        """
        Return the mean score
        """
        if not self._points:
            self.get_points()
        return round(numpypy.mean(self._points), 2)

    def median_points(self, **kwargs):
        """
        Return median score
        """
        if not self._points:
            self.get_points()
        if len(self._points) % 2:
            return sorted(self._points)[len(self._points)/2]
        else:
            mid = len(self._points) / 2
            return numpypy.mean(sorted(self._points)[(mid - 1):(mid + 1)])

    def std_dev_points(self, **kwargs):
        """
        Return score variance
        """
        if not self._points:
            self.get_points()
        return round(numpypy.std(self._points), 2)

    def games_played(self, **kwargs):
        """
        Return number of non-zero games
        """
        if not self._points:
            self.get_points()
        return len(self.get_points())


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

    @classmethod
    def get_stats(cls, league_key, week, **kwargs):
        """
        Get stat data for the player
        """
        import analyze.models.stats as stats
        #player_list = [p.player_key for p in cls.objects.all()]
        player_list = []
        for p in cls.objects.all():
            if not p.stats.filter(week_num=week).exists():
                player_list.append(p.player_key)
            else:
                print 'Data exists for %s week %d' % (p.player_key, week)
        query_str = "select player_key, player_stats from fantasysports.players.stats where league_key='%s' and player_key in (value) and stats_type='week' and stats_week='%s'" % (league_key, str(week))
        for result in cls.query_manager.batch_query(query_str, player_list):
            p_key = result.get('player_key')
            player = cls.objects.get(player_key=p_key)
            print "%s week %d" % (player, week)
            try:
                p_stats = stats.PlayerStats()
                p_stats.player = player
                p_stats.week_num = week
                p_stats.load_stats(result)
                p_stats.save()
                player.season_points = player._season_points()
                player.save()
            except ValueError as e:
                print e

    class Meta:
        """ Metadata class for Player """
        app_label = 'analyze'

