"""
Team management
"""
from analyze.models.league import League
from analyze.models.player import Player
from utils.query import QueryManager
from django.db import models
from django.utils.datastructures import SortedDict


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
    players = models.ManyToManyField(Player, through='Roster')

    query_manager = QueryManager()

    def __unicode__(self):
        return '%s: %s' % (self.team_key, self.name)


    @classmethod
    def load_teams(cls, league_id):
        """
        Load teams from yahoo into db
        """
        print 'Loading teams...'
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


class Roster(models.Model):
    """
    Player membership model
    """
    team = models.ForeignKey(Team)
    player = models.ForeignKey(Player)
    week = models.SmallIntegerField()
    position = models.CharField(max_length=4)

    query_manager = QueryManager()

    def __unicode__(self):
        return '%s: %s week %s %s' % (self.team.__unicode__(), self.player.__unicode__(), str(self.week), self.position)

    @classmethod
    def load_rosters(cls, league_id, week):
        """
        Load the rosters for the week
        """
        print 'Loading rosters for league %s week %s' % (league_id, str(week))
        week_list = cls.objects.filter(week=week)
        teams = Team.objects.filter(league__league_key=league_id)
        team_list = SortedDict([(team.team_key, team) for team in teams])
        query_str = "select team_key, roster.players.player.player_key, roster.players.player.selected_position.position from fantasysports.teams.roster where team_key in (value) and week='%s'" % week
        for result in cls.query_manager.batch_query(query_str, team_list.keys()):
            team_key = result.get('team_key')
            team = team_list.get(team_key)
            print 'Loading team %s week %s' % (team.name, str(week))
            team_rosters = week_list.filter(team=team)
            team_rosters.delete()
            player_list = result.get('roster').get('players').get('player')
            for player in player_list:
                player_obj = Player.get_player(player.get('player_key'))
                position = player.get('selected_position').get('position')
                roster_item = cls.objects.create(team=team, week=week, player=player_obj, position=position)
                roster_item.save()
                print '%s: %s' % (player_obj, position)

    class Meta:
        """ Metadata class for Roster """
        app_label = 'analyze'
