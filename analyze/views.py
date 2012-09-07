"""
View Module
"""
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.utils.datastructures import SortedDict
from django.db.models import Q
from analyze.models.stats import STATS
from analyze.models.player import Player
from analyze.models.league import League, YEAR_KEYS
from analyze.models.team import Team
from urllib import urlencode
import copy
import numpypy


def template_factory(base_class, name):
    class BaseView(base_class):
        """
        Provide the base site context
        """
        nav_list = SortedDict([
            #('home', {'name': 'Home', 'ref': '/', 'active': False}),
            ('teams', {'name': 'Fantasy Teams', 'ref': 'teams/', 'active': False}),
            ('players', {'name': 'NFL Players', 'ref': 'players/', 'active': False}),
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
    template_name = 'player_detail.html'
    page_title = 'Player Detail'
    model = Player


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
        stat_keys = filter(lambda x: x not in ['57'], stat_list[0].stat_data.keys())
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
                    numpypy.mean(column_lists[key]),
                    numpypy.std(column_lists[key]),
                    )
            avg_stats.append(avg_str)
        avg_stats.append(player.mean_points())
        context['stat_list'].append(avg_stats)
        points = player.get_points()
        context['stat_rows'] = [
                ("Total Points", player._season_points()),
                ("Mean", player.mean_points()),
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
        league_prefix, league_id = league_key.split('.l.')
        return league_prefix

    def get_queryset(self):
        year_key = self.get_year_key()
        queryset = Player.objects.filter(player_key__contains=year_key)
        queryset = queryset.filter(season_points__gt=0)
        position = self.request.GET.get('position', 'all')
        name = self.request.GET.get('name')
        sort = self.request.GET.get('sort', 'total')
        min_std = int(self.request.GET.get('min_std', 1))
        min_mean = int(self.request.GET.get('min_mean', 1))
        reverse = bool(self.request.GET.get('reverse'))
        if position in ('QB', 'WR', 'RB', 'TE', 'K'):
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
