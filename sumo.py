#!/usr/bin/env python

import pyglet
import urllib2
import pymunk as pm
import math, sys, random

LEG_LEN = 35
MUSCLE_STRENGTH = 4000000
MUSCLE_STIFFNESS = 20000

GL = pyglet.gl
KEY = pyglet.window.key

class Player(object):
    def __init__(self, world, shared_body, direction):
        self.world = world
        self.shared_body = shared_body
        self.direction = direction
        self.stretch = (math.pi/4)
        self.angle = 0
        self.score = 0
        self.image = None

        self._setup()

    def setImage(self, image):
        image = urllib2.urlopen(image)
        pygimage = pyglet.image.load('', file=image)
        image.close()
        image = self.image = pyglet.sprite.Sprite(pygimage)
        if image.width > image.height:
            image.scale = 50.0/image.width
        else:
            image.scale = 50.0/image.height
        image.x = -image.width/2
        image.y = -image.height/2

    def _setup(self):
        direction = self.direction

        self.head_body = pm.Body(3, 10000)
        self.head_body.player = self
        self.head = pm.Circle(self.head_body, 25, (0,0))
        self.head.ignore_internal = True
        self.head.player = self

        self.thigh = pm.Body(10, 10000)
        self.calf = pm.Body(10, 10000)

        self.segments = [
            pm.Segment(self.thigh, (0,0), (0,-LEG_LEN), 5.0),
            pm.Segment(self.calf, (0,0), (0,-LEG_LEN), 5.0),
        ]

        self.reset()

        neck_joint = pm.PinJoint(self.shared_body, self.head_body, (50*direction,30), (0,-25))
        hip_joint = pm.PinJoint(self.shared_body, self.thigh, (50*direction,0), (0,0))
        knee_joint = pm.PinJoint(self.thigh, self.calf, (0,-LEG_LEN), (0,0))

        self.buttock = pm.Circle(self.thigh, 1, (0,0))
        self.buttock.ignore_internal = True
        self.buttock.player = self
        self.knee = pm.Circle(self.calf, 1, (0,0))
        self.knee.ignore_internal = True
        self.knee.player = self

        self.neck_muscle = pm.DampedRotarySpring(self.shared_body, self.head_body, 0, MUSCLE_STRENGTH, MUSCLE_STIFFNESS/10)
        self.thigh_muscle = pm.DampedRotarySpring(self.shared_body, self.thigh, 0, MUSCLE_STRENGTH, MUSCLE_STIFFNESS)
        self.calf_muscle = pm.DampedRotarySpring(self.thigh, self.calf, 0, MUSCLE_STRENGTH, MUSCLE_STIFFNESS)

        self.foot = pm.Circle(self.calf, 1, (0,-LEG_LEN))
        self.foot.friction = 0.5
        self.foot.player = self
        self.world.add(self.head_body, self.head, neck_joint, self.neck_muscle, self.thigh, self.calf, self.segments, hip_joint, self.buttock, knee_joint, self.knee, self.thigh_muscle, self.calf_muscle, self.foot)
        self.updateMuscles()
        self.revive()

    def updateMuscles(self):
        self.thigh_muscle.rest_angle = (self.angle + self.stretch) * self.direction
        self.calf_muscle.rest_angle = (-self.stretch*2) * self.direction

    def die(self):
        self.dead = True
        for m in (self.neck_muscle, self.thigh_muscle, self.calf_muscle):
            m.stiffness = 0
            m.damping = 0

    def revive(self):
        for m in (self.neck_muscle, self.thigh_muscle, self.calf_muscle):
            m.stiffness = MUSCLE_STRENGTH
            m.damping = MUSCLE_STIFFNESS
        self.neck_muscle.damping = MUSCLE_STIFFNESS/20
        self.dead = False

    def reset(self):
        self.head_body.position = 50*self.direction,355
        self.thigh.position = 50*self.direction,300
        self.calf.position = 50*self.direction,300-LEG_LEN
        for obj in (self.thigh, self.calf, self.head_body):
            obj.angle = 0
            obj.velocity = (0,0)
            obj.angular_velocity = 0
            obj.reset_forces()

    def draw(self):
        # Draw head
        head = self.head
        body = head.body
        rad = head.radius

        GL.glPushMatrix()
        x,y = body.position
        GL.glTranslatef(x, y, 0.0)
        GL.glRotatef(body.angle*(180/math.pi), 0, 0, 1)
        x,y = head.offset
        GL.glTranslatef(x, y, 0.0)
        GL.glBegin(GL.GL_TRIANGLE_FAN)
        radius = head.radius
        GL.glVertex2f(0,0)
        for i in xrange(17):
            rad = ((i+1)/8.0)*math.pi
            GL.glVertex2f(math.cos(rad)*radius,math.sin(rad)*radius);
        GL.glEnd()
        if self.image:
            self.image.draw()
        GL.glPopMatrix()

        # Draw legs
        for line in self.segments:
            body = line.body
            GL.glPushMatrix()
            x,y = body.position
            GL.glTranslatef(x, y, 0.0)
            GL.glRotatef(body.angle*(180/math.pi), 0, 0, 1.0)

            GL.glBegin(GL.GL_LINES)
            GL.glVertex2f(*line.a)
            GL.glVertex2f(*line.b)
            GL.glEnd()
            GL.glPopMatrix()

class Ground(object):
    def __init__(self, space):
        self.body = body = pm.Body(pm.inf, pm.inf)
        body.position = (0,40)

        self.ground = ground = pm.Segment(body, (-1000,0), (1000,0), 5.0)
        ground.friction = 0.5
        ground.color = (1.0, 1.0, 1.0)
        self.mat = mat = pm.Segment(body, (-200,5), (200,5), 5.0)
        mat.friction = 0.5
        mat.color = (1.0, 0.0, 0.0)
        space.add(ground, mat)

    def draw(self):
        for line in (self.mat, self.ground):
            body = line.body
            GL.glPushMatrix()
            x,y = body.position
            GL.glTranslatef(x, y, 0.0)
            GL.glRotatef(body.angle*(180/math.pi), 0, 0, 1.0)
            GL.glColor3f(*line.color)

            GL.glBegin(GL.GL_LINES)
            GL.glVertex2f(*line.a)
            GL.glVertex2f(*line.b)
            GL.glEnd()
            GL.glPopMatrix()


### Physics stuff
pm.init_pymunk()
space = pm.Space()
space.gravity = (0.0, -900.0)

space.resize_static_hash()
space.resize_active_hash()

GROUND = Ground(space)

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
body.position = 0,300

P1 = Player(space, body, -1.0)
P2 = Player(space, body, 1.0)

def reset(_=None):
    body.position = (0,300)
    body.angle = 0
    body.velocity = (0,0)
    body.angular_velocity = 0
    body.reset_forces()
    P1.reset()
    P1.revive()
    P2.reset()
    P2.revive()

def kill(player):
    if player.dead:
        return
    if player is P1:
        other = P2
    else:
        other = P1
    other.score += 1
    other.score_label.text = str(other.score)
    player.die()
    print "Scores: Left %s, right %s" % (P1.score, P2.score)
    if not other.dead:
        pyglet.clock.schedule_once(reset, 1.5)

def onCollision(space, arbiter):
    shapes = arbiter.shapes
    if GROUND.mat in shapes:
        if P1.head in shapes:
            kill(P1)
        elif P2.head in shapes:
            kill(P2)
    elif GROUND.ground in shapes:
        for s in shapes:
            if hasattr(s,'player'):
                kill(s.player)
    else:
        for shape in arbiter.shapes:
            if hasattr(shape, "ignore_internal"):
                return False

    return True
space.add_collision_handler(0, 0, onCollision, None, None, None) 

reset()

STRETCH_RANGE = math.pi/5
ANGLE_RANGE = math.pi/5
KEYS = {
    KEY.W: (P1, STRETCH_RANGE, 0),
    KEY.S: (P1, -STRETCH_RANGE, 0),
    KEY.D: (P1, 0, ANGLE_RANGE),
    KEY.A: (P1, 0, -ANGLE_RANGE),

    KEY.UP: (P2, STRETCH_RANGE, 0),
    KEY.DOWN: (P2, -STRETCH_RANGE, 0),
    KEY.LEFT: (P2, 0, ANGLE_RANGE),
    KEY.RIGHT: (P2, 0, -ANGLE_RANGE),
}

config = pyglet.gl.Config(alpha_size=8)
window = pyglet.window.Window(config=config)
P1.score_label = pyglet.text.Label('0', font_name='Verdana', font_size=36, color=(255,255,255,255),
                                   x=5, y=window.height, anchor_y='top', anchor_x='left')
P2.score_label = pyglet.text.Label('0', font_name='Verdana', font_size=36, color=(255,255,255,255),
                                   x=window.width-5, y=window.height, anchor_y='top', anchor_x='right')

GL.glShadeModel(GL.GL_SMOOTH);
GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA);
GL.glEnable(GL.GL_BLEND);
GL.glEnable(GL.GL_LINE_SMOOTH)
GL.glEnable(GL.GL_POLYGON_SMOOTH)
GL.glHint(GL.GL_LINE_SMOOTH_HINT, GL.GL_NICEST)
GL.glHint(GL.GL_POLYGON_SMOOTH_HINT, GL.GL_NICEST)

@window.event
def on_key_press(symbol, modifiers):
    if symbol == KEY.ESCAPE:
        pyglet.app.exit()
    elif symbol in KEYS:
        player, stretch, angle = KEYS[symbol]
        player.stretch += stretch
        player.angle += angle
        player.updateMuscles()

@window.event
def on_key_release(symbol, modifiers):
    if symbol in KEYS:
        player, stretch, angle = KEYS[symbol]
        player.stretch -= stretch
        player.angle -= angle
        player.updateMuscles()

@window.event
def on_draw():
    window.clear()

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.gluPerspective(60., window.width / float(window.height), .1, 1000.)
    GL.glMatrixMode(GL.GL_MODELVIEW)

    global body
    focusx, focusy = body.position

    GL.glPushMatrix()
    GL.gluLookAt(focusx/2,150,300, focusx, focusy, 0, 0,1,0)

    GL.glLineWidth(3)
    GROUND.draw()

    # Draw shared body
    GL.glColor3f(1.0, 1.0, 1.0)
    for line in lines:
        body = line.body
        GL.glPushMatrix()
        x,y = body.position
        GL.glTranslatef(x, y, 0.0)
        GL.glRotatef(body.angle*(180/math.pi), 0, 0, 1.0)

        GL.glBegin(GL.GL_LINES)
        GL.glVertex2f(*line.a)
        GL.glVertex2f(*line.b)
        GL.glEnd()
        GL.glPopMatrix()

    # Draw individual features
    P1.draw()
    P2.draw()

    GL.glPopMatrix()

    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GL.glOrtho(0, window.width, 0, window.height, 0, 1000.)
    GL.glMatrixMode(GL.GL_MODELVIEW)

    P1.score_label.draw()
    P2.score_label.draw()

def update(dt):
    for x in xrange(10):
        space.step(dt/10.0)
        pass

if __name__ == '__main__':
    import sys

    if len(sys.argv) == 2:
        P1.setImage(sys.argv[1])
        P2.setImage(sys.argv[1])
    elif len(sys.argv) == 3:
        P1.setImage(sys.argv[1])
        P2.setImage(sys.argv[2])

    pyglet.clock.schedule_interval(update, 1/60.0) # update at 60Hz
    pyglet.app.run()
