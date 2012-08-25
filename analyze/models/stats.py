"""
Statistical data models 
"""
from utils.query import QueryManager
from django.db import models
from picklefield.fields import PickledObjectField
from analyze.models.player import Player


def calc_pts_allowed(pts):
    """
    Since it's not exactly linear, manually calculate dem points
    """
    if pts == 0:
        return 10
    elif pts < 7:
        return 7
    elif pts < 14:
        return 4
    elif pts < 21:
        return 1
    elif pts < 28:
        return 0
    elif pts < 35:
        return -1
    else:
        return -4


STATS = {
        '4': ('Pass Yds',     lambda x: x / 25.0 ),
        '5': ('Pass TD',      lambda x: x * 4 ),
        '6': ('INT',          lambda x: x * -1 ),
        '9': ('Rush Yds',     lambda x: x / 10.0 ),
        '10': ('Rush TD',     lambda x: x * 6 ),
        '12': ('Rec Yds',     lambda x: x / 10.0 ),
        '13': ('Rec TD',      lambda x: x * 6 ),
        '15': ('Ret TD',      lambda x: x * 6 ),
        '16': ('2pt',         lambda x: x * 2 ),
        '18': ('Fumbles',     lambda x: x * -2 ),
        '19': ('FG 0-19',     lambda x: x * 3 ),
        '20': ('FG 20-29',    lambda x: x * 3 ),
        '21': ('FG 30-39',    lambda x: x * 3 ),
        '22': ('FG 40-49',    lambda x: x * 4 ),
        '23': ('FG 50+',      lambda x: x * 5 ),
        '29': ('PAT',         lambda x: x * 1 ),
        '31': ('Pts Allowed', lambda x: calc_pts_allowed(x) ),
        '32': ('Sack',        lambda x: x * 1 ),
        '33': ('INT',         lambda x: x * 2 ),
        '35': ('TD',          lambda x: x * 6 ),
        '36': ('Safety',      lambda x: x * 2 ),
        '37': ('Blk Kick',    lambda x: x * 2 ),
        '49': ('Ret TD',      lambda x: x * 6 ),
        '57': ('',            lambda x: 0 ),
        }


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

    def total_points(self, **kwargs):
        """
        Return the total points for the player for the week
        """
        points = 0
        for key, value in self.stat_data.items():
            points = points + STATS[key][1](value)
        return points

    class Meta:
        """ Metadata class for PlayerStats """
        app_label = 'analyze'

