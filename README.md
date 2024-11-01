![Seeed](https://img.shields.io/badge/Seeed-ReSpeaker-brightgreen)
![ReSpeaker](https://img.shields.io/badge/ReSpeaker-2--Mic%20Pi%20HAT-blue)
![Voice Card](https://img.shields.io/badge/Voice%20Card-seeed--2mic--voicecard-orange)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-brightgreen.svg)
![Linux](https://img.shields.io/badge/Linux-6.6.51%2B-orange.svg)
![Vosk](https://img.shields.io/badge/Vosk-Offline%20ASR-yellow.svg)
![PyAudio](https://img.shields.io/badge/PyAudio-0.2.11-lightgrey.svg)
![NumPy](https://img.shields.io/badge/NumPy-1.21%2B-red.svg)

---

# Seeed ReSpeaker Speech-to-Text on Raspberry Pi

This repository provides a implementation for setting up and using Seeed's ReSpeaker (tested on 2-Mic) Pi HAT for a speech-to-text system on a Raspberry Pi 5. The project is tested on an updated Raspberry Pi 5 with Linux kernel 6.6.51+rpt-rpi-2712 and features Vosk's offline speech recognition. This project can be used as a starting point for further development with your Seeed voice card.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Classes and Key Functions](#classes-and-key-functions)
- [Diagnostics and Debugging](#diagnostics-and-debugging)
- [Troubleshooting](#troubleshooting)
- [Acknowledgments](#acknowledgments)

---

## Overview

This project configures and manages a ReSpeaker 2-Mics Pi HAT on a Raspberry Pi 5. It integrates Vosk’s ASR (automatic speech recognition) model for speech-to-text conversion. Key configurations and audio diagnostics help ensure optimal performance.

## Features

- **Speech Recognition (Vosk)**: Offline speech recognition using the Vosk library with automatic model download.
- **Voice Activity Detection (VAD)**: Efficient VAD thresholding for identifying spoken audio, minimizing false detections.
- **Diagnostics**: Real-time diagnostics for audio sample rate, CPU usage, and system performance.
- **Detailed Logging**: Configurable logging to assist in debugging and monitoring.
- **Automatic Device Setup**: Scans and configures ReSpeaker 2-Mics HAT or defaults to the available device if not detected.

## Requirements

- **Hardware**:
  - Raspberry Pi 5 (tested on this model)
  - Seeed ReSpeaker 2-Mics Pi HAT
  - SSD recommended for faster performance

- **Software**:
  - OS: Raspberry Pi OS Lite (64-bit)
  - Voice card installed https://github.com/Wartem/seeed-voicecard
  - Dependencies: Install via `requirements.txt` (detailed below)

### Python Packages

Install dependencies:
```bash
pip install -r requirements.txt
```

`requirements.txt` should contain:
```
# Basic audio processing
numpy
sounddevice
PyAudio

# Lightweight alternatives for speech recognition
vosk

# Async support
asyncio

# Audio processing
librosa

# Download files from the web
wget

# System and process utilities
psutil
```

## Setup

1. **Install Dependencies**:
    ```bash
    pip install pyaudio numpy vosk wget psutil
    ```

2. **Configure Audio Device**:
   Ensure the ReSpeaker 2-Mics Pi HAT is connected and identified as `hw:0,0`.

3. **Model Setup**:

   The Vosk ASR model is downloaded automatically by the `setup_vosk_model` function, which verifies the model path specified in `config.json` under `"MODEL_PATH"`. This path points to a local directory for storing the ASR model files. If the model is not already downloaded, the setup function will download it automatically.

   To use a different Vosk model, follow these steps:

   1. **Browse the Available Models**: Visit the [Vosk Model Repository](https://alphacephei.com/vosk/models) to see the list of available models. Models vary in language, size, and acoustic accuracy.
   
   2. **Select a Model**: Choose a model based on your language and performance requirements. Download links are provided for each model; make note of the model’s name and path.

   3. **Update `config.json`**:
      - Copy the path to the downloaded model, or note the model’s name for later download.
      - Open your `config.json` file.
      - Update the `"MODEL_PATH"` field with the chosen model’s path. For example:
        ```json
        "MODEL_PATH": "./vosk-models/vosk-model-small-en-us-0.15"
        ```

   4. **Save the Changes**: After updating the path in `config.json`, save the file. If the model is not yet downloaded, the `setup_vosk_model` function will handle the download when you start the application.

## Configuration

The default configuration file is `config.json`. On first run, the program creates this file if it does not exist.

**Key Configuration Options**:
- `MODEL_PATH`: Path to the Vosk model.
- `SAMPLE_RATE`: Set to `48000` for ReSpeaker 2-Mics HAT.
- `CHANNELS`: Set to `2` for stereo input.
- `CHUNK_SIZE`: Default to `8000`.
- `VAD_THRESHOLD`: Voice activity detection threshold, adjustable.
- `DEBUG_MODE`: Enables verbose logging for diagnostics.

## Usage

1. **Start the Program**:
   ```bash
   python main.py
   ```

2. **Real-Time Diagnostics**:
   When `DEBUG_MODE` is enabled, logs report on system diagnostics, CPU usage, and sample rates.

3. **Audio Processing**:
   Audio input is continuously processed and queued.

### Classes and Key Functions

- **LoggerConfig**:
  Centralizes logging configuration. `setup_logger` initializes the logger with `DEBUG` or `INFO` levels based on `debug_mode`.

- **AudioDiagnostics**:
  Tracks audio processing stats, including sample rate and CPU usage, updated every second in `debug_mode`.

- **ConfigManager**:
  Loads and validates configuration settings, merging with defaults. Handles JSON parsing errors.

- **AudioHandler**:
  Main handler for audio input, device setup, and VAD. Initializes Vosk, configures the ReSpeaker device, and processes audio.

- **setup_vosk_model(model_path: str)**:
  Ensures the Vosk model exists, downloading and extracting if not present.

## Diagnostics and Debugging

Diagnostics, available with `DEBUG_MODE`, offer insights into:
- **Sample Rate**: Expected vs. actual sample rates, helping identify audio buffer issues.
- **CPU Usage**: Real-time CPU metrics indicating potential bottlenecks.
- **VAD Threshold**: Adjust `VAD_THRESHOLD` based on environment.

### Enabling Debug Mode
In `config.json`, set `"DEBUG_MODE": true`.

## Troubleshooting

- **Device Not Recognized**:
  Ensure ReSpeaker 2-Mics HAT is connected and configured at `hw:0,0`.
  
- **Model Not Downloading**:
  Check internet connection, or manually download Vosk from [alphacephei.com/vosk/models](https://alphacephei.com/vosk/models) to `MODEL_PATH`.

- **Permission Errors**:
  Ensure the user has read/write access to the configuration and model directories.

- **High CPU Usage**:
  If CPU usage is high, consider disabling `DEBUG_MODE` and optimizing `VAD_THRESHOLD`.

---

## Acknowledgments

This project utilizes Seeed's ReSpeaker HAT, Vosk for offline ASR.