"""
Team management
"""
from utils.query import QueryManager
from django.db import models

class Team(models.Model):
    """
    Fantasy team model
    """
    team_key = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=32)
    manager_name = models.CharField(max_length=32)
