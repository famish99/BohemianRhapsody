"""
View Module
"""
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.utils.datastructures import SortedDict
from analyze.models.player import Player
from urllib import urlencode


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

        def get_context_data(self, **kwargs):
            """
            Give base site context
            """
            context = super(BaseView, self).get_context_data(**kwargs)
            link_list = []
            for key, value in self.__class__.nav_list.items():
                add_value = {}
                add_value['ref'] = "/%s/%s" % (self.kwargs.get('year'), value['ref'])
                if key == name:
                    add_value['active'] = True
                else:
                    add_value['active'] = False
                add_value['name'] = value['name']
                link_list.append(add_value)
            context['nav_list'] = link_list
            context['year'] = self.kwargs.get('year')
            context['page_title'] = self.__class__.page_title
            return context

    return BaseView


HTemplateView = template_factory(TemplateView, 'home')
PListView = template_factory(ListView, 'players')

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


class PlayerList(PListView):
    """
    View class for player list
    """
    paginate_by = 30
    template_name = 'player_list.html'
    page_title = 'Players Home'

    def get_queryset(self):
        year_key = self.__class__.year_keys.get(self.kwargs.get('year'), '257')
        queryset = Player.objects.filter(player_key__contains=year_key)
        queryset = queryset.filter(season_points__gt=0)
        position = self.request.GET.get('position')
        if position:
            queryset = queryset.filter(position__contains=position)
        queryset = queryset.order_by('-season_points')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(PlayerList, self).get_context_data(**kwargs)
        page_vars = {}
        position = self.request.GET.get('position')
        if position:
            page_vars['position'] = position
        page_obj = context['page_obj']
        if page_obj.has_previous():
            page_vars['page'] = page_obj.previous_page_number()
            context['prev_page'] = urlencode(page_vars)
        if page_obj.has_next():
            page_vars['page'] = page_obj.next_page_number()
            context['next_page'] = urlencode(page_vars)
        return context
