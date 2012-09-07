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
    wins = models.SmallIntegerField(default=0)
    losses = models.SmallIntegerField(default=0)
    ties = models.SmallIntegerField(default=0)
    rank = models.SmallIntegerField(default=0)

    query_manager = QueryManager()

    @classmethod
    def load_teams(cls, league_id):
        """
        Load teams from yahoo into db
        """
        print 'Loading teams'
        query_str = "select * from fantasysports.teams where league_key='%s'" % league_id
        teams = QueryManager.decode_query(cls.query_manager.run_yql_query(query_str, retry=False)).get('query').get('results').get('team')
        query_str = "select standings.teams.team.team_key, standings.teams.team.team_standings from fantasysports.leagues.standings where league_key='%s'" % (league_id)
        results = QueryManager.decode_query(cls.query_manager.run_yql_query(query_str, retry=False)).get('query').get('results').get('league')
        standings = { 
                item.get('standings').get('teams').get('team').get('team_key'):
                item.get('standings').get('teams').get('team').get('team_standings')
                for item in results
                }
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
            outcome_totals = standings.get(team_key).get('outcome_totals')
            team.wins   = int(outcome_totals.get('wins'))
            team.losses = int(outcome_totals.get('losses'))
            team.ties   = int(outcome_totals.get('ties'))
            team.rank   = int(standings.get(team_key).get('rank'))
            team.save()

    class Meta:
        """ Metadata class for Team """
        app_label = 'analyze'

