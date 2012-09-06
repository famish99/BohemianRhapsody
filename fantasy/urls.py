from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
import analyze.views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', analyze.views.LeagueList.as_view()),
    url(r'^(?P<league_key>[\w.]+)/$', analyze.views.PlayerList.as_view()),
    url(r'^(?P<league_key>[\w.]+)/players/$', analyze.views.PlayerList.as_view()),
    url(r'^(?P<league_key>[\w.]+)/player/(?P<pk>\d+)/$', analyze.views.PlayerDetail.as_view()),
    url(r'^(?P<league_key>[\w.]+)/teams/$', analyze.views.TeamList.as_view()),
    url(r'^(?P<league_key>[\w.]+)/team/(?P<pk>\d+)/$', analyze.views.TeamDetail.as_view()),
    # url(r'^fantasy/', include('fantasy.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
