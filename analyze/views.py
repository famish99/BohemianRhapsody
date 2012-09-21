"""
View Module
"""
from analyze.models.stats import STATS, PlayerStats
from analyze.models.player import Player
from analyze.models.league import League, NFLMatchup, YEAR_KEYS
from analyze.models.team import Team
from utils.mathutils import MathUtils
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.utils.datastructures import SortedDict
from django.db.models import Q
from urllib import urlencode
import copy


def template_factory(base_class, name):
    class BaseView(base_class):
        """
        Provide the base site context
        """
        nav_list = SortedDict([
            #('home', {'name': 'Home', 'ref': '/', 'active': False}),
            ('teams', {'name': 'Fantasy Teams', 'ref': 'teams/', 'active': False}),
            ('players', {'name': 'NFL Players', 'ref': 'players/', 'active': False}),
            ('nflteams', {'name': 'NFL Teams', 'ref': 'nflteams/', 'active': False}),
            ])

        year_keys = YEAR_KEYS

        script_list = []

        def get_context_data(self, **kwargs):
            """
            Give base site context
            """
            context = super(BaseView, self).get_context_data(**kwargs)
            link_list = []
            for key, value in self.__class__.nav_list.items():
                add_value = value.copy()
                add_value['ref'] = "/%s/%s" % (self.kwargs.get('league_key'), value['ref'])
                if key == name:
                    add_value['active'] = True
                else:
                    add_value['active'] = False
                link_list.append(add_value)
            context['nav_list'] = link_list
            context['league_key'] = self.kwargs.get('league_key')
            context['page_title'] = self.__class__.page_title
            context['script_list'] = self.__class__.script_list
            return context

    return BaseView


HTemplateView = template_factory(TemplateView, 'home')
HListView = template_factory(ListView, 'home')
PListView = template_factory(ListView, 'players')
PDetailView = template_factory(DetailView, 'players')
TListView = template_factory(ListView, 'teams')
TDetailView = template_factory(DetailView, 'teams')
NListView = template_factory(ListView, 'nflteams')
NDetailView = template_factory(DetailView, 'nflteams')


class HomeView(HTemplateView):
    """
    View class for home page
    """
    template_name = 'home.html'
    page_title = 'Home'
    nav_list = {}

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['year_list'] = self.__class__.year_keys.keys()
        return context


class LeagueList(HListView):
    """
    View class for the league list
    """
    template_name = 'league_list.html'
    page_title = 'League Selection'
    model = League

    def get_context_data(self, **kwargs):
        context = super(LeagueList, self).get_context_data(**kwargs)
        context['nav_list'] = None
        return context


class NFLTeamList(NListView):
    """
    List teams in the league
    """
    template_name = 'nflteam_list.html'
    page_title = 'NFL Matchups'

    def get_queryset(self, **kwargs):
        league_key = self.kwargs.get('league_key')
        year = self.__class__.year_keys.get(league_key.split('.l.', 1)[0])
        week = self.request.GET.get('week', League.objects.get(league_key=league_key).current_week)
        queryset = NFLMatchup.objects.filter(year=year)
        queryset = queryset.filter(week=week)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(NFLTeamList, self).get_context_data(**kwargs)
        league = League.objects.get(league_key=self.kwargs.get('league_key'))
        context['league'] = league
        context['weeks'] = range(league.start_week, league.end_week + 1)
        return context


class NFLTeamDetail(NDetailView):
    """
    View class for individual team detail
    """
    template_name = 'team_detail.html'
    page_title = 'Team Detail'
    model = Team


class TeamList(TListView):
    """
    List teams in the league
    """
    template_name = 'team_list.html'
    page_title = 'Teams'

    def get_queryset(self, **kwargs):
        queryset = Team.objects.filter(league__league_key=self.kwargs.get('league_key'))
        queryset = queryset.order_by('rank')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(TeamList, self).get_context_data(**kwargs)
        context['league'] = League.objects.get(league_key=self.kwargs.get('league_key'))
        return context


class TeamDetail(TDetailView):
    """
    View class for individual team detail
    """
    template_name = 'team_detail.html'
    page_title = 'Team Detail'
    model = Team

    position_list = [
            'QB',
            'WR',
            'WR',
            'WR',
            'RB',
            'RB',
            'TE',
            'K',
            'DEF',
            'BN',
            'BN',
            'BN',
            'BN',
            'BN',
            'BN',
            ]

    unique_list = [
            'QB',
            'WR',
            'RB',
            'TE',
            'K',
            'DEF',
            'BN',
            ]

    def get_context_data(self, **kwargs):
        context = super(TeamDetail, self).get_context_data(**kwargs)
        team = context['object']
        weeks = range(1, League.objects.get(league_key=self.kwargs.get('league_key')).current_week + 1)
        context['stat_headers'] = ['Week #'] + self.__class__.position_list
        context['stat_list'] = []
        for week in weeks:
            lineup = team.players.filter(roster__week=week)
            player_list = [ player
                    for position in self.__class__.unique_list
                    for player in team.players.filter(Q(roster__position=position), Q(roster__week=week))
                    ]
            stat_week = [ {'week': week} ] + [ {'player': player} for player in player_list ]
            points = MathUtils.sum([ roster.player.get_weekly_points(week) for roster in team.roster.filter(week=week).exclude(position='BN')])
            lower_stat = [ {'points': 'Total: %.2f' % points} ] + [ {'points': '%.2f' % player.get_weekly_points(week)} for player in player_list ]
            context['stat_list'].append(stat_week)
            context['stat_list'].append(lower_stat)

        return context


class PlayerDetail(PDetailView):
    """
    View class for individual player detail
    """
    template_name = 'player_detail.html'
    page_title = 'Player Detail'
    model = Player

    def get_context_data(self, **kwargs):
        context = super(PlayerDetail, self).get_context_data(**kwargs)
        player = context['object']
        stat_list = player.stats.all()
        stat_keys = filter(lambda x: x not in ['50', '51', '52', '53', '54', '55', '56', '57'], stat_list[0].stat_data.keys())
        columns = filter(lambda x: x[0] in stat_keys, STATS.items())
        stat_headers = [ stat_item[1][0] for stat_item in columns ]
        stat_headers.insert(0, 'Week #')
        stat_headers.append('Points')
        context['stat_headers'] = stat_headers
        context['stat_list'] = []
        column_lists = { key: [] for key, value in columns }
        for stat in stat_list:
            if int(player.bye_week) == stat.week_num:
                continue
            total_points = stat.total_points()
            stat_week = []
            stat_week.append(stat.week_num)
            for key, value in columns:
                stat_week.append(stat.stat_data[key])
                column_lists[key].append(stat.stat_data[key])
            stat_week.append(total_points)
            context['stat_list'].append(stat_week)
        avg_stats = ['Avg']
        for key, value in columns:
            avg_str = "%.1f &plusmn; %.1f" % (
                    MathUtils.mean(column_lists[key]),
                    MathUtils.std(column_lists[key]),
                    )
            avg_stats.append(avg_str)
        avg_stats.append(player.mean_points())
        context['stat_list'].append(avg_stats)
        points = player.get_points()
        context['stat_rows'] = [
                ("Total Points", player._season_points()),
                ("Geometric Mean", player.gmean_points()),
                ("Arithmetic Mean", player.mean_points()),
                ("Std Dev", player.std_dev_points()),
                ("Median", player.median_points()),
                ("Floor", player.floor_points()),
                ("Ceiling", player.ceiling_points()),
                ("Games Played", player.games_played()),
                ("Risk Factor", '%.2f%%' % player.risk_factor()),
                ]
        context['page_title'] = '%s %s Detail' % (player.first_name, player.last_name)
        return context


class PlayerList(PListView):
    """
    View class for player list
    """
    paginate_by = 25
    template_name = 'list.html'
    page_title = 'Players Home'

    script_list = [
            '/static/jquery.js',
            '/static/common.js',
            '/static/player_list.js',
            ]

    positions = SortedDict([
        ('all', {'label': 'All', 'selected': False}),
        ('QB' , {'label': 'QB' , 'selected': False}),
        ('WR' , {'label': 'WR' , 'selected': False}),
        ('RB' , {'label': 'RB' , 'selected': False}),
        ('TE' , {'label': 'TE' , 'selected': False}),
        ('K'  , {'label': 'K'  , 'selected': False}),
        ('DEF', {'label': 'DEF', 'selected': False}),
        ])

    sort_methods = SortedDict([
        ('total',  {'label': 'Total',       'selected': False, 'method': lambda x: x.season_points, 'reverse': lambda x: not x}),
        ('avg',    {'label': 'Mean',        'selected': False, 'method': lambda x: x.mean_points(), 'reverse': lambda x: not x}),
        ('std',    {'label': 'Std Dev',     'selected': False, 'method': lambda x: x.std_dev_points(), 'reverse': lambda x: not x}),
        ('cst',    {'label': 'Consistency', 'selected': False, 'method': lambda x: x.std_dev_points()/x.mean_points()/x.games_played(), 'reverse': lambda x: x}),
        ('risk',   {'label': 'Risk',        'selected': False, 'method': lambda x: x.risk_factor(), 'reverse': lambda x: x}),
        ('upside', {'label': 'Upside',      'selected': False, 'method': lambda x: x.std_dev_points()*x.games_played(), 'reverse': lambda x: not x}),
        ('flr',    {'label': 'Floor',       'selected': False, 'method': lambda x: x.floor_points(), 'reverse': lambda x: not x}),
        ('med',    {'label': 'Median',      'selected': False, 'method': lambda x: x.median_points(), 'reverse': lambda x: not x}),
        ('cei',    {'label': 'Ceiling',     'selected': False, 'method': lambda x: x.ceiling_points(), 'reverse': lambda x: not x}),
        ])

    def get_year_key(self):
        """
        Return the league key prefix
        """
        league_key = self.kwargs.get('league_key')
        league_prefix, league_id = league_key.split('.l.', 1)
        return league_prefix

    def get_queryset(self):
        year_key = self.get_year_key()
        queryset = Player.objects.filter(player_key__contains='%s.p.' % year_key)
        queryset = queryset.filter(season_points__gt=0)
        position = self.request.GET.get('position', 'all')
        name = self.request.GET.get('name')
        sort = self.request.GET.get('sort', 'total')
        min_std = int(self.request.GET.get('min_std', 1))
        min_mean = int(self.request.GET.get('min_mean', 1))
        reverse = bool(self.request.GET.get('reverse'))
        if position in ('QB', 'WR', 'RB', 'TE', 'K', 'DEF'):
            queryset = queryset.filter(position__contains=position)
        if name:
            queryset = queryset.filter(
                    Q(first_name__icontains=name) |
                    Q(last_name__icontains=name)
                    )
        if sort == 'total':
            if reverse:
                queryset = queryset.order_by('season_points')
            else:
                queryset = queryset.order_by('-season_points')
        else:
            queryset = list(queryset)
            queryset = filter(lambda x: x.std_dev_points() > min_std, queryset)
            queryset = filter(lambda x: x.mean_points() > min_mean, queryset)
            sort_method = self.__class__.sort_methods.get(sort)
            queryset.sort(key=sort_method['method'], reverse=sort_method['reverse'](reverse))
        return queryset

    def get_context_data(self, **kwargs):
        context = super(PlayerList, self).get_context_data(**kwargs)
        page_vars = {}
        positions = copy.deepcopy(self.__class__.positions)
        sort_methods = copy.deepcopy(self.__class__.sort_methods)
        min_std = self.request.GET.get('min_std')
        if min_std:
            page_vars['min_std'] = min_std
        min_mean = self.request.GET.get('min_mean')
        if min_mean:
            page_vars['min_mean'] = min_mean
        sort = self.request.GET.get('sort')
        if sort:
            page_vars['sort'] = sort
            sort_methods[sort]['selected'] = True
        reverse = bool(self.request.GET.get('reverse'))
        if reverse:
            page_vars['reverse'] = reverse
            context['reverse'] = reverse
        name = self.request.GET.get('name')
        if name:
            page_vars['name'] = name
            context['player_name'] = name
        position = self.request.GET.get('position')
        if position:
            page_vars['position'] = position
            positions[position]['selected'] = True
        page_obj = context['page_obj']
        if page_obj.has_previous():
            page_vars['page'] = page_obj.previous_page_number()
            context['prev_page'] = urlencode(page_vars)
        if page_obj.has_next():
            page_vars['page'] = page_obj.next_page_number()
            context['next_page'] = urlencode(page_vars)
        context['search_position'] = positions.items()
        context['sort_methods'] = sort_methods.items()
        return context
