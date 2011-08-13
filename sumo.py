#!/usr/bin/env python

import pygame
from pygame.locals import *
from pygame.color import *
import pymunk as pm
import math, sys, random
X,Y,Z = 0,1,2 # Easy indexing

class Score(object):
    def __init__(self):
        self.i = 0

    def inc(self):
        self.i += 1

    def __str__(self):
        return str(self.i)

LEFT_SCORE = Score()
RIGHT_SCORE = Score()

def to_pygame(p):
    """Small hack to convert pymunk to pygame coordinates"""
    return int(p.x), int(-p.y+600)

def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption("Joints. Just wait and the L will tip over")
    clock = pygame.time.Clock()
    running = True

    ### Physics stuff
    pm.init_pymunk()
    space = pm.Space()
    space.gravity = (0.0, -900.0)

    space.resize_static_hash()
    space.resize_active_hash()

    ### static stuff
    ground_body = pm.Body(pm.inf, pm.inf)
    ground_body.position = (300,40)

    ground = pm.Segment(ground_body, (-1000,0), (1000,0), 5.0)
    ground.friction = 0.6
    ground.color = THECOLORS['black']
    mat = pm.Segment(ground_body, (-200,5), (200,5), 5.0)
    mat.friction = 0.6
    mat.color = THECOLORS['red']
    space.add(ground, mat)

    ### The moving L shape
    l_head = (25, (-50, 55))
    l_shoulder = (-50, 30)
    l_hip = (-50,0)

    r_head = (25, (50, 55))
    r_shoulder = (50, 30)
    r_hip = (50,0)
    r_knee = (30,-20)
    r_foot = (50,-40)

    body = pm.Body(10,10000)

    LEG_LEN = 35

    left_thigh = pm.Body(10, 10000)
    left_calf = pm.Body(10, 10000)

    right_thigh = pm.Body(10, 10000)
    right_calf = pm.Body(10, 10000)

    lines = [pm.Segment(body, l_shoulder, l_hip, 5.0) 
            ,pm.Segment(body, r_shoulder, r_hip, 5.0)
            ,pm.Segment(body, r_shoulder, l_hip, 5.0)
            ,pm.Segment(body, l_shoulder, r_hip, 5.0)

            ,pm.Segment(left_thigh, (0,0), (0,-LEG_LEN), 5.0)
            ,pm.Segment(left_calf, (0,0), (0,-LEG_LEN), 5.0)
            ,pm.Segment(right_thigh, (0,0), (0,-LEG_LEN), 5.0)
            ,pm.Segment(right_calf, (0,0), (0,-LEG_LEN), 5.0)
    ]

    left_head = pm.Circle(body, *l_head)
    right_head = pm.Circle(body, *r_head)

    left_foot = pm.Circle(left_calf, 1, (0,-LEG_LEN))
    right_foot = pm.Circle(right_calf, 1, (0,-LEG_LEN))
    left_foot.friction = 0.6
    right_foot.friction = 0.6

    feet = [left_foot, right_foot]

    space.add(body, lines, left_head, right_head, feet, left_thigh, left_calf, right_thigh, right_calf)

    MUSCLE_STRENGTH = 6000000
    MUSCLE_STIFFNESS = 10000

    def reset():
        body.position = (300,300)
        left_thigh.position = 250,300
        left_calf.position = 250,300-LEG_LEN
        right_thigh.position = 350,300
        right_calf.position = 350,300-LEG_LEN
        for obj in (body, left_thigh, left_calf, right_thigh, right_calf):
            obj.angle = 0
            obj.velocity = (0,0)
            obj.angular_velocity = 0
            obj.reset_forces()

    def onCollision(space, arbiter):
        dead = False
        shapes = arbiter.shapes
        if left_head in shapes:
            RIGHT_SCORE.inc()
            dead = True 
        elif right_head in shapes:
            LEFT_SCORE.inc()
            dead = True
        elif ground in shapes:
            if left_head in shapes or left_foot in shapes:
                RIGHT_SCORE.inc()
                dead = True
            elif right_head in shapes or left_foot in shapes:
                LEFT_SCORE.inc()
                dead = True
        if dead:
            print "Left has %s, right has %s" % (LEFT_SCORE, RIGHT_SCORE)
            reset()
            return True
            
        return True
    space.add_collision_handler(0, 0, onCollision, None, None, None) 

    reset()

    space.add(pm.PinJoint(body, left_thigh, l_hip, (0,0)))
    left_thigh_muscle = pm.DampedRotarySpring(body, left_thigh, -(math.pi/4), MUSCLE_STRENGTH, MUSCLE_STIFFNESS)
    left_calf_muscle = pm.DampedRotarySpring(left_thigh, left_calf, (math.pi/2), MUSCLE_STRENGTH, MUSCLE_STIFFNESS)
    space.add(pm.PinJoint(left_thigh, left_calf, (0,-LEG_LEN), (0,0)))
    space.add(left_thigh_muscle, left_calf_muscle)

    space.add(pm.PinJoint(body, right_thigh, r_hip, (0,0)))
    space.add(pm.PinJoint(right_thigh, right_calf, (0,-LEG_LEN), (0,0)))
    right_thigh_muscle = pm.DampedRotarySpring(body, right_thigh, (math.pi/4), MUSCLE_STRENGTH, MUSCLE_STIFFNESS)
    right_calf_muscle = pm.DampedRotarySpring(right_thigh, right_calf, -(math.pi/2), MUSCLE_STRENGTH, MUSCLE_STIFFNESS)
    space.add(right_thigh_muscle, right_calf_muscle)

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

            elif event.type == KEYDOWN and event.key == K_DOWN:
                right_thigh_muscle.rest_angle = (math.pi/8)
                right_calf_muscle.rest_angle = -(math.pi/4)
            elif event.type == KEYUP and event.key in (K_UP, K_DOWN):
                right_thigh_muscle.rest_angle = (math.pi/4)
                right_calf_muscle.rest_angle = -(math.pi/2)
            elif event.type == KEYDOWN and event.key == K_UP:
                right_thigh_muscle.rest_angle = (math.pi/2)
                right_calf_muscle.rest_angle = -(math.pi)

            elif event.type == KEYDOWN and event.key == K_s:
                left_thigh_muscle.rest_angle = -(math.pi/8)
                left_calf_muscle.rest_angle = (math.pi/4)
            elif event.type == KEYUP and event.key in (K_s, K_w):
                left_thigh_muscle.rest_angle = -(math.pi/4)
                left_calf_muscle.rest_angle = (math.pi/2)
            elif event.type == KEYDOWN and event.key == K_w:
                left_thigh_muscle.rest_angle = -(math.pi/2)
                left_calf_muscle.rest_angle = (math.pi)

        ### Clear screen
        screen.fill(THECOLORS["white"])
        
        ### Draw stuff
        for line in lines:
            body = line.body
            pv1 = body.position + line.a.rotated(body.angle)
            pv2 = body.position + line.b.rotated(body.angle)
            p1 = to_pygame(pv1)
            p2 = to_pygame(pv2)
            pygame.draw.lines(screen, THECOLORS["black"], False, [p1,p2], 4)

        for head in (left_head, right_head):
            body = head.body
            cv = body.position + head.offset.rotated(body.angle)
            c = to_pygame(cv)
            pygame.draw.circle(screen, THECOLORS["black"], c, int(head.radius))

        for line in (ground, mat):
            offset = line.body.position
            a = to_pygame(offset+line.a)
            b = to_pygame(offset+line.b)
            pygame.draw.lines(screen, line.color, False, [a, b], 4)

        ### Update physics
        dt = 1.0/50.0/10.0
        for x in range(10):
            space.step(dt)

        ### Flip screen
        pygame.display.flip()
        clock.tick(50)

        
if __name__ == '__main__':
    sys.exit(main())
