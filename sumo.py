#!/usr/bin/env python

import pygame
from pygame.locals import *
from pygame.color import *
import pymunk as pm
import math, sys, random
X,Y,Z = 0,1,2 # Easy indexing

class Player(object):
    def __init__(self, thigh_muscle, calf_muscle, direction):
        self.thigh_muscle = thigh_muscle
        self.calf_muscle = calf_muscle
        self.direction = direction
        self.stretch = (math.pi/4)
        self.angle = 0
        self.score = 0

    def updateMuscles(self):
        self.thigh_muscle.rest_angle = (self.angle + self.stretch) * self.direction
        self.calf_muscle.rest_angle = (-self.stretch*2) * self.direction

def to_pygame(p):
    """Small hack to convert pymunk to pygame coordinates"""
    return int(p.x), int(-p.y+600)

def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 600))
    pygame.display.set_caption("Fight!")
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

    MUSCLE_STRENGTH = 4000000
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

    def kill(player):
        if player is P1:
            P2.score += 1
        else:
            P1.score += 1
        print "Scores: Left %s, right %s" % (P1.score, P2.score)
        reset()

    def onCollision(space, arbiter):
        shapes = arbiter.shapes
        if left_head in shapes:
            kill(P1)
        elif right_head in shapes:
            kill(P2)
        elif ground in shapes:
            if left_head in shapes or left_foot in shapes:
                kill(P1)
            elif right_head in shapes or right_foot in shapes:
                kill(P2)

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

    P1 = Player(left_thigh_muscle, left_calf_muscle, -1.0)
    P2 = Player(right_thigh_muscle, right_calf_muscle, 1.0)

    STRETCH_RANGE = math.pi/5
    ANGLE_RANGE = math.pi/5
    KEYS = {
        K_w: (P1, STRETCH_RANGE, 0),
        K_s: (P1, -STRETCH_RANGE, 0),
        K_d: (P1, 0, ANGLE_RANGE),
        K_a: (P1, 0, -ANGLE_RANGE),

        K_UP: (P2, STRETCH_RANGE, 0),
        K_DOWN: (P2, -STRETCH_RANGE, 0),
        K_LEFT: (P2, 0, ANGLE_RANGE),
        K_RIGHT: (P2, 0, -ANGLE_RANGE),
    }

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False

            elif event.type == KEYDOWN and event.key in KEYS:
                player, stretch, angle = KEYS[event.key]
                player.stretch += stretch
                player.angle += angle
                player.updateMuscles()

            elif event.type == KEYUP and event.key in KEYS:
                player, stretch, angle = KEYS[event.key]
                player.stretch -= stretch
                player.angle -= angle
                player.updateMuscles()

        ### Clear screen
        screen.fill(THECOLORS["white"])
        
        ### Draw stuff
        for line in lines:
            body = line.body
            pv1 = body.position + line.a.rotated(body.angle)
            pv2 = body.position + line.b.rotated(body.angle)
            pt1 = to_pygame(pv1)
            pt2 = to_pygame(pv2)
            pygame.draw.lines(screen, THECOLORS["black"], False, [pt1,pt2], 4)

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
