#!/bin/python
# coding=utf-8
import logging
logger = logging.getLogger()
import math
import numpy

#Definitions
class Toroid:
    def __init__(self, height, inner_radius, outer_radius):
        self.h = height
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius

    def area(self):
        return self.h * (self.outer_radius - self.inner_radius)

    def __str__(self):
        return "Toroid(heigt=%f, inner_radius=%f, outer_radius=%f)" %(self.h,
                self.inner_radius, self.outer_radius)
    def volume(self):
        return math.pi * self.h * ( (self.outer_radius ** 2) - (self.inner_radius ** 2) )
