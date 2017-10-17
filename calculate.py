#!/bin/python
# coding=utf-8
import logging
logger = logging.getLogger()
import collections
import math
import matplotlib.pyplot as plt
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
            return math.pi * self.h * ( (self.outer_radius ** 2)
                    - (self.inner_radius ** 2) )

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

def fit(core, wire, turns, wrap_thickness = 0.0):
    rt = turns
    stack = Stack()
    radius = core.inner_radius - wrap_thickness
    h = core.h + 2 * wrap_thickness
    l = core.outer_radius - core.inner_radius + 2 * wrap_thickness
    bloated_radius = wire.radius() * 1.12
    while rt > 0:
        radius = radius - bloated_radius
        h = h + bloated_radius * 2
        l = l + bloated_radius * 2
        if radius <= 0:
            raise 'wire is too big'
        length = math.pi * 2 * radius
        t = int(length / (bloated_radius * 2))
        t = min(t, rt)
        if t == 0:
            raise('cannot fit a single turn')
        rt = rt - t
        circ = 2.0 * h + 2.0 * l
        stack.add_layer(Layer(turns= t, wire_length= (circ * t), wire= wire))
        radius = radius - bloated_radius #yes, a second time.
        h = h + bloated_radius * 2
        l = l + bloated_radius * 2
    return stack

def calculate_power(stackp, stacks, voltage_primary):
    turn_ratio = stackp.turns() / stacks.turns()
    logger.info('Turn ratio: %s' % turn_ratio)
    rp = stackp.resistance()
    rs = stacks.resistance()
    current_secondary = numpy.arange(0.1, 100, 1)
    voltage_secondary = []
    dissipated_power = []
    for cs in current_secondary:
        ps = rs * (cs ** 2 )
        cp = cs / turn_ratio
        pp = rp * (cp ** 2)
        deltaVs = cs * rs
        deltaVp = cp * rp
        vs = ((voltage_primary - deltaVp) / turn_ratio) - deltaVs
        voltage_secondary.append(vs)
        dis_pow = pp + ps
        dissipated_power.append(dis_pow)
    plot1 = plt.plot(current_secondary, dissipated_power, label="diss. power")
    plot2 = plt.plot(current_secondary, voltage_secondary, label='voltage')
    plt.legend(['diss. power', 'voltage'])
    plt.show()


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

def optimize_wire(core, turns_primary, turns_secondary, insulation_thickness):
    ratio = turns_primary / turns_secondary
    logger.debug('Ratio is %f' % ratio)
    target_empty_area = math.pi * (core.inner_radius ** 2) / 2.0
    wire_primary_index = 39

    while wire_primary_index >= 6:
        wire_primary = wire_list[wire_primary_index]
        logger.debug('Trying winding primary with %s ...' % wire_primary.name)
        wire_primary_index -= 1
        try:
            stack_primary = fit(core, wire_primary, turns_primary,
                    insulation_thickness * 2) #the first layer has double insulation
            clear_radius = core.inner_radius - stack_primary.thickness()
            clear_area = math.pi * (clear_radius ** 2)
            if clear_area < target_empty_area:
                logger.debug('Primary alone does not leave enough clear space.')
                break
            wire_secondary_index = wire_primary_index
            while wire_secondary_index >= 0:
                wire_secondary = wire_list[wire_secondary_index]
                logger.debug('\tTrying winding secondary with %s ...'
                        % wire_secondary.name)
                wire_secondary_index -= 1
                try:
                    stack_secondary = fit(core, wire_secondary, turns_secondary, stack_primary.thickness()
                            + insulation_thickness) 
                    clear_radius = core.inner_radius - stack_primary.thickness() - stack_secondary.thickness()
                    clear_area = math.pi * (clear_radius ** 2)
                    if clear_area < target_empty_area:
                        logger.debug('\tBoth stacks do not leave enough clear area.')
                        break
                    else:
                        best_primary = stack_primary
                        best_secondary = stack_secondary
                except:
                    logger.debug('\tSecondary does not phisically fit!')
                    break
        except:
            logger.debug('Primary alone does not fit!')
            break
    return (best_primary, best_secondary)

def calculate_wasted_power(primary, secondary, sec_current):
    rs = secondary.resistance()
    rp = primary.resistance()
    ratio = primary.turns() / secondary.turns()
    wasted = (sec_current ** 2) * rs
    wasted += ((sec_current / ratio) ** 2) * rp
    return wasted

def calculate_max_current(primary, secondary, max_waste_power):
    for current in numpy.arange(0.1, 100, 0.05):
        w = calculate_wasted_power(primary, secondary, current)
        if w <= max_waste_power:
            best_current = current
        else:
            break
    return best_current

#----------------------------------------------
#Variables
core = Toroid(height=51.0 / 1000, inner_radius=70.0 / 1000 /2,
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


(p, s) = optimize_wire(core, turns_primary, turns_secondary, insulation_thickness)
print 'Primary is:'
print p
print p.layers[0]
print 'Secondary is:'
print s
sc = calculate_max_current(p, s, max_wasted_power)
print 'Maximum secondary current is: %.1f a' % sc
voltage_drop = sc * s.resistance()

print 'Voltage drop at full load: %.2f v (%.1f %%)' % (voltage_drop, voltage_drop * 100/ voltage_secondary)
print 'Input power: %.1f w' % (voltage_secondary * sc + max_wasted_power / 2)
