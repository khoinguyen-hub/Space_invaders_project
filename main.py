
from pygame import *
import sys
from os.path import abspath, dirname
from random import choice

base_path = abspath(dirname(__file__))
font_path = base_path + '/fonts'
image_path = base_path + '/images'
sound_path = base_path + '/sounds'

#colors (R,G,B)
white = (255, 255, 255)
green = (78, 255, 87)
yellow = (241, 255, 0)
blue = (80, 255, 0)
purple = (203, 0 ,255)
red = (237, 28, 36)

screen = display.set_mode((800, 600))

#load files and images
font = font_path + 'space_invaders.ttf'
images_names = ['ship', 'mystery', 'enemy1_1', 'enemy1_2', 'enemy2_1', 'enemy2_2', 'enemy3_1', 'enemy3_2',
                'explosionblue', 'explosiongreen', 'explosionpurple', 'laser', 'enemylaser']
images_load_files = {name: image.load(image_path + '{}.png'.format(name)).covert_alpha() for name in images_names}

barrier_position = 450
alien_default_position = 65
alien_move_down = 35

class Ship(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = images_load_files['ship']
        self.rect = self.image.get_rect(topleft=(375, 540))
        self.speed = 5

    def update(self, keys, *args):
        if keys[K_LEFT] and self.rect.x > 10:
            self.rect.x -= self.speed
        if keys[K_RIGHT] and self.rect.x < 740:
            self.rect.x += self.speed
        #draw the ship everytime update is call
        game.screen.blit(self.image, self.rect)

class Bullet(sprite.Sprite):
    def __init__(self, x_position, y_position, direction, speed, filename, type):
        sprite.Sprite.__init__(self)
        #passing different filename for different bullet type
        self.image = images_load_files[filename]
        self.rect = self.image.get_rect(topleft=(x_position, y_position))
        self.speed = speed
        self.direction = direction
        #ship or enemy bullet
        self.type = type
        self.filename = filename

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)
        self.rect.y += self.speed * self.direction
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()

class Alien(sprite.Sprite):
    def __init__(self, row, column):
        sprite.Sprite.__init__(self)
        self.row = row
        self.column = column
        self.images = []
        self.alien_images()
        self.index = 0
        self.images = self.images[self.index]
        self.rect = self.image.get_rect()

    #rotates between the image frames of an alien
    def toggle_image(self):
        self.index += 1
        #reset the counter if already reach the end of the frames
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def update(self, *args):
        game.screen.blit(self.image, self.rect)

    def alien_images(self):
        #a dictionary with the keys being the number of rows and values are the name that allows
        #image loader to access that specific alien images
        images = {0: ['1_2', '1_1'], 1: ['2_2', '2_1'], 2: ['2_2', '2_1'], 3: ['3_1', '3_2'],
                  4: ['3_1', '3_2']}
        image1, image2 = (images_load_files['enemy{}'.format(image_number)] for image_number in images[self.row])
        self.images.append(transform.scale(image1, (40, 35)))
        self.images.append(transform.scale(image2, (40, 35)))

class AliensGroup(sprite.Group):
    def __init__(self, columns, rows):
        sprite.Group.__init__(self)
        self.aliens = [[None] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        self.leftAddMove = 0
        self.rightAddMove = 0
        self.moveTime = 600
        self.direction = 1
        self.rightMoves = 30
        self.leftMoves = 30
        self.moveNumber = 15
        self.timer = time.get_ticks()
        self.bottom = game.enemyPosition + ((rows-1) * 45) + 35
        self._aliveColumns = list(range(columns))
        self._leftAliveColumn = 0
        self._rightAliveColumn = columns - 1

    def update(self, current_time):
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:
                max_move = self.rightMoves + self.rightAddMove
            else:
                max_move = self.leftMoves + self.leftAddMove

            #when the alien group reach one side of the screen
            if self.moveNumber >= max_move:
                self.leftMoves = 30 + self.rightAddMove
                self.rightMoves = 30 +self.leftAddMove
                #change direction to allow the group to move the opposite direction
                self.direction *= -1
                self.moveNumber = 0
                self.bottom = 0
                for alien in self:
                    #move the whole group of alien down
                    alien.rect.y += alien_move_down
                    #as the group moves, aliens rotate through their frames
                    alien.toggle_image()
                    if self.bottom < alien.rect.y + 35:
                        self.bottom = alien.rect.y + 35
            else:
                velocity = 10 if self.direction == 1 else -10
                for alien in self:
                    alien.rect.x += velocity
                    alien.toggle_image()
                self.moveNumber += 1

            self.timer += self.moveTime

    #function to add aliens to the game
    def add_internal(self, *sprites):
        #allows a temporary AliensGroup class instance to call this function
        super(AliensGroup, self).add_internal(self, *sprites)
        for s in sprites:
            self.aliens[s.row][s.column] = s

    #function to remove aliens from the game
    def remove_internal(self, *sprites):
        super(AliensGroup, self).remove_internal(*sprites)
        for s in sprites:
            self.kill(s)
        self.update_speed()

    def is_column_dead(self, column):
        # if column is full on None, return true
        return not any(self.aliens[row][column] for row in range(self.rows))

    #increases speed when number of aliens decreases
    def update_speed(self):
        if len(self) == 1:
            self.moveTime = 200
        elif len(self) <= 10:
            self.moveTime = 400

    def kill(self, alien):
        self.aliens[alien.row][alien.column] = None
        #check if all the aliens in this column is dead
        is_column_dead = self.is_column_dead(alien.column)
        #if true
        if is_column_dead:
            #remove this column from alive column list
            self._aliveColumns.remove(alien.column)

        #if dead alien's column is on the furthest right
        if alien.column == self._rightAliveColumn:
            #if the entire column is empty
            while self._rightAliveColumn > 0 and is_column_dead:
                #update the right boundary where alien would move opposite direction when reached
                self._rightAliveColumn -= 1
                self.rightAddMove += 5
                is_column_dead = self.is_column_dead(self._rightAliveColumn)

        elif alien.column == self._leftAliveColumn:
            while self._leftAliveColumn < self.columns and is_column_dead:
                self._leftAliveColumn +=1
                self.leftAddMove += 5
                is_column_dead = self.is_column_dead(self._leftAliveColumn)

class Barrier(sprite.Sprite):
    def __init__(self, size, color, row, column):
        sprite.Sprite.__init__(self)
        self.height = size
        self.width = size
        self.color = color
        self.image = Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column

    def update(self, keys, *args):
        game.screen.blit(self.image, self.rect)

class UFO(sprite.Sprite):
    def __init__(self):
        sprite.Sprite.__init__(self)
        self.image = images_load_files['mystery']
        self.image = transform.scale(self.image, (75, 35))
        self.rect =self.image.get_rect(topleft=(-80, 45))
        self.row = 5
        self.moveTime = 25000
        self.direction = 1
        self.timer = time.get_ticks()
        self.



def main(self):



if __name__ == '__main__':
    game = Game()
    game.main()


