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
from urllib import urlencode
import copy


def template_factory(base_class, name):
    class BaseView(base_class):
        """
        Provide the base site context
        """
        nav_list = SortedDict([
            #('home', {'name': 'Home', 'ref': '/', 'active': False}),
            ('players', {'name': 'NFL Players', 'ref': 'players/', 'active': False}),
            #('managers', {'name': 'Fantasy Managers', 'ref': '#', 'active': False}),
            ])

        year_keys = SortedDict([
            ('2011', '257'),
            ('2012', '273'),
            ])

        script_list = []

        def get_context_data(self, **kwargs):
            """
            Give base site context
            """
            context = super(BaseView, self).get_context_data(**kwargs)
            link_list = []
            for key, value in self.__class__.nav_list.items():
                add_value = value.copy()
                add_value['ref'] = "/%s/%s" % (self.kwargs.get('year'), value['ref'])
                if key == name:
                    add_value['active'] = True
                else:
                    add_value['active'] = False
                link_list.append(add_value)
            context['nav_list'] = link_list
            context['year'] = self.kwargs.get('year')
            context['page_title'] = self.__class__.page_title
            context['script_list'] = self.__class__.script_list
            return context

    return BaseView


HTemplateView = template_factory(TemplateView, 'home')
PListView = template_factory(ListView, 'players')
PDetailView = template_factory(DetailView, 'players')

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
        for stat in stat_list:
            stat_week = []
            stat_week.append(stat.week_num)
            for key, value in columns:
                stat_week.append(stat.stat_data[key])
            stat_week.append(stat.total_points())
            context['stat_list'].append(stat_week)
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

    def get_queryset(self):
        year_key = self.__class__.year_keys.get(self.kwargs.get('year'), '257')
        queryset = Player.objects.filter(player_key__contains=year_key)
        queryset = queryset.filter(season_points__gt=0)
        position = self.request.GET.get('position', 'all')
        name = self.request.GET.get('name')
        sort = self.request.GET.get('sort')
        if position in ('QB', 'WR', 'RB', 'TE', 'K'):
            queryset = queryset.filter(position__contains=position)
        if name:
            queryset = queryset.filter(
                    Q(first_name__icontains=name) |
                    Q(last_name__icontains=name)
                    )
        # Test out sorting by method for later calculation purposes
        # and advanced sorting purposes
        if sort == "test":
            queryset = list(queryset)
            queryset.sort(key=lambda x: x._season_points(), reverse=True)
        else:
            queryset = queryset.order_by('-season_points')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(PlayerList, self).get_context_data(**kwargs)
        page_vars = {}
        positions = copy.deepcopy(self.__class__.positions)
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
        return context
