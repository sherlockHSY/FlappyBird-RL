from itertools import cycle
import random
import sys
import pygame
from pygame.locals import *

"""
The Flappy Bird Environment. The interface imitates the style of the environment module in gym.
Fork from https://github.com/sourabhv/FlapPyBird .Based on this code.

Flappy Bird 环境
接口格式仿照gym中环境模块的风格
基于 https://github.com/sourabhv/FlapPyBird 修改
"""


# 全局参数
FPS = 30
SCREENWIDTH = 288
SCREENHEIGHT = 512
# amount by which base can maximum shift to left
PIPEGAPSIZE = 100  # gap between upper and lower part of pipe
BASEY = SCREENHEIGHT * 0.79

# list of all possible players (tuple of 3 positions of flap)
PLAYERS_LIST = (
    # red bird
    (
        'assets/sprites/redbird-upflap.png',
        'assets/sprites/redbird-midflap.png',
        'assets/sprites/redbird-downflap.png',
    ),
    # blue bird
    (
        'assets/sprites/bluebird-upflap.png',
        'assets/sprites/bluebird-midflap.png',
        'assets/sprites/bluebird-downflap.png',
    ),
    # yellow bird
    (
        'assets/sprites/yellowbird-upflap.png',
        'assets/sprites/yellowbird-midflap.png',
        'assets/sprites/yellowbird-downflap.png',
    ),
)

# list of backgrounds
BACKGROUNDS_LIST = (
    'assets/sprites/background-day.png',
    'assets/sprites/background-night.png',
)

# list of pipes
PIPES_LIST = (
    'assets/sprites/pipe-green.png',
    'assets/sprites/pipe-red.png',
)


class FlappyBird(object):
    def __init__(self):
        super(FlappyBird).__init__()
        # global SCREEN, FPSCLOCK
        self.action_space = [0,1]
        
        pygame.init()
        self.FPSCLOCK = pygame.time.Clock()
        self.SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
        pygame.display.set_caption('Flappy Bird')
        # image, sound and hitmask  dicts
        self.IMAGES, self.SOUNDS, self.HITMASKS = {}, {}, {}
        # numbers sprites for score display
        self.IMAGES['numbers'] = (
            pygame.image.load('assets/sprites/0.png').convert_alpha(),
            pygame.image.load('assets/sprites/1.png').convert_alpha(),
            pygame.image.load('assets/sprites/2.png').convert_alpha(),
            pygame.image.load('assets/sprites/3.png').convert_alpha(),
            pygame.image.load('assets/sprites/4.png').convert_alpha(),
            pygame.image.load('assets/sprites/5.png').convert_alpha(),
            pygame.image.load('assets/sprites/6.png').convert_alpha(),
            pygame.image.load('assets/sprites/7.png').convert_alpha(),
            pygame.image.load('assets/sprites/8.png').convert_alpha(),
            pygame.image.load('assets/sprites/9.png').convert_alpha()
        )

        # game over sprite
        self.IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
        # message sprite for welcome screen
        self.IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
        # base (ground) sprite
        self.IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()
        
        # sounds
        self.play_flap_sound = False
        self.play_point_sound = False
        self.play_hit_sound = False
        if 'win' in sys.platform:
            soundExt = '.wav'
        else:
            soundExt = '.ogg'

        self.SOUNDS['die'] = pygame.mixer.Sound('assets/audio/die' + soundExt)
        self.SOUNDS['hit'] = pygame.mixer.Sound('assets/audio/hit' + soundExt)
        self.SOUNDS['point'] = pygame.mixer.Sound('assets/audio/point' + soundExt)
        self.SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
        self.SOUNDS['wing'] = pygame.mixer.Sound('assets/audio/wing' + soundExt)
        # 固定参数
        self.pipeVelX = -4
        self.playerMaxVelY = 10  # max vel along Y, max descend speed
        self.playerMinVelY = -8  # min vel along Y, max ascend speed
        self.playerAccY = 1  # players downward accleration
        self.playerRot = 45  # player's rotation
        self.playerVelRot = 3  # angular speed
        self.playerRotThr = 20  # rotation threshold
        self.playerVelY = -9  # player's velocity along Y, default same as playerFlapped
        self.playerFlapAcc = -9  # players speed on flapping
        self.playerFlapped = False  # True when player flaps

        # 初始坐标
        self.playerx = 0
        self.playery = 0
        self.basex = 0
        self.baseShift = 0
        
        # 这三个参数决定小鸟的翅膀会不会动
        self.loopIter = 0 
        self.playerIndex = 0
        self.playerIndexGen = cycle([0, 1, 2, 1])

        # 障碍物坐标
        self.upperPipes = []
        self.lowerPipes = []

        # 初始得分
        self.score = 0
        self.max_score = 0
        # crashInfo = mainGame(self.movementInfo)
        # showGameOverScreen(crashInfo)
    
    def seed(self,seed):
        random.seed(seed)
    
    def get_score(self):
        return self.score
    
    def get_max_score(self):
        return self.max_score
    
    # 渲染环境 Visual environment
    def render(self, turn_on_sound=False):
        if turn_on_sound:
            if self.play_flap_sound:
                self.SOUNDS['wing'].play()
            if self.play_point_sound:
                self.SOUNDS['point'].play()
            if self.play_hit_sound:
                self.SOUNDS['hit'].play()
            
            self.play_point_sound = False
            self.play_hit_sound = False
            self.play_flap_sound = False

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
        # draw sprites
        self.SCREEN.blit(self.IMAGES['background'], (0, 0))

        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            self.SCREEN.blit(self.IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            self.SCREEN.blit(self.IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        self.SCREEN.blit(self.IMAGES['base'], (self.basex, BASEY))
        
        self.showScore(self.score)

        # Player rotation has a threshold
        visibleRot = self.playerRotThr
        if self.playerRot <= self.playerRotThr:
            visibleRot = self.playerRot
        playerSurface = pygame.transform.rotate(self.IMAGES['player'][self.playerIndex], visibleRot)
        # playerSurface = self.IMAGES['player'][self.playerIndex]
        self.SCREEN.blit(playerSurface, (self.playerx, self.playery))

        pygame.display.update()
        self.FPSCLOCK.tick(FPS) 

    # 初始化环境，并返回初始状态
    def reset(self):
        # select random background sprites
        randBg = random.randint(0, len(BACKGROUNDS_LIST) - 1)
        self.IMAGES['background'] = pygame.image.load(BACKGROUNDS_LIST[randBg]).convert()
        # select random player sprites
        randPlayer = random.randint(0, len(PLAYERS_LIST) - 1)
        self.IMAGES['player'] = (
            pygame.image.load(PLAYERS_LIST[randPlayer][0]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][1]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][2]).convert_alpha(),
        )

        # select random pipe sprites
        pipeindex = random.randint(0, len(PIPES_LIST) - 1)
        self.IMAGES['pipe'] = (
            pygame.transform.rotate(pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(), 180),
            pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(),
        )

        # hismask for pipes
        self.HITMASKS['pipe'] = (
            getHitmask(self.IMAGES['pipe'][0]),
            getHitmask(self.IMAGES['pipe'][1]),
        )

        # hitmask for player
        self.HITMASKS['player'] = (
            getHitmask(self.IMAGES['player'][0]),
            getHitmask(self.IMAGES['player'][1]),
            getHitmask(self.IMAGES['player'][2]),
        )

        self.loopIter = 0
        self.score = 0
        self.playerIndex = 0

        # 初始坐标
        self.playerx = int(SCREENWIDTH * 0.2)
        self.playery = int((SCREENHEIGHT - self.IMAGES['player'][0].get_height()) / 2)
        self.playerIndexGen = cycle([0, 1, 2, 1])
        
        self.basex = 0
        self.baseShift = self.IMAGES['base'].get_width() - self.IMAGES['background'].get_width()

        # get 2 new pipes to add to upperPipes lowerPipes list 上下两个障碍物
        newPipe1 = self.getRandomPipe()
        newPipe2 = self.getRandomPipe()

        # list of upper pipes
        self.upperPipes = [
            {'x': SCREENWIDTH + 100, 'y': newPipe1[0]['y']},
            {'x':  SCREENWIDTH + 100 + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
        ]

        # list of lowerpipe
        self.lowerPipes = [
            {'x': SCREENWIDTH + 100, 'y': newPipe1[1]['y']},
            {'x': SCREENWIDTH + 100 + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
        ]
        
        self.playerVelY = -9
        self.playerFlapped = False


        # state = self.transform2state(playerx, playery, self.playerVelY, lowerPipes, upperPipes)
        observation = [self.playerx, self.playery, self.playerVelY, self.lowerPipes, self.upperPipes]
        return observation

    def checkCrash(self,):
        """Returns True if player collders with base or pipes."""
        player = {'x': self.playerx, 'y': self.playery, 'index': self.playerIndex}
        pi = player['index']
        player['w'] = self.IMAGES['player'][0].get_width()
        player['h'] = self.IMAGES['player'][0].get_height()

        # if player crashes into ground
        if player['y'] + player['h'] >= BASEY - 1:
            return [True, True]
        else:
            playerRect = pygame.Rect(player['x'], player['y'],
                                    player['w'], player['h'])
            pipeW = self.IMAGES['pipe'][0].get_width()
            pipeH = self.IMAGES['pipe'][0].get_height()

            for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
                # upper and lower pipe rects
                uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
                lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)

                # player and upper/lower pipe hitmasks
                pHitMask = self.HITMASKS['player'][pi]
                uHitmask = self.HITMASKS['pipe'][0]
                lHitmask = self.HITMASKS['pipe'][1]

                # if bird collided with upipe or lpipe
                uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
                lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

                if uCollide or lCollide:
                    return [True, False]

        return [False, False]
    
    # 环境交互 Interact with the environment
    def step(self,action):
        
        done = False
        # 定义reward，小鸟活着就是0，挂了就是-1000 live:0, die:-1000
        reward = 0
        if action:
            # action==0 无动作，action==1 往上跳了一下 flap
            if self.playery > -2 * self.IMAGES['player'][0].get_height():
                self.playerVelY = self.playerFlapAcc
                self.playerFlapped = True
                self.play_flap_sound = True
        
        # 检查是否碰到障碍物，碰到，游戏结束；没碰到，更新得分
        crashTest = self.checkCrash()
        if crashTest[0]:
            self.play_hit_sound = True
            reward = -1000         
            state_ = 'terminal'
            done = True
            return state_, reward, done

        # 计算得分 check for score
        playerMidPos = self.playerx + self.IMAGES['player'][0].get_width() / 2
        for pipe in self.upperPipes:
            pipeMidPos = pipe['x'] + self.IMAGES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                self.score += 1
                self.play_point_sound = True

        if self.score > self.max_score:
            self.max_score = self.score
        
        # 更新环境，也就是更新小鸟和障碍物的位置 update environment
        if (self.loopIter + 1) % 3 == 0: # 这个就是让翅膀的图片交替变换，产生摆动的效果
            self.playerIndex = next(self.playerIndexGen)
        self.loopIter = (self.loopIter + 1) % 30
        self.basex = -((-self.basex + 100) % self.baseShift)
        
        # rotate the player
        if self.playerRot > -90:
            self.playerRot -= self.playerVelRot

        # player's movement
        if self.playerVelY < self.playerMaxVelY and not self.playerFlapped:
            self.playerVelY += self.playerAccY
        if self.playerFlapped:
            self.playerFlapped = False
            # more rotation to cover the threshold (calculated in visible rotation)
            self.playerRot = 45

        playerHeight = self.IMAGES['player'][self.playerIndex].get_height()
        self.playery += min(self.playerVelY, BASEY - self.playery - playerHeight)

        # move pipes to left
        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            uPipe['x'] += self.pipeVelX
            lPipe['x'] += self.pipeVelX

        # add new pipe when first pipe is about to touch left of screen
        if  0 < self.upperPipes[0]['x'] < 5:
            newPipe = self.getRandomPipe()
            self.upperPipes.append(newPipe[0])
            self.lowerPipes.append(newPipe[1])

        # remove first pipe if its out of the screen
        if  self.upperPipes[0]['x'] < -self.IMAGES['pipe'][0].get_width():
            self.upperPipes.pop(0)
            self.lowerPipes.pop(0)


        observation_ = [self.playerx,self.playery,self.playerVelY, self.lowerPipes,self.upperPipes]
        
        return observation_, reward, done


    def getRandomPipe(self):
        """Returns a randomly generated pipe"""
        # y of gap between upper and lower pipe
        gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
        gapY += int(BASEY * 0.2)
        pipeHeight = self.IMAGES['pipe'][0].get_height()
        pipeX = SCREENWIDTH + 10
        
        return [
            {'x': pipeX, 'y': gapY - pipeHeight},  # upper pipe
            {'x': pipeX, 'y': gapY + PIPEGAPSIZE},  # lower pipe
        ]

    def showScore(self,score):
        """Displays score in center of screen"""
        scoreDigits = [int(x) for x in list(str(score))]
        totalWidth = 0  # total width of all numbers to be printed

        for digit in scoreDigits:
            totalWidth += self.IMAGES['numbers'][digit].get_width()

        Xoffset = (SCREENWIDTH - totalWidth) / 2
        for digit in scoreDigits:
            self.SCREEN.blit(self.IMAGES['numbers'][digit], (Xoffset, SCREENHEIGHT * 0.1))
            Xoffset += self.IMAGES['numbers'][digit].get_width()

    def transform2state(self, x, y, vel, pipe_low, pipe_upper):
        pipe_height = self.IMAGES['pipe'][0].get_height()
        pipe_width = self.IMAGES['pipe'][0].get_width()
        
        pipe_low_0,pipe_low_1 = pipe_low[0],pipe_low[1]
        
        if pipe_low[0]['x'] - x <= -pipe_width:
            pipe_low_0 = pipe_low[1]
            if len(pipe_low) > 2:
                pipe_low_1 = pipe_low[2]

        x0 = pipe_low_0['x'] - x 
        y0_l =pipe_low_0['y'] - y # 大于0说明小鸟在low pipe的上方
        y0_u = (pipe_height + pipe_upper[0]['y']) - y # 小于0说明小鸟在upper pipe的下方
        
        if -50 < x0 <= 0:
            y0_u = pipe_low_1["y"] - y
        else:
            y0_u = 0

        # Evaluate player position compared to pipe
        if x0 < -40:
            x0 = int(x0)
        elif x0 < 140:
            x0 = int(x0) - (int(x0) % 10)
        else:
            x0 = int(x0) - (int(x0) % 70)

        if -180 < y0_l < 180:
            y0_l = int(y0_l) - (int(y0_l) % 10)
        else:
            y0_l = int(y0_l) - (int(y0_l) % 60)

        if -180 < y0_u < 180:
            y0_u = int(y0_u) - (int(y0_u) % 10)
        else:
            y0_u = int(y0_u) - (int(y0_u) % 60)

        return [x0, y0_l, y0_u, vel]


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in range(rect.width):
        for y in range(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False


def getHitmask(image):
    """Returns a hitmask using an image's alpha."""
    mask = []
    for x in range(image.get_width()):
        mask.append([])
        for y in range(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask

def playerShm(playerShm):
    """oscillates the value of playerShm['val'] between 8 and -8"""
    if abs(playerShm['val']) == 8:
        playerShm['dir'] *= -1

    if playerShm['dir'] == 1:
        playerShm['val'] += 1
    else:
        playerShm['val'] -= 1

    