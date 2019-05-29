import sys, pygame
import random
import math
import socket
import _thread
import time

pygame.init()


class Object():
    def __init__(self, name, x, y, direction):
        self.name = name
        self.currentPhoto = pygame.image.load(direction)

        self.rect = self.currentPhoto.get_rect()
        self.rect.centerx = int(x)
        self.rect.centery = int(y)

    def updateObject(self, direction, centerx, centery):
        self.currentPhoto = pygame.image.load(direction)
        self.rect = self.currentPhoto.get_rect()
        self.rect.centerx = centerx
        self.rect.centery = centery


class Game():
    def __init__(self):
        self.bground_photo = pygame.image.load('photos/bground.png')
        self.bground_rect = self.bground_photo.get_rect()
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = socket.gethostname()
        self.port = 55555
        self.serversocket.connect((self.host, self.port))
        self.getterSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.getterSocket.connect((self.host, 55554))
        self.size = self.bground_rect.width, self.bground_rect.height
        self.white = 255, 255, 255
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("First Game")
        self.clock = pygame.time.Clock()
        self.run = True
        self.currentPlayer = 0
        self.gameObjects = []
        self.locker = _thread.allocate_lock()

    def getMsg(self):
        info = ['', '', '', '']
        msg = self.getterSocket.recv(1024*1024).decode('ascii')
        ind = 0
        info[0], info[1], info[2], info[3] = '', '', '', ''
        # name, photopath, rect.centerx, rect.centery
        self.gameObjects.clear()
        for char in msg:
            if char == '}':
                ind += 1
                if ind == 4:
                    #print(info)
                    self.gameObjects.append(Object(info[0], info[2], info[3], info[1]))
                    info[0], info[1], info[2], info[3] = '', '', '', ''
                    ind = 0
                continue
            info[ind] += char
        msg = "ready"
        self.getterSocket.send(msg.encode('ascii'))

    def sendMsg(self, msg):
        self.serversocket.send(msg.encode('ascii'))

    def redrawGameWindow(self):
        self.screen.blit(self.bground_photo, self.bground_rect)
        for obj in self.gameObjects:
            self.screen.blit(obj.currentPhoto, obj.rect)

    def checkEvents(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self.sendMsg("DDOWN")
                if event.key == pygame.K_LEFT:
                    self.sendMsg("DLEFT")
                if event.key == pygame.K_RIGHT:
                    self.sendMsg("DRIGHT")
                if event.key == pygame.K_UP:
                    self.sendMsg("DUP")
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    self.sendMsg("UDOWN")
                if event.key == pygame.K_LEFT:
                    self.sendMsg("ULEFT")
                if event.key == pygame.K_RIGHT:
                    self.sendMsg("URIGHT")
                if event.key == pygame.K_UP:
                    self.sendMsg("UUP")
            if event.type == pygame.QUIT:
                self.sendMsg("QUIT")
                self.run = False
            if event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                self.sendMsg('pos' + str(pos))

    def startGameClient(self):
        msg = self.serversocket.recv(1024).decode('ascii')
        print(msg)
        x = input()
        if msg == 'host' and int(x) not in range(1, 5):
            print('Liczba od 1 do 4!')
            while int(x) not in range(1, 5):
                x = input()
        self.serversocket.send(x.encode('ascii'))

    def begin(self):
        self.startGameClient()
        while self.run:
            self.clock.tick(60)
            self.checkEvents()
            self.getMsg()
            self.screen.fill(self.white)
            self.redrawGameWindow()
            pygame.display.flip()


p = Game()
p.begin()
p.s.close()
pygame.quit()
