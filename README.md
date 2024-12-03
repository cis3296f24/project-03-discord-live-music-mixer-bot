# JockeyBot

**JockeyBot** is a Discord music bot that offers a customized listening experience with various audio effects and support for multiple streaming services.

---

## Features
- Play music from YouTube and other streaming services.
- Queue system for managing multiple tracks.
- Audio effects including reversal, speed adjustment, flangers, gain, reverb, and high/low pass filters.
- Mashup feature to automatically lock the BPM of one track to another.
- Customizable command prefix (default is `,`).

---

## Requirements
- Python 3.8 or higher
- FFmpeg installed and added to PATH
- Discord Bot Token

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jockeybot.git
   cd jockeybot
   
1. Install the packages:
   ```bash
   pip install -r requirements.txt

Create a file named discordkey.txt in the root directory and paste your Discord Bot Token inside.

Ensure FFmpeg is installed and added to your system's PATH.

## Usage
Run the bot using:

| Command         | Description                                                |
|-----------------|------------------------------------------------------------|
| `,join`         | Join the user's voice channel                              |
| `,leave`        | Leave the current voice channel                            |
| `,play <url>`    | Add a YouTube video to the queue and start playing if not already |
| `,pause`        | Pause the current track                                    |
| `,unpause`      | Resume the paused track                                    |
| `,skip`         | Skip the current track and play the next in queue          |
| `,gain <value>` | Adjust the gain of the current track                   |
| `,lowpass <frequency>` | Apply a low-pass filter to the current track        |
| `,highpass <frequency>` | Apply a high-pass filter to the current track      |
| `,pitchshift <semitones>` | Adjust the pitch of the current track            |
| `,normalize`    | Normalize the audio of the current track                   |
| `,pan <value>`  | Adjust the stereo panning of the current track
| `,highend <value>`  | Boosts the high-end signals in a track (hi-hats, snares, etc)
| `,lowend <value>`  | Boosts the low-end signals in a track (basslines, kicks, 808s, etc)
| `,reverb <decay>, <delay>`  | Creates a reverb-like effect using input params for decay and delay
| `,undo`  | Boosts the high-end signals in a track (hi-hats, snares, etc)





## Contributing

- Fork the repository.
- Create a new branch for your feature.
- Commit your changes.
- Push to your branch.
- Create a pull request.
