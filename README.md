---
title: EAC Translator
emoji: 🌍
colorFrom: indigo
colorTo: green
sdk: gradio
sdk_version: "5.35.0"
app_file: app.py
pinned: false
license: mit
---

# 🌍 EAC Translator

A multilingual translator for English, French, and Swahili with voice input and output. Built with ❤️ by [Eng. Jobbers – Qtrinova Inc](https://eng-jobbers.vercel.app/).

## ✨ Features

- 🎙️ Voice input via microphone
- 🧠 Automatic language detection
- 🔁 English ↔ French ↔ Swahili (with pivot logic)
- 🎛️ Tone control (Neutral, Formal, Casual, Romantic)
- 🔊 Text-to-speech with voice selection (David, Zira, etc.)
- 📱 Mobile-friendly UI
- 📤 Audio playback and download

## 🚀 Built With

- Gradio
- Hugging Face Transformers
- pyttsx3
- SpeechRecognition
- langid

## 📦 Installation (Optional for Local Use)

```bash
pip install -r requirements.txt
python app.py