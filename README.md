<p align="center">
  <img src="assets/chip-source.png" alt="Chip" width="40%" align="middle">
  <img src="assets/capri.png" alt="Capri" width="40%" align="middle">
</p>

Bring Capri (back lol) to life as a desktop companion! Inspired by jpartnma_'s tiktok video.

Beware that Capri may try to take over your human CPU. We take no responsibility for her actions.

To download it just click on the release in the right hand corner and click capri-setup.exe!

To compile it yourself, make sure you have the following installed: .NET 8.0 SDK and run "dotnet build app\Capri.csproj --configuration Release" in the root directory of the project. The compiled .exe will be located in app\bin\Release\net8.0-windows\win-x64\publish\.

## Optional local Whisper input

The **Use local Whisper input** option uses a local Python server to transcribe microphone input. Python is not required for the rest of Capri.

On Windows, install Python 3.10 or newer and FFmpeg. Make sure `ffmpeg.exe` is available on `PATH`, then run these commands from the repository root:

```powershell
py -3 -m venv .venv-whisper
.\.venv-whisper\Scripts\python.exe -m pip install --upgrade pip
.\.venv-whisper\Scripts\python.exe -m pip install fastapi uvicorn faster-whisper numpy python-multipart
```

Build and run Capri from the repository checkout so it can find `whisper_server.py`:

```powershell
dotnet build app\Capri.csproj --configuration Release
.\app\bin\Release\net8.0-windows\Capri.exe
```

The first time local Whisper is used, `faster-whisper` downloads the `base` speech model. The default configuration runs on the CPU using `int8`. To use a different Python executable, set `CAPRI_WHISPER_PYTHON` before starting Capri:

```powershell
$env:CAPRI_WHISPER_PYTHON = "C:\path\to\python.exe"
```

Have fun and more updates to come!

Features I'd like to add:

- Tray application
- Voice lines (with mute)
- Text bubbles?
- Possibility to connect local LLM for conversations
- More animations, images &amp; quirks
- Head pats (smh)
- Mischief mode (screen glitches, stealing your cursor, "you've been hacked" notes)
- Sitting on top of your windows
- Peeking from the edge of the screen when you're idle
- Start with Windows
- Hiding while you're in fullscreen games or videos
- Alarms &amp; a study timer