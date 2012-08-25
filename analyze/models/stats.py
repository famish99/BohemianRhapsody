"""
Statistical data models 
"""
from utils.query import QueryManager
from django.db import models
from picklefield.fields import PickledObjectField
from analyze.models.player import Player

class PlayerStats(models.Model):
    """
    Contains the actual stat info for nfl players
    """

    player = models.ForeignKey(Player, related_name='stats')
    week_num = models.SmallIntegerField()
    stat_data = PickledObjectField()

    def __init__(self, *args, **kwargs):
        super(PlayerStats, self).__init__(*args, **kwargs)
        if not self.stat_data:
            self.stat_data = {}

    def load_stats(self, result, **kwargs):
        """
        Take the decoded object from the query and shove it into a more
        compact form

        @param result: The decoded query
        """
        stat_list = result.get('player_stats').get('stats').get('stat')
        for item in stat_list:
            key = item.get('stat_id')
            value = int(item.get('value'))
            self.stat_data[key] = value
        print self.stat_data

    class Meta:
        """ Metadata class for PlayerStats """
        app_label = 'analyze'

