"""
Team management
"""
from utils.query import QueryManager
from django.db import models
from analyze.models.league import League

class Team(models.Model):
    """
    Fantasy team model
    """
    team_key = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=32)
    manager_name = models.CharField(max_length=32)
    league = models.ForeignKey(League, related_name='teams')

    query_manager = QueryManager()

    @classmethod
    def load_teams(cls, league_id):
        """
        Load teams from yahoo into db
        """
        query_str = "select * from fantasysports.teams where league_key='%s'" % league_id
        results = QueryManager.decode_query(cls.query_manager.run_yql_query(query_str, retry=False)).get('query').get('results')
        teams = results.get('team')
        league = League.objects.get(league_key=league_id)
        for raw_team in teams:
            team_key = raw_team.get('team_key')
            team, created = cls.objects.get_or_create(team_key=team_key, defaults={'league': league})
            if not created:
                print 'Team key already exists, reloading team data %s' % team_key
            else:
                print 'Creating team %s' % team_key
            team.team_key = team_key
            name = ''
            managers = raw_team.get('managers').get('manager')
            if isinstance(managers, list):
                join_str = ' + '
                name = join_str.join([ item.get('nickname') for item in managers ])
            else:
                name = managers.get('nickname')
            team.name = raw_team.get('name')
            team.manager_name = name
            team.league = league
            team.save()

    class Meta:
        """ Metadata class for Team """
        app_label = 'analyze'

