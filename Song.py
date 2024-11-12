
class Song:
    #simple class to keep track of song info, stored in FIFO queue
    def __init__(self, title, link):
        self.title = title
        self.link = link

    #getter
    def __str___(self):
        return f"{self.title, self.link}"