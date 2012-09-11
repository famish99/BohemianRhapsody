"""
League module
"""
from utils.query import QueryManager
from django.db import models
from django.utils.datastructures import SortedDict


YEAR_KEYS = SortedDict([
    ('257', '2011'),
    ('273', '2012'),
    ])


class League(models.Model):
    """
    League data model, contains fantasy league info
    """
    league_key = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=32)
    start_week = models.SmallIntegerField()
    end_week = models.SmallIntegerField()
    current_week = models.SmallIntegerField()
    scoring_type = models.CharField(max_length=16)

    query_manager = QueryManager()

    def __unicode__(self):
        return '%s: %s' % (self.league_key, self.name)

    def year(self):
        """
        Return the year of the league
        """
        league_pre, league_id = self.league_key.split('.l.', 1)
        return YEAR_KEYS.get(league_pre)

    @classmethod
    def load_league(cls, league_id, **kwargs):
        """
        Load league data from yahoo into db
        """
        league, created = cls.objects.get_or_create(league_key=league_id)
        if not created:
            print 'League key already exists, reloading league data %s' % league_id
        else:
            print 'Creating league %s' % league_id
        query_str = "select * from fantasysports.leagues where league_key='%s'" % league_id
        results = QueryManager.decode_query(cls.query_manager.run_yql_query(query_str)).get('query').get('results').get('league')
        league.league_key = results.get('league_key')
        league.name = results.get('name')
        league.scoring_type = results.get('scoring_type')
        league.start_week = int(results.get('start_week'))
        league.end_week = int(results.get('end_week'))
        league.current_week = int(results.get('current_week'))
        league.save()

    class Meta:
        """ Metadata class for League """
        app_label = 'analyze'

