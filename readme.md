# Whisper for Windows by extensos

Whisper for Windows is a modern speech recognition application that uses OpenAI's Whisper model to transcribe speech in real-time. It features a sleek, interactive user interface with a multi-band frequency visualization.

## Features

- Real-time speech recognition using OpenAI's Whisper model
- Interactive multi-band frequency visualization
- Support for German language (easily adaptable to other languages)
- Copy transcribed text to clipboard
- Standalone executable for Windows (no Python installation required)

## Installation

1. Download the latest release from the [Releases](https://github.com/YourUsername/WhisperForWindows/releases) page.
2. Extract the ZIP file to a location of your choice.
3. Run `Whisper_for_Windows_by_extensos.exe`.

## Usage

1. Launch the application by running `Whisper_for_Windows_by_extensos.exe`.
2. Click the "Start Recording" button to begin capturing audio.
3. Speak into your microphone. The visualization will show the audio input in real-time.
4. Click "Stop Recording" when you're finished speaking.
5. The application will process your speech and display the transcribed text.
6. Use the "Copy Text" button to copy the transcription to your clipboard.

## Development

If you want to contribute to the development of Whisper for Windows, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/YourUsername/WhisperForWindows.git
   ```
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application in development mode:
   ```
   python speech_recognition_app.py
   ```

### Building the Executable

To build the standalone executable:

1. Ensure you have all dependencies installed:
   ```
   pip install -r requirements.txt
   ```
2. Run the build script:
   ```
   python build_app.py
   ```
3. The executable will be created in the `dist` folder.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for the Whisper speech recognition model
- PyQt6 for the graphical user interface
- FFmpeg for audio processing

