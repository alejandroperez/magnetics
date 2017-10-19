#!/bin/python
# coding=utf-8
import logging
logging.basicConfig()
logger = logging.getLogger()
#logger.setLevel(logging.INFO)
import collections
import numpy
import winding
import core
import calculate
import math

#Variables
core = core.Toroid(height=51.0 / 1000, inner_radius=70.0 / 1000 /2,
        outer_radius= 108.0 /1000 / 2)
frequency = 60.0
voltage_primary = 120.0
voltage_secondary = 90.0
magnetic_field = 1.2 #teslas
max_wasted_power = 15.0 #watts



#----------------------------------------------
#Calculation
insulation_thickness = 0.25/1000 #0.125mm mylar, 50% overlap
ratio = voltage_primary / voltage_secondary
turns_primary = voltage_primary / 4.44 / core.area() / frequency/ magnetic_field
turns_secondary = turns_primary / ratio
print 'Core geometry: %s, core area: %.5f m^2' % (core, core.area())
print "Electrical input is %.1f volts at %.1f hertz" % (voltage_primary, frequency)


(p, s) = calculate.optimize_wire(core, turns_primary, turns_secondary, insulation_thickness)
print 'Primary is:'
print p
print p.layers[0]
print 'Secondary is:'
print s
sc = calculate.calculate_max_current(p, s, max_wasted_power)
print 'Maximum secondary current is: %.1f a' % sc
voltage_drop = sc * s.resistance()

print 'Voltage drop at full load: %.2f v (%.1f %%)' % (voltage_drop, voltage_drop * 100/ voltage_secondary)
print 'Input power: %.1f w' % (voltage_secondary * sc + max_wasted_power / 2)
u0 = math.pi * 4e-7
L = u0 * 42400.0 * (turns_primary ** 2) * core.h / (2 * math.pi) * math.log(core.outer_radius / core.inner_radius, math.e)
Xl = math.pi * 2 * L * frequency
print 'Inductance is: %f H. Reactance is: (%.2f, %.2f i)'% (L, p.resistance(), Xl)
print 'Magnetizing current is: %.3f' % (voltage_primary / math.sqrt ((Xl ** 2) + (p.resistance() ** 2)))
