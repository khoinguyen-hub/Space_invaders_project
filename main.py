import pygame
from pygame import *
import sys
from os.path import abspath, dirname
from random import choice

base_path = abspath(dirname(__file__))
font_path = base_path + '/fonts/'
image_path = base_path + '/images/'
sound_path = base_path + '/sounds/'

# colors (R,G,B)
white = (255, 255, 255)
green = (78, 255, 87)
yellow = (241, 255, 0)
blue = (80, 255, 0)
purple = (203, 0, 255)
red = (237, 28, 36)

screen = display.set_mode((800, 600))

# load files and images
font = font_path + 'space_invaders.ttf'
images_names = ['ship', 'ship_exp0', 'ship_exp1', 'ship_exp2', 'ship_exp3', 'ship_exp4', 'ship_exp5', 'ship_exp6',
                'ship_exp7', 'ship_exp8', 'ufo', 'alien00', 'alien01', 'alien10', 'alien11', 'alien20', 'alien21',
                'a_exp0', 'a_exp1', 'a_exp2', 'laser', 'enemylaser']
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
        # draw the ship everytime update is call
        game.screen.blit(self.image, self.rect)


class Bullet(sprite.Sprite):
    def __init__(self, x_position, y_position, direction, speed, filename, side):
        sprite.Sprite.__init__(self)
        # passing different filename for different bullet type
        self.image = images_load_files[filename]
        self.rect = self.image.get_rect(topleft=(x_position, y_position))
        self.speed = speed
        self.direction = direction
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
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()

    # rotates between the image frames of an alien
    def toggle_image(self):
        self.index += 1
        # reset the counter if already reach the end of the frames
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def update(self, *args):
        game.screen.blit(self.image, self.rect)

    def alien_images(self):
        # a dictionary with the keys being the number of rows and values are the name that allows
        # image loader to access that specific alien images
        images = {0: ['00', '01'], 1: ['10', '11'], 2: ['10', '11'], 3: ['20', '21'],
                  4: ['20', '21']}
        image1, image2 = (images_load_files['alien{}'.format(image_number)] for image_number in images[self.row])
        self.images.append(transform.scale(image1, (50, 45)))
        self.images.append(transform.scale(image2, (50, 45)))


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
        self.bottom = game.alienPosition + ((rows-1) * 45) + 35
        self._aliveColumns = list(range(columns))
        self._leftAliveColumn = 0
        self._rightAliveColumn = columns - 1

    def update(self, current_time):
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:
                max_move = self.rightMoves + self.rightAddMove
            else:
                max_move = self.leftMoves + self.leftAddMove

            # when the alien group reach one side of the screen
            if self.moveNumber >= max_move:
                self.leftMoves = 30 + self.rightAddMove
                self.rightMoves = 30 +self.leftAddMove
                # change direction to allow the group to move the opposite direction
                self.direction *= -1
                self.moveNumber = 0
                self.bottom = 0
                for alien in self:
                    # move the whole group of alien down
                    alien.rect.y += alien_move_down
                    # as the group moves, aliens rotate through their frames
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

    # function to add aliens to the game
    def add_internal(self, *sprites):
        # allows a temporary AliensGroup class instance to call this function
        super(AliensGroup, self).add_internal(*sprites)
        for s in sprites:
            self.aliens[s.row][s.column] = s

    # function to remove aliens from the game
    def remove_internal(self, *sprites):
        super(AliensGroup, self).remove_internal(*sprites)
        for s in sprites:
            self.kill(s)
        self.update_speed()

    def random_bottom(self):
        col = choice(self._aliveColumns)
        col_aliens = (self.aliens[row-1][col] for row in range(self.rows  , 0, -1))
        return next((an for an in col_aliens if an is not None), None)

    def is_column_dead(self, column):
        # if column is full on None, return true
        return not any(self.aliens[row][column] for row in range(self.rows))

    # increases speed when number of aliens decreases
    def update_speed(self):
        if len(self) == 1:
            self.moveTime = 200
        elif len(self) <= 10:
            self.moveTime = 400

    def kill(self, alien):
        self.aliens[alien.row][alien.column] = None
        # check if all the aliens in this column is dead
        is_column_dead = self.is_column_dead(alien.column)
        # if true
        if is_column_dead:
            # remove this column from alive column list
            self._aliveColumns.remove(alien.column)

        # if dead alien's column is on the furthest right
        if alien.column == self._rightAliveColumn:
            # if the entire column is empty
            while self._rightAliveColumn > 0 and is_column_dead:
                # update the right boundary where alien would move opposite direction when reached
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
        self.image = images_load_files['ufo']
        self.image = transform.scale(self.image, (75, 35))
        self.rect = self.image.get_rect(topleft=(-80, 45))
        self.row = 5
        self.moveTime = 25000
        self.direction = 1
        self.timer = time.get_ticks()
        self.ufoEncountered = mixer.Sound(sound_path + 'mysteryentered.wav')
        self.ufoEncountered.set_volume(0.3)
        self.playMusic = True

    def update(self, keys, current_time, *args):
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
        self.text = Text(20, str(score), white, ufo.rect.x + 20, ufo.rect.y + 6)
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
        game.screen.blit(self.image, self.rect)


class Text(object):
    def __init__(self, size, message, color, x_position, y_position):
        self.font = pygame.font.Font(font, size)
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
        self.title_text = Text(100, 'Space', white, 230, 50)
        self.title_text2 = Text(50, 'Invaders', green, 270, 150)
        self.game_over_text = Text(50, 'Game Over', white, 250, 270)
        self.next_round_text = Text(50, 'Next Round', white, 240, 270)
        self.alien1_text = Text(25, '  =  10pts', green, 368, 270)
        self.alien2_text = Text(25, '  =  20pts', blue, 368, 320)
        self.alien3_text = Text(25, '  =  30pts', purple, 368, 370)
        self.alien4_text = Text(25, '  =  ???', red, 368, 420)
        self.score_text = Text(20, 'Score', white, 5, 5)
        self.lives_text = Text(20, 'Lives', white, 640, 5)

        self.ship_life1 = ShipLife(715, 3)
        self.ship_life2 = ShipLife(742, 3)
        self.ship_life3 = ShipLife(769, 3)
        self.ship_life_group = sprite.Group(self.ship_life1, self.ship_life2, self.ship_life3)

    def reset(self, score):
        self.player_object = Ship()
        self.player_object_group = sprite.Group(self.player_object)
        self.explosion_group = sprite.Group()
        self.bullets = sprite.Group()
        self.ufo = UFO()
        self.ufo_group = sprite.Group(self.ufo)
        self.alien_bullets = sprite.Group()
        self.make_aliens()
        self.allSprites = sprite.Group(self.player_object, self.aliens, self.ship_life_group, self.ufo)
        self.keys = key.get_pressed()
        self.timer = time.get_ticks()
        self.note_timer = time.get_ticks()
        self.ship_timer = time.get_ticks()
        self.score = score
        self.create_audio()
        self.make_new_ship = False
        self.ship_alive = True

    def make_barriers(self, n):
        barrier_group = sprite.Group()
        for row in range(4):
            for column in range(9):
                barrier = Barrier(10, green, row, column)
                barrier.rect.x = 50 + (200 * n) + (column * barrier.width)
                barrier.rect.y = barrier_position + (row * barrier.height)
                barrier_group.add(barrier)
        return barrier_group

    def create_audio(self):
        self.sounds = {}
        for sound_name in ['shoot', 'shoot2', 'invaderkilled', 'mysterykilled', 'shipexplosion']:
            self.sounds[sound_name] = mixer.Sound(sound_path + '{}.wav'.format(sound_name))
            self.sounds[sound_name].set_volume(0.2)

        self.music_notes = [mixer.Sound(sound_path + '{}.wav'.format(i)) for i in range(4)]
        for sound in self.music_notes:
            sound.set_volume(0.5)

        self.note_index = 0

    def play_main_music(self, current_time):
        if current_time - self.note_timer > self.aliens.moveTime:
            self.note = self.music_notes[self.note_index]
            if self.note_index < 3:
                self.note_index += 1
            else:
                self.note_index = 0

            self.note.play()
            self.note_timer += self.aliens.moveTime

    @staticmethod
    def should_exit(temp_event):
        return temp_event.type == QUIT or (temp_event.type == KEYUP and temp_event.key == K_ESCAPE)

    def check_input(self):
        self.keys = key.get_pressed()
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
            if e.type == KEYDOWN:
                if e.key == K_SPACE:
                    if len(self.bullets) == 0 and self.ship_alive:
                        if self.score < 1000:
                            bullet = Bullet(self.player_object.rect.x + 23, self.player_object.rect.y + 5, -1, 15,
                                            'laser', 'center')
                            self.bullets.add(bullet)
                            self.allSprites.add(self.bullets)
                            self.sounds['shoot'].play()
                        else:
                            leftbullet = Bullet(self.player_object.rect.x + 8, self.player_object.rect.y + 5, -1, 15,
                                                'laser', 'left')
                            rightbullet = Bullet(self.player_object.rect.x + 38, self.player_object.rect.y + 5, -1, 15,
                                                 'laser', 'right')
                            self.bullets.add(leftbullet)
                            self.bullets.add(rightbullet)
                            self.allSprites.add(self.bullets)
                            self.sounds['shoot2'].play()

    def make_aliens(self):
        aliens = AliensGroup(10, 5)
        for row in range(5):
            for column in range(10):
                alien = Alien(row, column)
                alien.rect.x = 157 + (column * 50)
                alien.rect.y = self.alienPosition + (row * 45)
                aliens.add(alien)

        self.aliens = aliens

    def make_aliens_shoot(self):
        if (time.get_ticks() - self.timer) > 700 and self.aliens:
            alien = self.aliens.random_bottom()
            self.alien_bullets.add(Bullet(alien.rect.x + 14, alien.rect.y + 20, 1, 5, 'enemylaser', 'center'))
            self.allSprites.add(self.alien_bullets)
            self.timer = time.get_ticks()

    def calculate_score(self, row):
        scores = {0: 30, 1: 20, 2: 20, 3: 10, 4: 10, 5: choice([50, 100, 150, 300])}
        score = scores[row]
        self.score += score
        return score

    def create_main_menu(self):
        self.alien1 = images_load_files['alien00']
        self.alien2 = images_load_files['alien10']
        self.alien3 = images_load_files['alien20']
        self.ufo_image = images_load_files['ufo']
        self.alien1 = transform.scale(self.alien1, (50, 50))
        self.alien2 = transform.scale(self.alien2, (50, 50))
        self.alien3 = transform.scale(self.alien3, (50, 50))
        self.ufo_image = transform.scale(self.ufo_image, (70, 40))
        game.screen.blit(self.alien1, (318, 270))
        game.screen.blit(self.alien2, (318, 320))
        game.screen.blit(self.alien3, (318, 370))
        game.screen.blit(self.ufo_image, (299, 420))

    def check_collisions(self):
        sprite.groupcollide(self.bullets, self.alien_bullets, True, True)

        for alien in sprite.groupcollide(self.aliens, self.bullets, True, True).keys():
            self.sounds['invaderkilled'].play()
            self.calculate_score(alien.row)
            AlienExplosion(alien, self.explosion_group)
            self.game_timer = time.get_ticks()

        for ufo in sprite.groupcollide(self.ufo_group, self.bullets, True, True).keys():
            ufo.ufoEncountered.stop()
            self.sounds['mysterykilled'].play()
            score = self.calculate_score(ufo.row)
            UfoDie(ufo, score, self.explosion_group)
            new_ship = UFO()
            self.allSprites.add(new_ship)
            self.ufo_group.add(new_ship)

        for player in  sprite.groupcollide(self.player_object_group, self.alien_bullets, True, True).keys():
            if self.ship_life3.alive():
                self.ship_life3.kill()
            elif self.ship_life2.alive():
                self.ship_life2.kill()
            elif self.ship_life1.alive():
                self.ship_life1.kill()
            else:
                self.gameOver = True
                self.startGame = False
            self.sounds['shipexplosion'].play()
            ShipExplosion(player, self.explosion_group)
            self.make_new_ship = True
            self.ship_timer = time.get_ticks()
            self.ship_alive = False

        if self.aliens.bottom >= 540:
            sprite.groupcollide(self.aliens, self.player_object_group, True, True)
            if not self.player_object.alive() or self.aliens.bottom >= 600:
                self.gameOver = True
                self. startGame = False

        sprite.groupcollide(self.bullets, self.allBarriers, True, True)
        sprite.groupcollide(self.alien_bullets, self.allBarriers, True, True)
        if self.aliens.bottom >= barrier_position:
            sprite.groupcollide(self.aliens, self.allBarriers, False, True)

    def create_new_ship(self, create_ship, current_time):
        if create_ship and (current_time - self.ship_timer > 900):
            self.player_object = Ship()
            self.allSprites.add(self.player_object)
            self.player_object_group.add(self.player_object)
            self.make_new_ship = False
            self.ship_alive = True

    def create_game_over(self, current_time):
        self.screen.blit(self.background, (0, 0))
        passed = current_time - self.timer
        if passed < 750:
            self.game_over_text.draw(self.screen)
        elif 750 < passed < 1500:
            self.screen.blit(self.background, (0, 0))
        elif 1500 < passed < 2250:
            self.game_over_text.draw(self.screen)
        elif 2250 < passed < 2750:
            self.screen.blit(self.background, (0, 0))
        elif passed > 3000:
            self.mainScreen = True

        for e in event.get():
            if self.should_exit(e):
                sys.exit()

    def main(self):
        pygame.font.init()
        while True:
            if self.mainScreen:
                self.screen.blit(self.background, (0, 0))
                self.title_text.draw(self.screen)
                self.title_text2.draw(self.screen)
                self.alien1_text.draw(self.screen)
                self.alien2_text.draw(self.screen)
                self.alien3_text.draw(self.screen)
                self.alien4_text.draw(self.screen)
                self.create_main_menu()
                for e in event.get():
                    if self.should_exit(e):
                        sys.exit()
                    if e.type == KEYUP:
                        self.allBarriers = sprite.Group(self.make_barriers(0), self.make_barriers(1),
                                                        self.make_barriers(2), self.make_barriers(3))
                        self.ship_life_group.add(self.ship_life1, self.ship_life2, self.ship_life3)
                        self.reset(0)
                        self.startGame = True
                        self.mainScreen = False
            elif self.startGame:
                if not self.aliens and not self.explosion_group:
                    current_time = time.get_ticks()
                    if current_time - self.game_timer < 3000:
                        self.screen.blit(self.background, (0, 0))
                        self.score_text2 = Text(20, str(self.score), green, 85, 5)
                        self.score_text.draw(self.screen)
                        self.score_text2.draw(self.screen)
                        self.next_round_text.draw(self.screen)
                        self.lives_text.draw(self.screen)
                        self.ship_life_group.update()
                        self.check_input()
                    if current_time - self.game_timer > 3000:
                        self.alienPosition += alien_move_down
                        self.reset(self.score)
                        self.game_timer += 3000
                else:
                    current_time = time.get_ticks()
                    self.play_main_music(current_time)
                    self.screen.blit(self.background, (0, 0))
                    self.allBarriers.update(self.screen)
                    self.score_text2 = Text(20, str(self.score), green, 85, 5)
                    self.score_text.draw(self.screen)
                    self.score_text2.draw(self.screen)
                    self.lives_text.draw(self.screen)
                    self.check_input()
                    self.aliens.update(current_time)
                    self.allSprites.update(self.keys, current_time)
                    self.explosion_group.update(current_time)
                    self.check_collisions()
                    self.create_new_ship(self.make_new_ship, current_time)
                    self.make_aliens_shoot()

            elif self.gameOver:
                current_time = time.get_ticks()
                self.alienPosition = alien_default_position
                self.create_game_over(current_time)

            display.update()
            self.clock.tick(60)


if __name__ == '__main__':
    game = Game()
    game.main()