

class Position:
    x = 0
    y = 0
    def __init__(self, x:int=0, y:int=0) -> None:
        self.x = x
        self.y = y

    def getX(self):
        return self.x

    def getY(self):
        return self.y