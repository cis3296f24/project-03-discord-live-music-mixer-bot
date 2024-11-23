
class Song:
    #simple class to keep track of song info, stored in FIFO queue
    def __init__(self, title:str, path:str, url:str):
        self.title = title      # Title of the Song on Youtube
        self.path = path        # Users local path referencing the downloaded Song placed inside their local folder as a result of calling ".play [URL]" 
        self.url = url          # Youtube URL for the Song. This URL is parsed by Youtube DL

    #getter
    def __str___(self):
        return f"{self.title, self.path, self.url}"