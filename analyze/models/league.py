"""
League module
"""
from utils.query import QueryManager
from django.db import models
from django.db.models import Q
from django.utils.datastructures import SortedDict


YEAR_KEYS = SortedDict([
    ('257', '2011'),
    ('273', '2012'),
    ])


TEAM_KEYS = {
        'ARI': 'Arizona Cardinals',
        'ATL': 'Atlanta Falcons',
        'BAL': 'Baltimore Ravens',
        'BUF': 'Buffalo Bills',
        'CAR': 'Carolina Panthers',
        'CHI': 'Chicago Bears',
        'CIN': 'Cincinnati Bengals',
        'CLE': 'Cleveland Browns',
        'DAL': 'Dallas Cowboys',
        'DEN': 'Denver Broncos',
        'DET': 'Detroit Lions',
        'GBP': 'Green Bay Packers',
        'HOU': 'Houston Texans',
        'IND': 'Indianapolis Colts',
        'JAC': 'Jacksonville Jaguars',
        'KCC': 'Kansas City Chiefs',
        'MIA': 'Miami Dolphins',
        'MIN': 'Minnesota Vikings',
        'NOS': 'New Orleans Saints',
        'NEP': 'New England Patriots',
        'NYG': 'New York Giants',
        'NYJ': 'New York Jets',
        'OAK': 'Oakland Raiders',
        'PHI': 'Philadelphia Eagles',
        'PIT': 'Pittsburgh Steelers',
        'SEA': 'Seattle Seahawks',
        'SDC': 'San Diego Chargers',
        'SFO': 'San Francisco 49ers',
        'STL': 'St. Louis Rams',
        'TBB': 'Tampa Bay Buccaneers',
        'TEN': 'Tennessee Titans',
        'WAS': 'Washington Redskins',
        }


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


class NFLMatchup(models.Model):
    """
    Data models containing the NFL matchup information
    """
    away_team = models.CharField(max_length=32)
    home_team = models.CharField(max_length=32)
    away_score = models.SmallIntegerField(null=True)
    home_score = models.SmallIntegerField(null=True)
    week = models.SmallIntegerField()
    year = models.SmallIntegerField()

    @classmethod
    def find_team(cls, team, **kwargs):
        """
        Locate a matchup containing a specific team

        @param team: Team name to search for, will query away and home team
        @return: QuerySet object limited to teams where it was home or away
        """
        return cls.objects.filter(Q(home_team=team) | Q(away_team=team))

    @classmethod
    def load_matchups(cls, year, week, **kwargs):
        """
        Load NFL matchups into db from web
        """
        from xml.etree import ElementTree
        import urllib2

        req_str = 'http://football.myfantasyleague.com/%s/export?TYPE=nflSchedule&W=%s' % (str(year), str(week))
        req = urllib2.Request(req_str)
        response = urllib2.urlopen(req)
        data = response.read()

        root = ElementTree.fromstring(data)
        cls.objects.filter(year=year, week=week).delete()
        for match in root:
            matchup = cls()
            matchup.week = week
            matchup.year = year
            for team in match:
                attr = team.attrib
                score = attr.get('score')
                team = TEAM_KEYS.get(attr.get('id'))
                if score == '':
                    score = None
                if int(attr.get('isHome')):
                    matchup.home_team = team
                    matchup.home_score = score
                else:
                    matchup.away_team = team
                    matchup.away_score = score
            matchup.save()

    class Meta:
        """ Metadata class for NFLMatchup """
        app_label = 'analyze'
