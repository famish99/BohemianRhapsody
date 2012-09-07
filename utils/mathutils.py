"""
Numpy abstraction layer. This allows the user to switch from a PyPy deployment
to a CPython deployment without having to search for all the numpy calls
"""

import numpypy
import math

class MathUtils:
    """
    numpy/numpypy wrapper class
    """

    default_round = 2

    @classmethod
    def mean(cls, input_list, **kwargs):
        """
        Return mean
        """
        return round(numpypy.mean(input_list, **kwargs), cls.default_round)

    @classmethod
    def gmean(cls, input_list, **kwargs):
        """
        Return mean
        """
        product = reduce(lambda x, y: x*y, input_list)
        return round(math.pow(product, 1.0/len(input_list)), cls.default_round)

    @classmethod
    def sum(cls, input_list, **kwargs):
        """
        Calculate sum
        """
        return round(numpypy.sum(input_list, **kwargs), cls.default_round)

    @classmethod
    def median(cls, input_list, **kwargs):
        """
        Calculate median
        """
        if len(input_list) % 2:
            return round(sorted(input_list)[len(input_list)/2], cls.default_round)
        else:
            mid = len(input_list) / 2
            return round(numpypy.mean(sorted(input_list)[(mid - 1):(mid + 1)]), cls.default_round)

    @classmethod
    def std(cls, input_list, **kwargs):
        """
        Calculate variance
        """
        return round(numpypy.std(input_list, **kwargs), cls.default_round)

    @classmethod
    def min(cls, input_list, **kwargs):
        """
        Calculate floor
        """
        return round(numpypy.min(input_list, **kwargs), cls.default_round)

    @classmethod
    def max(cls, input_list, **kwargs):
        """
        Calculate ceiling
        """
        return round(numpypy.max(input_list, **kwargs), cls.default_round)

    @classmethod
    def normalize(cls, input_list, **kwargs):
        """
        Normalize list elements
        """
        list_norm = 1.0/numpypy.max(input_list, **kwargs)
        if kwargs.get('round', True):
            output_list = map(lambda x: round(x*list_norm, cls.default_round), input_list)
        else:
            output_list = map(lambda x: x*list_norm, input_list)
        return output_list
