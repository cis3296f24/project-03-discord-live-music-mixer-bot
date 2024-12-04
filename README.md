JOCKEYBOT 
This project will be a music bot for Discord that allows for an increasingly customized listening experience, such as audio reversal, increased/decreased playback speed, and other effects such as flangers, gain, reverb, and high/low pass filters. It will have a functional queue system and will support tracks across several streaming services to ensure an extensive music library will be available for all music tastes. It will also have a mashup feature, which will automatically lock the BPM of one track to another.
  

The most important class in this program will be a Player class which will wait for user input. It will frequently cite a Storage class which contains the tracks themselves, as well as a neighboring Web class dedicated to scraping the track from whichever streaming service is being requested (Soundcloud, Youtube, etc). Once the track is stored, it will be placed in the Storage queue if another track is playing, and it will be deleted as soon as the track is finished playing to save space. The storage class will operate in two loops; one will be dedicated to waiting for a track to be queued, and the other will allow users to queue for effects as a track plays. Most effects will have their own classes, however some effects (like playback speed or filtering) will be contained in the same class, assuming they accomplish essentially the same function in different directions. If the track queue loop in the Player class is quit, that will be the bot’s sign to leave the voice chat. That loop will effectively be the bot’s Main.

![This is a screenshot.](images.png)
# How to run
The binary provided in ./dist/ will have the latest version of the executable available. You need the token in a .txt file in the same 
directory as all of the files in the bot. Assuming you have both, you will be able to host the bot in your server!

Commands:

,join - Joins voice channel. Must be in a voice channel for this to work.

,leave - Leaves voice channel.

,get - Downloads a video from youtube and converts it to mp3. Adds it to the player queue and calls the player function.

,pause - Pauses the track that's currently playing.

,stop - Stops the track that's currently playing and moves on to the next track in the queue.

,fx - Adds effects to the currently-playing track. These will be in a separate file, and the list of available effects will be
provided in the ',help' command.

,help - Provides information on the bot's functionality and how to use it in the channel the command is called.

# How to contribute
Follow this project board to know the latest status of the project: [http://...]([http://...])  

### How to build
- Use this github repository: ... 
- Specify what branch to use for a more stable release or for cutting edge development.  
- Use InteliJ 11
- Specify additional library to download if needed 
- What file and target to compile and run. 
- What is expected to happen when the app start. 
