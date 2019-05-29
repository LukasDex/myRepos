import sys, pygame
import random
import math
import socket
import _thread
import ast
import time

pygame.init()


class ParentObject():
    def __init__(self, speed, name, x, y):
        self.speed = speed
        self.name = name
        self.rect = self.currentPhoto.get_rect()
        self.rect.centery = y
        self.rect.centerx = x
        self.canMove = True
        self.isSent = False
        self.id = id(self)
        self.status = "newObj"


class Object(ParentObject):
    def __init__(self, speed, name, x, y, photoPath, creator, direction=[1, 0], colliding=False):
        self.creator = creator
        self.direction = direction
        self.x = x
        self.y = y
        self.path = photoPath
        self.currentPhoto = pygame.image.load(photoPath)
        super().__init__(speed, name, x, y)
        self.direction[0] = self.direction[0] * self.speed
        self.direction[1] = self.direction[1] * self.speed
        self.isColliding = colliding

    def getDirection(self):
        return 'a'

    def move(self):
        self.x = self.x + self.direction[0]
        self.y = self.y + self.direction[1]
        self.rect.centerx = self.x
        self.rect.centery = self.y


class Player(ParentObject):
    def __init__(self, speed, name, x, y):
        self.direction = [0, 0]
        self.isColliding = True
        self.pics = {"front": [], "rear": [], "right": [], "left": []}
        for key in self.pics.keys():
            for i in range(1, 5):
                self.pics[key].append(pygame.image.load("photos/{}_{}_{}.png".format(name, key, i)))
        self.currentPhoto = self.pics["front"][0]
        super().__init__(speed, name, x, y)
        self.rect.width -= 9
        self.hp = 5
        self.path = "photos/{}_{}_{}.png".format(name, 'front', 1)

    def getDirection(self):
        if self.direction[1] > 0:
            return 'front'
        elif self.direction[1] < 0:
            return 'rear'
        elif self.direction[0] > 0:
            return 'right'
        elif self.direction[0] < 0:
            return 'left'
        return 'front'

    def setDirection(self, x, y):
        self.direction = [x, y]

    def move(self, dir, value):
        self.direction[dir] += value * self.speed

    def wystrzel(self, Game, pos):
        angle = math.atan2((self.rect.centery - pos[1]), (self.rect.centerx - pos[0])) * 180 / math.pi
        y = -math.sin(math.pi * angle / 180)
        x = -math.cos(math.pi * angle / 180)
        Game.newObject(10, 'EnergyBlast', self.rect.centerx, self.rect.centery, 'photos/EnergyBlast.png', self,
                       [x, y])


class Game():
    def __init__(self):
        self.gameObjects = []
        self.bground_photo = pygame.image.load('photos/bground.png')
        self.bground_rect = self.bground_photo.get_rect()
        self.size = self.bground_rect.width, self.bground_rect.height
        self.white = 255, 255, 255
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("First Game")
        self.clock = pygame.time.Clock()
        self.currentID = 0
        self.action = None
        self.run = True
        self.numberofPlayers = 0
        self.maxPlayers = 2
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = socket.gethostname()
        print(host)
        port = 9998
        self.serversocket.bind((host, port))
        self.serversocket.listen(5)
        self.bufferSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bufferSocket.bind((host, 9999))
        self.bufferSocket.listen(5)
        self.locker = _thread.allocate_lock()
        self.clientLists = []
        # _thread.start_new_thread(self.listen_for_new_players, ())

    def startGame(self):
        info1 = []
        info2 = []
        msg = 'Witaj! Wybierz liczbe graczy od 1 do 4!'
        hostrecv = True
        while self.maxPlayers != self.numberofPlayers:
            clientsocket, addr = self.serversocket.accept()
            bufferSocket, addr2 = self.bufferSocket.accept()
            info1.append((bufferSocket, addr2))
            info2.append((self.currentID, clientsocket, addr))

            clientsocket.send(msg.encode('ascii'))
            if hostrecv:
                hostrecv = False
                msg = 'Witaj! Napisz cokolowiek zeby kontynuowac!'
                numberofPlayers = clientsocket.recv(1024).decode('ascii')
                self.maxPlayers = int(numberofPlayers)
            else:
                clientsocket.recv(1024).decode('ascii')

            self.currentID += 1
            self.numberofPlayers += 1

        for i in range(self.numberofPlayers):
            self.gameObjects.append(Player(4, 'dark_knight', i * 600 + 200, 100))

        time.sleep(0.5)

        i = 0
        for inf1, inf2 in zip(info1, info2):
            _thread.start_new_thread(self.send_info, inf1)
            _thread.start_new_thread(self.receive_info, inf2)
            i += 1

    def send_info(self, clientsocket, addr):
        while 1:
            msg = ''
            for obj in self.gameObjects:
                # name, photopath, rect.centerx, rect.centery
                msg += obj.name
                msg += '}'
                msg += obj.path
                msg += '}'
                msg += str(obj.rect.centerx)
                msg += '}'
                msg += str(obj.rect.centery)
                msg += '}'
            print(msg)
            clientsocket.send(msg.encode('ascii'))
            print("ABC")
            clientsocket.recv(1024).decode('ascii')

    def receive_info(self, ID, clientsocket, addr):
        clientsocket, addr = clientsocket, addr
        while 1:
            action = clientsocket.recv(1024).decode('ascii')
            self.playerAction(action, ID)
        clientsocket.close()

    def redrawGameWindow(self):
        self.screen.blit(self.bground_photo, self.bground_rect)
        for obj in self.gameObjects:
            if obj.name == 'dark_knight':
                if obj.direction != [0, 0]:
                    ran = random.randint(0, 3)
                    obj.path = "photos/{}_{}_{}.png".format(obj.name, obj.getDirection(), ran + 1)
                    obj.currentPhoto = obj.pics[obj.getDirection()][ran]
        for i in self.gameObjects:
            self.screen.blit(i.currentPhoto, i.rect)

    def move(self):
        for obj in self.gameObjects:
            if (obj.direction != [0, 0]):
                if obj.name == 'EnergyBlast':
                    if self.checkWalls(obj.rect) == False:
                        # self.locker.acquire()
                        if obj.isSent:
                            obj.status = 'remove'
                        self.gameObjects.remove(obj)
                        # self.locker.release()
                        continue
                    obj.move()
                    continue
                directP = [obj.direction[0], obj.direction[1]]
                for obj2 in self.gameObjects:
                    if obj != obj2 and self.colliding(obj.rect.move(obj.direction), obj2.rect):
                        d = self.directionPossibility(obj, obj2)
                        directP[0] = directP[0] + d[0]
                        directP[1] = directP[1] + d[1]
                if self.checkWalls(obj.rect.move(obj.direction)):
                    obj.rect = obj.rect.move(directP)

    def newObject(self, speed, name, x, y, photoPath, creator, dir=[0, 0]):
        self.gameObjects.append(Object(speed, name, x, y, photoPath, creator, dir))

    def directionPossibility(self, obj, obj2):
        directions = [0, 0]
        directions2 = [0, 0]
        directions2[0] = obj.direction[0]
        if self.colliding(obj.rect.move(directions2), obj2.rect):
            directions[0] = -obj.direction[0]
        directions2 = [0, 0]
        directions2[1] = obj.direction[1]
        if self.colliding(obj.rect.move(directions2), obj2.rect):
            directions[1] = -obj.direction[1]
        return directions

    def colliding(self, rect1, rect2):
        if math.fabs(rect1.centerx - rect2.centerx) < (rect1.width + rect2.width) / 2 and math.fabs(
                rect1.centery - rect2.centery) < (rect1.height + rect2.height) / 2:
            return True
        return False

    def checkWalls(self, rect):
        if math.fabs(rect.top < 55 or rect.bottom > 750 or rect.left < 58 or rect.right > 1065):
            return False
        return True

    def playerAction(self, msg, ID=0):
        if msg == 'DDOWN':
            self.gameObjects[ID].move(1, 1)
        if msg == 'DLEFT':
            self.gameObjects[ID].move(0, -1)
        if msg == 'DRIGHT':
            self.gameObjects[ID].move(0, 1)
        if msg == 'DUP':
            self.gameObjects[ID].move(1, -1)

        if msg == 'UDOWN':
            self.gameObjects[ID].move(1, -1)
        if msg == 'ULEFT':
            self.gameObjects[ID].move(0, 1)
        if msg == 'URIGHT':
            self.gameObjects[ID].move(0, -1)
        if msg == 'UUP':
            self.gameObjects[ID].move(1, 1)
        if msg == 'QUIT':
            self.gameObjects.pop(ID)
        if msg[:3] == 'pos':  # strzał
            msg = ast.literal_eval(msg[3:])
            self.gameObjects[ID].wystrzel(self, (msg[0], msg[1]))

    def collision(self):
        for obj in self.gameObjects:
            for obj2 in self.gameObjects:
                if obj == obj2:
                    continue
                else:
                    if self.colliding(obj.rect, obj2.rect):
                        if obj.name == 'EnergyBlast' and obj2.name == 'dark_knight':
                            if obj.creator != obj2:
                                # self.locker.acquire()
                                if obj.isSent:
                                    obj.status = 'remove'
                                self.gameObjects.remove(obj)
                                # self.locker.release()
                                obj2.hp -= 1
                                if obj2.hp == 0:
                                    self.gameObjects.remove(obj2)
                                    obj2.status = 'remove'

                                continue
                        if obj.name == 'dark_knight' and obj2.name == 'EnergyBlast':
                            if obj2.creator != obj:
                                # self.locker.acquire()
                                if obj2.isSent:
                                    obj2.status = 'remove'
                                self.gameObjects.remove(obj2)
                                # self.locker.release()
                                obj.hp -= 1
                                if obj.hp == 0:
                                    self.gameObjects.remove(obj)
                                    obj.status = 'remove'

                                continue

    def begin(self):
        self.startGame()
        while self.run:
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False

            self.move()
            self.screen.fill(self.white)
            self.redrawGameWindow()
            self.collision()

            pygame.display.flip()


p = Game()
p.begin()
pygame.quit()
