import gradio as gr
from transformers import MarianMTModel, MarianTokenizer
from datetime import datetime
import langid
import os
import requests
import base64
import tempfile
import warnings

warnings.filterwarnings("ignore", message="Recommended: pip install sacremoses.")
langid.set_languages(['en', 'fr', 'sw'])

MODEL_MAP = {
    "English → Swahili": "Helsinki-NLP/opus-mt-en-sw",
    "English → French": "Helsinki-NLP/opus-mt-en-fr",
    "French → English": "Helsinki-NLP/opus-mt-fr-en",
    "French → Swahili (via English)": ["Helsinki-NLP/opus-mt-fr-en", "Helsinki-NLP/opus-mt-en-sw"]
}

TONE_MODIFIERS = {
    "Neutral": "",
    "Romantic": "Express this romantically: ",
    "Formal": "Translate this in a formal tone: ",
    "Casual": "Make this sound casual: "
}

loaded_models = {}

def load_model(model_name):
    if model_name not in loaded_models:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        loaded_models[model_name] = (tokenizer, model)
    return loaded_models[model_name]

def detect_language(text):
    try:
        lang, score = langid.classify(text)
        return lang
    except:
        return "unknown"

def translate(text, direction, tone):
    detected_lang = detect_language(text)
    expected_src = direction.split(" → ")[0].lower()
    warning = ""
    if expected_src.startswith("english") and detected_lang != "en":
        warning = f"⚠ Detected language is '{detected_lang}', but you selected English as source."
    elif expected_src.startswith("french") and detected_lang != "fr":
        warning = f"⚠ Detected language is '{detected_lang}', but you selected French as source."
    elif expected_src.startswith("swahili") and detected_lang != "sw":
        warning = f"⚠ Detected language is '{detected_lang}', but you selected Swahili as source."

    prompt = TONE_MODIFIERS[tone] + text
    model_info = MODEL_MAP[direction]

    if isinstance(model_info, list):
        tokenizer1, model1 = load_model(model_info[0])
        encoded1 = tokenizer1(prompt, return_tensors="pt", padding=True, truncation=True)
        intermediate = model1.generate(**encoded1)
        intermediate_text = tokenizer1.decode(intermediate[0], skip_special_tokens=True)

        tokenizer2, model2 = load_model(model_info[1])
        encoded2 = tokenizer2(intermediate_text, return_tensors="pt", padding=True, truncation=True)
        final = model2.generate(**encoded2)
        translation = tokenizer2.decode(final[0], skip_special_tokens=True)
    else:
        tokenizer, model = load_model(model_info)
        encoded = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
        generated = model.generate(**encoded)
        translation = tokenizer.decode(generated[0], skip_special_tokens=True)

    with open("translation_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {direction} | Tone: {tone}\n")
        f.write(f"Input: {text}\nOutput: {translation}\n\n")

    return f"{warning}\n{translation}" if warning else translation

# TTS using Hugging Face Inference API
def tts_via_api(text):
    api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not api_token:
        return None

    headers = {
        "Authorization": f"Bearer {api_token}"
    }

    payload = {
        "inputs": text
    }

    response = requests.post(
        "https://api-inference.huggingface.co/models/microsoft/speecht5_tts",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(response.content)
            return tmp.name
    else:
        return None

def transcribe_and_translate(audio_path, direction, tone):
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
        if len(audio.frame_data) < 10000:
            return "⚠ Audio too short or empty. Please try again."
        text = recognizer.recognize_google(audio)
        return translate(text, direction, tone)
    except Exception as e:
        return f"⚠ Could not transcribe audio: {e}"

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🌍 EAC Translator")
    gr.Markdown("Supports English, French, and Swahili. Includes tone control, language detection, voice input, and speech playback.")

    with gr.Tabs():
        with gr.Tab("📝 Text Translation"):
            with gr.Column():
                input_text = gr.Textbox(label="Text to Translate", lines=3)
                direction = gr.Dropdown(choices=list(MODEL_MAP.keys()), label="Translation Direction", value="English → Swahili")
                tone = gr.Radio(choices=list(TONE_MODIFIERS.keys()), label="Tone", value="Neutral")
                output_text = gr.Textbox(label="Translated Text", lines=3)
                with gr.Row():
                    translate_btn = gr.Button("Translate", scale=1)
                    speak_btn = gr.Button("🔊 Speak Translation", scale=1)
                audio_output = gr.Audio(label="Playback", interactive=False)

        with gr.Tab("🎙 Voice Translation"):
            with gr.Column():
                audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Speak Now")
                direction_voice = gr.Dropdown(choices=list(MODEL_MAP.keys()), label="Translation Direction", value="English → Swahili")
                tone_voice = gr.Radio(choices=list(TONE_MODIFIERS.keys()), label="Tone", value="Neutral")
                voice_output = gr.Textbox(label="Translated Text")
                with gr.Row():
                    voice_translate_btn = gr.Button("Transcribe & Translate", scale=1)
                    voice_speak_btn = gr.Button("🔊 Speak Translation", scale=1)
                audio_output2 = gr.Audio(label="Playback", interactive=False)

        translate_btn.click(fn=translate, inputs=[input_text, direction, tone], outputs=output_text)
        speak_btn.click(fn=tts_via_api, inputs=[output_text], outputs=audio_output)
        voice_translate_btn.click(fn=transcribe_and_translate, inputs=[audio_input, direction_voice, tone_voice], outputs=voice_output)
        voice_speak_btn.click(fn=tts_via_api, inputs=[voice_output], outputs=audio_output2)

    gr.Markdown(
        """<div style='text-align: center;'>
        <a href='https://eng-jobbers.vercel.app/' target='_blank' style='text-decoration: none; font-weight: bold;'>
        Built with ❤ by Eng. Jobbers – Qtrinova Inc
        </a>
        </div>""",
        elem_id="footer"
    )

demo.launch()