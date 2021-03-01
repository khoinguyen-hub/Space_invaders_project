
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
images_names = ['ship', 'ship_exp0', 'ship_exp1', 'ship_exp2', 'ship_exp3', 'ship_exp4', 'ship_exp5', 'ship_exp6', 'ship_exp7', 'ship_exp8',
                'mystery', 'alien00', 'alien01', 'alien10', 'alien11', 'alien20', 'alien21', 'a_exp0', 'a_exp1', 'a_exp2', 'laser', 'enemylaser']
images_load_files = {name: image.load(image_path + '{}.png'.format(name)).convert_alpha() for name in images_names}

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
    def __init__(self, x_position, y_position, direction, speed, filename, side):
        sprite.Sprite.__init__(self)
        #passing different filename for different bullet type
        self.image = images_load_files[filename]
        self.rect = self.image.get_rect(topleft=(x_position, y_position))
        self.speed = speed
        self.direction = direction
        #ship or enemy bullet
        self.side = side
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
        images = {0: ['00', '01'], 1: ['10', '11'], 2: ['10', '11'], 3: ['20', '21'],
                  4: ['20', '21']}
        image1, image2 = (images_load_files['alien{}'.format(image_number)] for image_number in images[self.row])
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
        self.ufoEncountered = mixer.Sound(sound_path + 'mysteryentered.wav')
        self.ufoEncountered.set_volume(0.3)
        self.playMusic = True

    def update(self, current_time, *args):
        reset_timer = False
        passed = current_time - self.timer
        if passed > self.moveTime:
            if (self.rect.x < 0 or self.rect.x > 800) and self.playMusic:
                self.ufoEncountered.play()
                self.playMusic = False
            if self.rect.x < 840 and self. direction == 1:
                self.ufoEncountered.fadeout(4000)
                self.rect.x += 2
                game.screen.blit(self.image, self.rect)
            if self.rect.x > -100 and self.direction == -1:
                self.rect.x -= 2
                game.screen.blit(self.image, self.rect)

        if self.rect.x > 830:
            self.playMusic = True
            self.direction = -1
            reset_timer = True
        if self.rect.x < -90:
            self.playMusic = True
            self.direction = 1
            reset_timer = True
        if passed > self.moveTime and reset_timer:
            self.timer = current_time

class AlienExplosion(sprite.Sprite):
    def __init__(self, alien, *groups):
        super(AlienExplosion, self).__init__(*groups)
        self.image = images_load_files['a_exp0']
        self.image2 = images_load_files['a_exp1']
        self.image3 = images_load_files['a_exp2']
        self.rect = self.image.get_rect(topleft=(alien.rect.x, alien.rect.y))
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed < 100:
            game.screen.blit(self.image, self.rect)
        elif 100 < passed <= 200:
            game.screen.blit(self.image2, self.rect)
        elif 200 < passed <= 300:
            game.screen.blit(self.image3, self.rect)
        elif 400 < passed:
            self.kill()

class UfoDie(sprite.Sprite):
    def __init__(self, ufo, score, *groups):
        super(UfoDie, self).__init__(*groups)
        self.text = Text(font, 20, str(score), white, ufo.rect.x + 20, ufo.rect.y + 6)
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 200 or 400 < passed <= 600:
            self.text.draw(game.screen)
        elif 600 < passed:
            self.kill()

class ShipExplosion(sprite.Sprite):
    def __init__(self, ship, *groups):
        super(ShipExplosion, self).__init__(*groups)
        self.image = images_load_files['ship_exp0']
        self.image2 = images_load_files['ship_exp1']
        self.image3 = images_load_files['ship_exp2']
        self.image4 = images_load_files['ship_exp3']
        self.image5 = images_load_files['ship_exp4']
        self.image6 = images_load_files['ship_exp5']
        self.image7 = images_load_files['ship_exp6']
        self.image8 = images_load_files['ship_exp7']
        self.image9 = images_load_files['ship_exp8']
        self.rect = self.image.get_rect(topleft=(ship.rect.x, ship.rect.y))
        self.timer = time.get_ticks()

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed < 100:
            game.screen.blit(self.image, self.rect)
        elif 100 < passed <= 200:
            game.screen.blit(self.image2, self.rect)
        elif 200 < passed <= 300:
            game.screen.blit(self.image2, self.rect)
        elif 300 < passed <= 400:
            game.screen.blit(self.image3, self.rect)
        elif 400 < passed <= 500:
            game.screen.blit(self.image4, self.rect)
        elif 500 < passed <= 600:
            game.screen.blit(self.image5, self.rect)
        elif 600 < passed <= 700:
            game.screen.blit(self.image6, self.rect)
        elif 700 < passed <= 800:
            game.screen.blit(self.image7, self.rect)
        elif 800 < passed <= 900:
            game.screen.blit(self.image8, self.rect)
        elif 900 < passed:
            self.kill()

class ShipLife(sprite.Sprite):
    def __init__(self, x_position, y_position):
        sprite.Sprite.__init__(self)
        self.image = images_load_files['ship']
        self.image = transform.scale(self.image, (23, 23))
        self.rect = self.image.get_rect(topleft=(x_position, y_position))

    def update(self, *args):
        game.screen.blit(self,image, self,rect)

class Text(object):
    def __init__(self, text_font, x_position, y_position, size, message, color):
        self.font = font.Font(text_font, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(x_position, y_position))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)

class Game(object):
    def __init__(self):
        mixer.pre_init(44100, -16, 1, 512)
        init()
        self.clock = time.Clock()
        display.set_caption('Space Invaders')
        self.screen = screen
        self.background = image.load(image_path + 'background.jpg').convert()
        self.startGame = False
        self.mainScreen = True
        self.gameOver = False
        self.alienPosition = alien_default_position
        self.title_text = Text(font, 50, 'Space', white, 164, 155)
        self.title_text2 = Text(font, 35, 'Invaders', green, 201, 225)
        self.game_over_text = Text(font, 50, 'Game Over', white, 250, 270)
        self.next_round_text = Text(font, 50, 'Next Round', white, 240, 270)
        self.alien1_text = Text(font, 25, '  =  10pts', green, 368, 270)
        self.alien2_text = Text(font, 25, '  =  20pts', blue, 368, 370)









def main(self):



if __name__ == '__main__':
    game = Game()
    game.main()


