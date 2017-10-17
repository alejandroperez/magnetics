#!/bin/python
# coding=utf-8
import logging
logger = logging.getLogger()
import collections
import math
import matplotlib.pyplot as plt
import numpy
import winding

def fit(core, wire, turns, wrap_thickness = 0.0):
    rt = turns
    stack = winding.Stack()
    radius = core.inner_radius - wrap_thickness
    h = core.h + 2.0 * wrap_thickness
    l = core.outer_radius - core.inner_radius + 2.0 * wrap_thickness
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
        stack.add_layer(winding.Layer(turns= t, wire_length= (circ * t), wire= wire))
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


def optimize_wire(core, turns_primary, turns_secondary, insulation_thickness):
    ratio = turns_primary / turns_secondary
    logger.debug('Ratio is %f' % ratio)
    target_empty_area = math.pi * (core.inner_radius ** 2) / 2.0
    wire_primary_index = 39

    while wire_primary_index >= 6:
        wire_primary = winding.wire_list[wire_primary_index]
        logger.debug('Trying winding primary with %s ...' % wire_primary.name)
        logger.debug(wire_primary)
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
                wire_secondary = winding.wire_list[wire_secondary_index]
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

