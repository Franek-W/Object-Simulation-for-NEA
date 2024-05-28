import random, math, pygame, time
from screeninfo import get_monitors
import numpy as np


# define PyGame constants here:
pygame.init()
for m in get_monitors():
    win_width = m.width
    win_height = m.height
# window_size = (win_width, win_height-75)
# window_size = (1000, 600)
window_size = (1800, 700)
BORDER_MATERIAL = 'wood'
fps = 200
conversion_factor = 250 # scaling factor used to make it look accurate (becuase everything is in terms of pixels)
# screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
screen = pygame.display.set_mode(window_size, pygame.RESIZABLE)
rect_group = pygame.sprite.Group()

mask_group = pygame.sprite.Group()

font = pygame.font.Font('freesansbold.ttf', 20)


class ObjectRect(pygame.sprite.Sprite):
    def __init__(self, width, height, colour, acceleration_x, acceleration_y, velocity_y, velocity_x, x, y,  material, surface_material, surface_condition):
        # NOTE: REMEMBER TO DO STUFF WITH COEFFICIENT OF RESTITUTION (BOUNCE FACTOR)
        super().__init__()
        self.__width = width    # pixel width
        self.__height = height  # pixel height
        self.__converted_width = self.__width * 10 ** -3    # real life width
        self.__converted_height = self.__height * 10 ** -3  # real life height
        self.__colour = colour
        self.__acceleration_x = acceleration_x
        self.__acceleration_y = acceleration_y
        self.__velocity_y = velocity_y
        self.__velocity_x = velocity_x
        self.__material = material
        self.__surface_material = surface_material
        self.__surface_condition = surface_condition    # 'wetness' scale
        self.__collided_y = False
        self.__collided_x = False
        self.__collided_object = None   # object the 'current' object has collided with
        self.__at_floor = False
        self.__at_ceil = False
        self.__at_wall = False
        self.__direction_y = None   # Up: True, Down: False
        self.__direction_x = None   # Right: True, Left: False
        self.__selected = False # True if the rectangle is the current objecta
        self.__collision_accel = 0  # acceleration of the object after the collision
        self.__angle = 0 # the degree of rotation of the object (clockwise from north)
        self.__coeff_fricions = {'aluminium,aluminium': [1.05, 0.15], # yes, the CoF can be > 1
                            'aluminium,wood': [0.25, 0.15],   # [normal, lubiricated]
                            'aluminium,plastic': [0.3, 0.15],
                            'aluminium,glass': [0.65, 0.15],
                            'aluminium,rubber': [0.8, 0.2],
                            'aluminium,concrete': [0.8, 0.4],
                            'aluminiun,asphalt': [0.75, 0.4],

                            'wood,wood': [0.375, 0.15],
                            'wood,plastic': [0.3, 0.15],
                            'wood,glass': [0.5, 0.15],
                            'wood,rubber': [0.6, 0.25],
                            'wood,concrete': [0.6, 0.3],
                            'wood,asphalt': [0.5, 0.3],

                            'plastic,plastic': [0.3, 0.15],
                            'plastic,glass': [0.45, 0.15],
                            'plastic,rubber': [0.6, 0.25],
                            'plastic,concrete': [0.6, 0.3],
                            'plastic,asphalt': [0.5, 0.3],

                            'glass,glass': [0.65, 0.15],
                            'glass,rubber': [0.75, 0.2],
                            'glass,concrete': [0.75, 0.4],
                            'glass,asphalt': [0.65, 0.4],

                            'rubber,rubber': [1.1, 0.2],
                            'rubber,concrete': [0.6, 0.4],
                            'rubber,asphalt': [0.8, 0.4],

                            'concrete,concrete': [0.8, 0.4],
                            'concrete,asphalt': [0.8, 0.4],

                            'asphalt,asphalt': [0.75, 0.4]}
        self.__coeff_restitution = {'aluminium,aluminium': 0.9,
                            'aluminium,wood': 0.6,
                            'aluminium,plastic': 0.5,
                            'aluminium,glass': 0.935,
                            'aluminium,hard rubber': 0.825,
                            'aluminium,concrete': 0.675,
                            'aluminium,asphalt': 0.675,
                            'wood,wood': 0.55,
                            'wood,plastic': 0.4,
                            'wood,glass': 0.65,
                            'wood,hard rubber': 0.5,
                            'wood,concrete': 0.425,
                            'wood,asphalt': 0.425,
                            'plastic,plastic': 0.4,
                            'plastic,glass': 0.5,
                            'plastic,hard rubber': 0.6,
                            'plastic,concrete': 0.6,
                            'plastic,asphalt': 0.6,
                            'glass,glass': 0.875,
                            'glass,hard rubber': 0.7,
                            'glass,concrete': 0.5,
                            'glass,asphalt': 0.5,
                            'hard rubber,hard rubber': 0.75,
                            'hard rubber,concrete': 0.725,
                            'hard rubber,asphalt': 0.725,
                            'concrete,concrete': 0.7,
                            'concrete,asphalt': 0.7,
                            'asphalt,asphalt': 0.7}
        self.image = pygame.surface.Surface((self.__width, self.__height))
        self.image.fill(self.__colour)
        pygame.draw.rect(self.image, self.__colour, [0, 0, self.__width, self.__height])
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.set_weight()
        self.rect_surface = pygame.Surface((self.__width, self.__height))
        self.rect_surface.fill(self.__colour)

    def get_material_density(self):
        # gets the density according to the material
        if self.__material == 'aluminium':
            return 7850
        elif self.__material == 'wood':
            return 450
        elif self.__material == 'plastic':
            return 935
        elif self.__material == 'glass':
            return 2500
        elif self.__material == 'rubber':   # hard rubber ~ tyre material
            return 930
        elif self.__material == 'concrete':
            return 2400
        elif self.__material == 'asphalt':
            return 2400

    def get_coeff_fricion(self, surface_1, surface_2):
        # gets the coefficient of friction for the 2 surfaces in use
        try:
            norm, lub = self.__coeff_fricions[surface_1 + ',' + surface_2]
            weighted_cof = lub + ((norm - lub) * self.__surface_condition)
            return weighted_cof
        except KeyError:
            try:
                norm, lub = self.__coeff_fricions[surface_2 + ',' + surface_1]
                weighted_cof = norm + ((lub - norm) * self.__surface_condition)
                return weighted_cof
            except KeyError:
                return -1
    
    def get_coeff_restitution(self, surface_1, surface_2):
        try:
            cor = self.__coeff_restitution[surface_1 + ',' + surface_2]
            return cor
        except KeyError:
            try:
                cor = self.__coeff_restitution[surface_2 + ',' + surface_1]
                return cor
            except KeyError:
                # the combination doesn't exist
                return -1
            

    def set_weight(self):
        # gets weight of material based on density
        density = self.get_material_density()
        # mass = density * volume
        self.__mass = density * (self.__converted_width * self.__converted_height)
        # weight = mass * gravity
        self.__weight = self.__mass * 9.81

    def get_weight(self):
        return self.__weight
    
    def get_mass(self):
        return self.__mass

    def apply_gravity(self):
        if not self.__collided_y:  # cannot continue falling when you collide with something
            # accelerates the object according the gravity
            # use v = u + a*t
            # use s = u*t + 0.5 * a * t^2
            v = self.__velocity_y + (9.81 * (1 / fps)) * conversion_factor
            self.__velocity_y = v
            s = (self.__velocity_y * (1 / 60)) + (0.5*9.81*((1 / fps) ** 2)) * conversion_factor
            if self.rect.y + s + self.rect.height <= window_size[1]:
                # the object will stay inside the window
                if not check_y_axis_collisions(rect_group, self, s)[0]: # s = displacement due to gravity
                    # there won't be a collision with another rect object
                    self.rect.y += s
                    self.__collided_y = False
                    self.__direction_y = False
                else:
                    # now make the objects bounce off eachother
                    """working here aswell :("""
                    try:
                        self.__velocity_y = self.__velocity_y * -self.get_coeff_restitution(self.__surface_material, self.__collided_object.get_surface_material())
                    except AttributeError:
                        pass
                    self.__collided_y = True
                    
            else:
                # the object will move outside the window
                # make the object bounce off the wall
                self.__velocity_y = self.__velocity_y * -self.get_coeff_restitution(self.__surface_material, BORDER_MATERIAL)
                self.__at_floor = True

    def get_velocity_y(self):
        return self.__velocity_y
    
    def get_velocity_x(self):
        return self.__velocity_x
    
    def set_velocity_x(self, vx):
        self.__velocity_x = vx
    
    def set_velocity_y(self, vy):
        self.__velocity_y = vy

    def get_acceleration_x(self):
        return self.__acceleration_x
    
    def get_acceleration_y(self):
        return self.__acceleration_y
        # up: True
        # down: False

    def get_direction_x(self):
        return self.__direction_x
        # right: True
        # left: False

    def get_direction_y(self):
        return self.__direction_y

    def get_height(self):
        return self.__height

    def get_width(self):
        return self.__width

    def get_surface(self):
        return self.__surface_material

    def set_collided_object(self, object):
        self.__collided_object = object
    
    def get_collided_object(self):
        return self.__collided_object
    
    def set_collision_frames(self, frames):
        self.__collision_frames = frames
    
    def set_collision_accel(self, accel):
        self.__collision_accel = accel

    def collide_y(self):
        # called when a rect collides with another rect
        self.__collided_y = True
        """
        REMEMBER THE V = 0 IS JUST A TEMP SOLUTION, THIS WONT WORK WITH ACCURATE MATHS
        """
        self.__velocity_y = 0
    
    def de_collide_y(self):
        # called usually an object moves out from under anther one, letting it fall
        self.__collided_y = False
    
    def collide_x(self):
        self.__collided_x = True
    
    def de_collide_x(self):
        self.__collided_x = False

    def kill_self(self):
        # removes its own instance (suicide)
        rect_group.remove(self) # removes from the sprite group
        del(self)
    
    def get_surface_material(self):
        return self.__surface_material
    
    def draw_rect_border(self, newly_selected):
        # draws a border around the current rectangle
        # 'current' rectangle is the one you have clicked on
        if newly_selected:
            new_colour = (self.__colour[0] / 2, self.__colour[1] / 2, self.__colour[2] / 2)
        else:
            new_colour = self.__colour
        pygame.draw.rect(self.image, new_colour, (0, 0, self.__width, self.__height), 5)
        # make this rectangle object the current / selected one (by user)
        self.__selected = True
    
    def deselect(self):
        # makes the rectangle object no longer the selected object
        if self.__selected: # saves uneccesary changes to the object
            self.__selected = False
            self.draw_rect_border(False)

    def get_at_floor(self):
        return self.__at_floor

    def get_colour(self):
        return self.__colour

    def apply_force(self, force_x, force_y):
        # applies the force to the object in the direction you want (-force is left, +force is right)
        if force_x != 0:
            if not check_x_axis_collisions(rect_group, self, force_x)[0]:
                if (force_x > 0 and (self.rect.x + self.rect.width + force_x <= window_size[0])) or (force_x < 0 and (self.rect.x + force_x > 0)):
                    self.rect.x += force_x
                    self.de_collide_x()
                    self.__collided_object = None
                    if force_x > 0:
                        self.__direction_x = True
                    else:
                        self.__direction_x = False
                else:
                    # it will hit a wall -> fix this
                    if self.rect.x > window_size[0] - (self.rect.x + self.rect.width):
                        # hits the right side of the border
                        # make the object bounce off the wall
                        self.__velocity_x = self.__velocity_x * -self.get_coeff_restitution(self.__surface_material, BORDER_MATERIAL)
                        self.__acceleration_x = 0
                    else:
                        # hits the left side of the screen
                        # make the object bounce off the wall
                        self.__velocity_x = self.__velocity_x * -self.get_coeff_restitution(self.__surface_material, BORDER_MATERIAL)
                        self.__acceleration_x = 0
            else:
                
                # make the object bounce off the wall
                # self.__velocity_x = self.__velocity_x * -self.get_coeff_restitution(self.__surface_material, self.__collided_object.get_surface_material())
                # print('worked')
                """
                WORKING HERE *********************************************************************************************************
                """
                self.collide_x()
        if force_y != 0:
            if not check_y_axis_collisions(rect_group, self, force_y)[0]:
                if (force_y > 0 and self.rect.y + self.rect.height + force_y <= window_size[1]) or (force_y < 0 and self.rect.y + force_y > 0):
                    self.rect.y += force_y
                    self.de_collide_y()
                    self.__collided_object = None
                    if force_y > 0:
                        self.__direction_y = False
                    else:
                        self.__direction_y = True
                else:
                    # it will hit either ceiling or wall -> fix this
                    if self.rect.y > window_size[1] - (self.rect.y + self.rect.height):
                        # hits the bottom side of the border (ceiling)
                        # make the object bounce off the wall
                        self.__velocity_y = self.__velocity_y * -self.get_coeff_restitution(self.__surface_material, BORDER_MATERIAL)
                        self.__acceleration_y = 0
                    else:
                        # hits the top side of the screen (floor)
                        # make the object bounce off the wall
                        self.__velocity_y = self.__velocity_y * -self.get_coeff_restitution(self.__surface_material, BORDER_MATERIAL)
                        self.__acceleration_y = 0
            else:
                """Working here 3rd time now?"""
                try:
                    self.__velocity_y = self.__velocity_y * -self.get_coeff_restitution(self.__surface_material, self.__collided_object.get_surface_material())
                except AttributeError:
                    pass
                # self.collide_y()
                print('worked and collided')

    def apply_accel_force(self, force_x, force_y):
        # accelerates an object (rather than just teleporting it)
        if force_x != 0:
                if not self.__at_wall:
                    # a = F / m
                    try:
                        # gets the surface of the object that the current object (self) is touching
                        surface_2 = self.__collided_object.get_surface()
                    except:
                        # self is not touching any object, therefore it must be touching a border (unless in air)
                        surface_2 = BORDER_MATERIAL
                    friction = self.get_coeff_fricion(str(self.__surface_material), str(surface_2)) * self.__weight
                    if self.__direction_x:
                        friction = -friction
                    a = (force_x + friction) / self.__mass  # adding friction here as it is a negative force (acts opposite way)
                    self.__acceleration_x = a
                    v = self.__velocity_x + (a * (1 / fps)) * conversion_factor
                    self.__velocity_x = v
                    s = (self.__velocity_x * (1 / 60)) + (0.5*a*((1 / fps) ** 2)) * conversion_factor
                    if (s > 0 and (self.rect.x + self.rect.width + s <= window_size[0])) or (s < 0 and (self.rect.x + s > 0)):
                        # object will stay inside window
                        collision, self.__collided_object = check_x_axis_collisions(rect_group, self, s)
                        if not collision:
                            # there won't be a collision with another object
                            if s > 0:
                                self.__direction_x = True
                            else:
                                self.__direction_x = False
                            self.rect.x += s
                            self.__collided_x = False
                            self.__collided_object = None
                        else:
                            # there will be a collision
                            self.__collided_x = True
                            self.calculate_momentum_x(self.__collided_object)   # does momentum for the objects involved HERERERERERERERERER ***************
                    else:
                        # the object will move outisde the window -> fix this
                        if self.rect.x > window_size[0] - (self.rect.x + self.rect.width):
                            # hits the right side of the border
                            # make the object bounce off the wall
                            self.__velocity_x = self.__velocity_x * -self.get_coeff_restitution(self.__surface_material, BORDER_MATERIAL)
                        else:
                            # hits the left side of the screen
                            # make the object bounce off the wall
                            self.__velocity_x = self.__velocity_x * -self.get_coeff_restitution(self.__surface_material, BORDER_MATERIAL)
        if force_y != 0:
            if not self.__collided_y:
                if not self.__at_ceil:
                    # a = F / m
                    a = force_y / self.__mass
                    self.__acceleration_y = a
                    v = self.__velocity_y + (a * (1 / fps)) * conversion_factor
                    self.__velocity_y = v
                    s = (self.__velocity_y * (1 / 60)) + (0.5*a*((1 / fps) ** 2)) * conversion_factor
                    if (s > 0 and (self.rect.y + self.rect.height + s <= window_size[1])) or (s < 0 and (self.rect.y + s > 0)):
                        # object will stay inside the window
                        collision, self.__collided_object = check_y_axis_collisions(rect_group, self, s)
                        if not collision:
                            # there won't be a collision with another object
                            if s < 0:
                                self.__direction_y = True
                            else:
                                self.__direction_y = False
                            self.rect.y += s
                            self.__collided_y = False
                            self.__collided_object = None
                        else:
                            # there will be a collision
                            self.__collided_y = True
                            self.calculate_momentum_y(self.__collided_object)
                            """Now make the objects bounce off eachother"""
                            # making the objects bounce off eachother
                            try:
                                self.__velocity_y = self.__velocity_y * -self.get_coeff_restitution(self.__surface_material, self.__collided_object.get_surface_material())
                            except AttributeError:
                                pass
                            print('**************************************************')
                            
                    else:
                        # the object will move outside the window (up or below) -> fix this
                        if self.rect.y > window_size[1] - (self.rect.y + self.rect.height):
                            # hits the bottom side of the border (ceiling)
                            # make the object bounce off the wall
                            self.__velocity_y = self.__velocity_y * -self.get_coeff_restitution(self.__surface_material, BORDER_MATERIAL)
                        else:
                            # hits the top side of the screen (floor)
                            # make the object bounce off the wall
                            self.__velocity_y = self.__velocity_y * -self.get_coeff_restitution(self.__surface_material, BORDER_MATERIAL)
  
    def calc_displacement_x(self):
        # calculating deceleration due to friction
        friction = self.get_coeff_fricion(f'{self.__surface_material}', BORDER_MATERIAL) * self.__weight
        if self.__direction_x:
            friction = -friction
        a = friction / self.__mass
        v = self.__velocity_x + (a * (1 / fps)) * conversion_factor
        if abs(v) <= 0.5:
            # makes sure it isn't jittering between going left and right
            v = 0
            self.__acceleration_x = 0
        self.__velocity_x = v
        s = (v * (1 / 60)) + (0.5*a*((1 / fps) ** 2)) * conversion_factor
        return s

    def calc_displacement_y(self):
        # not doing any friction calculations here -> no friction in air (yet)
        if not (-3 < self.__velocity_y < 3):
            a = self.__acceleration_y
            v = self.__velocity_y + (a * (1 / fps)) * conversion_factor
            s = (v * (1 / 60)) + (0.5*a*((1 / fps) ** 2)) * conversion_factor
            return s
        else:
            return 0
    
    def calculate_momentum_x(self, obj):
        # sorts out the momentums of each objects
        # p = mv
        obj = self.__collided_object
        p_before = (self.__mass * self.__velocity_x) + (obj.get_mass() * obj.get_velocity_x())
        # p_before = p_after becuase momentim is always conserved
        A = [[self.__mass, obj.get_mass()], [-1, 1]]
        B = [p_before, self.__velocity_x]
        # solving simultaneously
        v1, v2 = np.linalg.inv(A).dot(B)
        self.set_velocity_x(v1)
        obj.set_velocity_x(v2)
    
    def calculate_momentum_y(self, obj):
        # sorts out the momentums of each objects
        # p = mv
        obj = self.__collided_object
        p_before = (self.__mass * self.__velocity_y) + (obj.get_mass() * obj.get_velocity_y())
        # p_before = p_after becuase momentim is always conserved
        A = [[self.__mass, obj.get_mass()], [-1, 1]]
        B = [p_before, self.__velocity_y]
        # solving simultaneously
        v1, v2 = np.linalg.inv(A).dot(B)
        self.set_velocity_y(v1)
        obj.set_velocity_y(v2)
        
    def check_momentum_collision(self):
        if self.__velocity_x != 0:
            sx = self.calc_displacement_x()
            sy = self.calc_displacement_y()
            self.apply_force(sx, sy)
        else:
            self.__velocity_x = 0
        
    def rotateeeeeee(self, angle):
        # rotates the object
        """
        have to use a mask -> need a surface
        """
        self.__angle += 1 % 360 # repeats after 359 to 0
        og_image = self.image
        og_image.set_colorkey((0, 0, 0))
        og_image.fill(self.__colour)
        image = og_image.copy()
        image.set_colorkey((0, 0, 0))
        rect = image.get_rect()
        rect.center = (self.rect.center)
        old_center = rect.center
        new_image = pygame.transform.rotate(og_image, self.__angle)
        new_rect = new_image.get_rect()
        new_rect.center = old_center
        screen.blit(new_image, new_rect)
        
        pygame.display.update()
        

        print('woaaarked')
    
    def make_mask(self):
        return pygame.mask.from_surface(self.image)

    def rotate(self, angle):
        # Update the angle
        self.__angle = (self.__angle + angle) % 360
        # Rotate the image and update the rect
        orig_center = self.rect.center
        self.image = pygame.transform.rotate(self.image, angle)
        self.rect = self.image.get_rect(center=orig_center)
        # Update the mask
        self.mask = self.make_mask()

        print('worked')
        
        

"""
BIG ASS PROBLEM:

- you cant rotate an object in pygame, you can only rotate an image
- now have to turn all my objects into images - FUCK THIS SHIT MAN, PYGAME IS SO FUCKING ASS

new idea:
can have the object be made up of lines rather than be a reect object
but this means that all my funcstion that rely on rect.width and so on will not work
"""



""" Non-class functions go here: """

def apply_gravity_to_all(rect_group):
    for rect in rect_group:
        rect.apply_gravity()

def apply_forces_to_all(rect_group):
    # applies any forces acting on an object even when the object isn't selected
    """
    DO THIS ******
    """
    pass

def check_x_axis_collisions(rect_group, cur_obj, sx):
    if sx != 0:
        for obj in rect_group.sprites():
            if obj != cur_obj:
                if sx > 0:
                    # moving right
                    if (obj.rect.y <= cur_obj.rect.y <= obj.rect.y + obj.rect.height) or (obj.rect.y < cur_obj.rect.y + cur_obj.rect.height <= obj.rect.y + obj.rect.height):
                        # they are sharing a y-axis
                        if cur_obj.rect.x + cur_obj.rect.width <= obj.rect.x:
                            if cur_obj.rect.x + cur_obj.rect.width + sx > obj.rect.x:
                                fix_rect_clip_position_x(cur_obj, obj, True)
                                return True, obj
                elif sx < 0:
                    # moving left
                    if (obj.rect.y <= cur_obj.rect.y <= obj.rect.y + obj.rect.height) or (obj.rect.y < cur_obj.rect.y + cur_obj.rect.height <= obj.rect.y + obj.rect.height):
                        # they are sharing a y-axis
                        if cur_obj.rect.x >= obj.rect.x + obj.rect.width:
                            if cur_obj.rect.x + sx < obj.rect.x + obj.rect.width:
                                fix_rect_clip_position_x(cur_obj, obj, False)
                                # sets the 2 objects involved to be colliding with each other
                                cur_obj.set_collided_object(obj)
                                obj.set_collided_object(cur_obj)
                                return True, obj
    return False, None
                        
def check_y_axis_collisions(rect_group, cur_obj, sy):
    if sy != 0:
        for obj in rect_group.sprites():
            if obj != cur_obj:
                if sy > 0:
                    # moving down
                    if (obj.rect.x <= cur_obj.rect.x < obj.rect.x + obj.rect.width) or (obj.rect.x < cur_obj.rect.x + cur_obj.rect.width <= obj.rect.x + obj.rect.width):
                        # they are sharing an x-axis
                        if cur_obj.rect.y + cur_obj.rect.height <= obj.rect.y:
                            if cur_obj.rect.y + cur_obj.rect.height + sy >= obj.rect.y:
                                fix_rect_clip_position_y(cur_obj, obj)
                                return True, obj
                elif sy < 0:
                    # moving up
                    if (obj.rect.x <= cur_obj.rect.x <= obj.rect.x + obj.rect.width) or (obj.rect.x <= cur_obj.rect.x + cur_obj.rect.width <= obj.rect.x + obj.rect.width):
                        # they are sharing an x-axis
                        if cur_obj.rect.y > obj.rect.y + obj.rect.height:
                            if cur_obj.rect.y + sy < obj.rect.y + obj.rect.height:
                                return True, obj
    return False, None

def check_rect_to_rect_collision(rect_group):
    # checks for collisions between 2 rect objects
    for i in range(len(rect_group)):
        try:
            cur_obj = rect_group.sprites()[i]
            for obj in rect_group:
                # loop through all the objects
                if cur_obj != obj:
                    # you're not comparing the same object
                    if (obj.rect.x < cur_obj.rect.x < obj.rect.x + obj.rect.width) or (obj.rect.x < cur_obj.rect.x + cur_obj.rect.width <= obj.rect.x + obj.rect.width):
                        # cur_obj is clipping with obj along x-axis
                        if obj.rect.y < cur_obj.rect.y + cur_obj.rect.height < obj.rect.y + obj.rect.height:
                            # cur_obj is clipping with obj along y-axis
                            cur_obj.collide_y()
                            fix_rect_clip_position_y(cur_obj, obj)
                            cur_obj.set_collided_object(obj)
                            obj.set_collided_object(cur_obj)
                        else:
                            cur_obj.de_collide_y()
                            cur_obj.de_collide_x()
        except IndexError:
            continue

def fix_rect_clip_position_y(object_1, object_2):
    object_1.rect.y = object_2.rect.y - object_1.rect.height
    object_1.set_collided_object(object_2)
    object_2.set_collided_object(object_1)

def fix_rect_clip_position_x(object_1, object_2, dir):
    if dir:
        # moved right
        object_1.rect.x = object_2.rect.x - object_1.rect.width
    else:
        # moved left
        object_1.rect.x = object_2.rect.x + object_2.rect.width
    object_1.set_collided_object(object_2)
    object_2.set_collided_object(object_1)

def fix_multiple_selected(rect_group, selected_object):
    # makes sure there's only 1 object selected at a time+__
    for rect_object in rect_group:
        if rect_object != selected_object:
            # makes sure you're not deselecting the current object
            rect_object.deselect()

def determine_current_rect(rect_group, mx, my):
    # determines which rectangle is the current one by clicking on it
    # mx: x position of mouse cursor, my: y position of mouse cursor
    for rect_object in rect_group:
        if rect_object.rect.x <= mx <= rect_object.rect.x + rect_object.rect.width:
            # in between x coords of rectangle
            if rect_object.rect.y <= my <= rect_object.rect.y + rect_object.rect.height:
                # in between y coords of rectangle
                rect_object.draw_rect_border(True)
                fix_multiple_selected(rect_group, rect_object)
                # return the current object
                return rect_object

def deselect_all(rect_group):
    for obj in rect_group:
        obj.deselect()

def check_for_actions(current_object):
    keys = pygame.key.get_pressed()
    if keys[pygame.K_RIGHT]:
        # pressed right arrow
        current_object.apply_force(4, 0)
    if keys[pygame.K_LEFT]:
        # pressed left arrow
        current_object.apply_force(-4, 0)
    if keys[pygame.K_UP]:
        # pressed up arrow
        current_object.apply_force(0, -10)
    if keys[pygame.K_DOWN]:
        # pressed down arrow
        current_object.apply_force(0, 10)
    if keys[pygame.K_w]:
        # pressed 'w' key
        current_object.apply_accel_force(0, -200)
    if keys[pygame.K_s]:
        # pressed 's' key
        current_object.apply_accel_force(0, 200)
    if keys[pygame.K_a]:
        # pressed 'a' key
        current_object.apply_accel_force(-200, 0)
    if keys[pygame.K_d]:
        # pressed 'd' key
        current_object.apply_accel_force(200, 0)
    if keys[pygame.K_r]:
        # pressed 'r' key
        current_object.rotate(1)
    else:
        # no acceleration is being applied to the block, it will move by itself
        sx = current_object.calc_displacement_x()
        sy = current_object.calc_displacement_y()
        current_object.apply_force(sx, sy)

def check_all_momemtum_collisions(rect_group):
    for obj in rect_group:
        obj.check_momentum_collision()


# Main game loop
def main():
    end = False
    while not end:
        # time.sleep(0.00001)
        # this is where the PyGame elements go
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # user exited the window (pressed x at top right)
                end = True
            elif event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_SPACE]:
                    # space bar was pressed -> add rectangle to screen
                    colour = list(np.random.choice(range(256), size=3))
                    material = random.choice(['aluminium', 'wood', 'plastic', 'rubber', 'glass'])
                    random_x = random.randint(0, window_size[0])
                    random_y = random.randint(0, window_size[1])
                    random_size_y = random.randint(50, 150)
                    random_size_x = random.randint(50, 150)
                    rect = ObjectRect(100, 100, (200, 200, 200), 0, 0, 0, 0, 600, 100, 'plastic', 'aluminium', 1)
                    # (width, height, colour, acceleration_x, acceleration_y, velocity_y, velocity_x, x, y,  material, surface_material, surface_condition)
                    rect_group.add(rect)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # pressed LMB
                    mx, my = pygame.mouse.get_pos()
                    # check which rectangle the user clicked on
                    current_object = determine_current_rect(rect_group, mx, my)
                elif event.button == 3:
                    deselect_all(rect_group)
                    current_object = None
        
        # check for key presses:
        try:
            check_for_actions(current_object)
        except:
            pass

        # rect gravity application:
        apply_gravity_to_all(rect_group)
        rect_group.update()
        
        # check momentum collisions:
        check_all_momemtum_collisions(rect_group)

        # check collisions:
        check_rect_to_rect_collision(rect_group)
        rect_group.update()

        # drawing to screen:
        screen.fill((38, 38, 38))
        rect_group.draw(screen)

        # drawing text to screen:
        try:
            velocity_x = str(round(current_object.get_velocity_x()))
            velocity_y = str(round(current_object.get_velocity_y()))
        except:
            velocity_x = 0
            velocity_y = 0
        text_vel_x = font.render(f'vx: {velocity_x}', True, (200, 200, 200), (38, 38, 38))
        text_vel_y = font.render(f'vy: {velocity_y}', True, (200, 200, 200), (38, 38, 38))
        text_vel_x_rect = text_vel_x.get_rect()
        text_vel_y_rect = text_vel_y.get_rect()
        text_vel_x_rect.center = (40, 20)
        text_vel_y_rect.center = (40, 45)
        screen.blit(text_vel_x, text_vel_x_rect)
        screen.blit(text_vel_y, text_vel_y_rect)
        pygame.display.set_caption(f'VX: {velocity_x}  |  VY: {velocity_y}')

        # update the screen:
        pygame.display.update()
        pygame.time.Clock().tick(fps)

if __name__ == '__main__':
    main()