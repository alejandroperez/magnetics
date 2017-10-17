#!/bin/python
# coding=utf-8
import logging
logger = logging.getLogger()
import collections
import math
import matplotlib.pyplot as plt
import numpy

#Definitions

class Wire:
    def __init__(self, copper_diameter, insulation_thickness=0.000017, name=''):
        self.copper_diameter = copper_diameter
        self.insulation_thickness = insulation_thickness
        self.name = name
    def diameter(self):
        return 2.0 * self.insulation_thickness + self.copper_diameter
    def radius(self):
        return self.diameter() / 2
    def __str__(self):
        return 'Wire:%s(diameter=%f)' % (self.name, self.diameter())

class Layer:
    def __init__(self, turns, wire_length, wire):
        self.turns = turns
        self.wire_length = wire_length
        self.wire = wire

    def __str__(self):
        return 'Layer(turns= %f, wire_length= %f m, resistance= %f Ω)' % (self.turns, self.wire_length, self.resistance())

    def resistance(self):
        return 1.68e-8 * self.wire_length / (math.pi * (self.wire.radius() **
            2))

class Stack(list):
    def __init__(self):
        self.layers = []
    def add_layer(self, layer):
        self.layers.append(layer)
    def resistance(self):
        resistance = 0.0
        for l in self.layers:
            resistance = resistance + l.resistance()
        return resistance
    def turns(self):
        t = 0.0
        for l in self.layers:
            t = t + l.turns
        return t
    def wire_length(self):
        wl = 0.0
        for l in self.layers:
            wl = wl + l.wire_length
        return wl
    def thickness(self):
        th = 0.0
        for l in self.layers:
            th += l.wire.diameter()
            th += 0.0006 #0.6 mm for inter winding insulation
        return th
    def __str__(self):
        cable = self.layers[0].wire.name
        retval = 'Stack(wire: %s, resistance= %f Ω, turns= %f, wire length= %f m, layers=[' % (cable, self.resistance(), self.turns(), self.wire_length())
        for l in self.layers:
            retval += '%.1f, ' % l.turns
        retval += ']'
        return retval

#----------------------------------------------
#create the full awg series of cables

wires = {}
wire_list = []
for n in range(40):
    exponent = (2.1104 - (0.11594 * n))
    diameter = math.pow(math.e, exponent) / 1000 #in meters, from mm
    name = 'awg%s' % n
    wire = Wire(diameter, name=name)
    wires[name] = wire
    wire_list.append(wire)

