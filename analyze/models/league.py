"""
League module
"""
from utils.query import QueryManager
from django.db import models

class League(models.Model):
    """
    League data model, contains fantasy league info
    """
    league_key = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=32)
    start_week = models.SmallIntegerField()
    end_week = models.SmallIntegerField()
    current_week = models.SmallIntegerField()

    query_manager = QueryManager()
