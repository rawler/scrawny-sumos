#!/usr/bin/env python

import pygame
from pygame.locals import *
from pygame.color import *
import pymunk as pm
import math, sys, random

LEG_LEN = 35
MUSCLE_STRENGTH = 4000000
MUSCLE_STIFFNESS = 20000

class Player(object):
    def __init__(self, world, shared_body, direction):
        self.world = world
        self.shared_body = shared_body
        self.direction = direction
        self.stretch = (math.pi/4)
        self.angle = 0
        self.score = 0

        self._setup()

    def _setup(self):
        direction = self.direction
        self.head = pm.Circle(self.shared_body, 25, (50*direction, 55))

        self.thigh = pm.Body(10, 10000)
        self.calf = pm.Body(10, 10000)

        self.segments = [
            pm.Segment(self.thigh, (0,0), (0,-LEG_LEN), 5.0),
            pm.Segment(self.calf, (0,0), (0,-LEG_LEN), 5.0),
        ]

        self.reset()

        hip_joint = pm.PinJoint(self.shared_body, self.thigh, (50*direction,0), (0,0))
        knee_joint = pm.PinJoint(self.thigh, self.calf, (0,-LEG_LEN), (0,0))

        self.thigh_muscle = pm.DampedRotarySpring(self.shared_body, self.thigh, 0, MUSCLE_STRENGTH, MUSCLE_STIFFNESS)
        self.calf_muscle = pm.DampedRotarySpring(self.thigh, self.calf, 0, MUSCLE_STRENGTH, MUSCLE_STIFFNESS)

        self.foot = pm.Circle(self.calf, 1, (0,-LEG_LEN))
        self.foot.friction = 0.6
        self.world.add(self.head, self.thigh, self.calf, self.segments, hip_joint, knee_joint, self.thigh_muscle, self.calf_muscle, self.foot)
        self.updateMuscles()

    def updateMuscles(self):
        self.thigh_muscle.rest_angle = (self.angle + self.stretch) * self.direction
        self.calf_muscle.rest_angle = (-self.stretch*2) * self.direction

    def reset(self):
        self.thigh.position = 300+(50*self.direction),300
        self.calf.position = 300+(50*self.direction),300-LEG_LEN
        for obj in (self.thigh, self.calf):
            obj.angle = 0
            obj.velocity = (0,0)
            obj.angular_velocity = 0
            obj.reset_forces()

    def draw(self, screen):
        head = self.head
        body = head.body
        cv = body.position + head.offset.rotated(body.angle)
        c = to_pygame(cv)
        pygame.draw.circle(screen, THECOLORS["black"], c, int(head.radius))

        for line in self.segments:
            body = line.body
            pv1 = body.position + line.a.rotated(body.angle)
            pv2 = body.position + line.b.rotated(body.angle)
            pt1 = to_pygame(pv1)
            pt2 = to_pygame(pv2)
            pygame.draw.lines(screen, THECOLORS["black"], False, [pt1,pt2], 4)

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
    l_shoulder = (-50, 30)
    l_hip = (-50,0)
    r_shoulder = (50, 30)
    r_hip = (50,0)

    body = pm.Body(10,10000)

    lines = [pm.Segment(body, l_shoulder, l_hip, 5.0) 
            ,pm.Segment(body, r_shoulder, r_hip, 5.0)
            ,pm.Segment(body, r_shoulder, l_hip, 5.0)
            ,pm.Segment(body, l_shoulder, r_hip, 5.0)
    ]

    space.add(body, lines)
    body.position = 300,300

    P1 = Player(space, body, -1.0)
    P2 = Player(space, body, 1.0)

    def reset():
        body.position = (300,300)
        body.angle = 0
        body.velocity = (0,0)
        body.angular_velocity = 0
        body.reset_forces()
        P1.reset()
        P2.reset()

    def kill(player):
        if player is P1:
            P2.score += 1
        else:
            P1.score += 1
        print "Scores: Left %s, right %s" % (P1.score, P2.score)
        reset()

    def onCollision(space, arbiter):
        shapes = arbiter.shapes
        if P1.head in shapes:
            kill(P1)
        elif P2.head in shapes:
            kill(P2)
        elif ground in shapes:
            if P1.head in shapes or P1.foot in shapes:
                kill(P1)
            elif P2.head in shapes or P2.foot in shapes:
                kill(P2)

        return True
    space.add_collision_handler(0, 0, onCollision, None, None, None) 

    reset()

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

        P1.draw(screen)
        P2.draw(screen)

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
