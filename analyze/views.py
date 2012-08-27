"""
View Module
"""
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.utils.datastructures import SortedDict
from analyze.models.player import Player


def template_factory(base_class, name):
    class BaseView(base_class):
        """
        Provide the base site context
        """
        nav_list = SortedDict([
            ('home', {'name': 'Home', 'ref': '/', 'active': False}),
            ('players', {'name': 'NFL Players', 'ref': '/players', 'active': False}),
            #('managers', {'name': 'Fantasy Managers', 'ref': '#', 'active': False}),
            ])

        def get_context_data(self, **kwargs):
            """
            Give base site context
            """
            context = super(BaseView, self).get_context_data(**kwargs)
            link_list = []
            for key, value in self.__class__.nav_list.items():
                if key == name:
                    value['active'] = True
                link_list.append(value)
            context['nav_list'] = link_list
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


class PlayerList(PListView):
    """
    View class for player list
    """
    model = Player
    template_name = 'list.html'
    page_title = 'Players Home'
