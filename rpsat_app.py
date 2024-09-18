import streamlit as st
from PyPDF2 import PdfReader
from transformers import pipeline
import pyttsx3
from gtts import gTTS
from googletrans import Translator
import time
import numpy as np
import re

st.set_page_config(page_title="RPSAT", page_icon="")
st.image("rpsat.png")
st.markdown("<h1 style='text-align: center; color: grey;'>Research Paper Summarizer and Audio Translator</h1>", unsafe_allow_html=True)
name = st.text_input('Search')

@st.cache_data
def translate_summary(summ, lang):
    mylist = []
    translator = Translator()
    for i in summ:
        text_t = translator.translate(i, dest=lang)
        mylist.append(text_t.text)
    return " ".join(mylist).replace('{', '').replace('}', '').replace("'summary_text': '", "").replace("'summary_text'", "")

def play_audio(summary, lang):
    with open('summary.txt',  "wb") as f:
        f.write(bytes(summary, encoding="utf-16"))
    file = open("summary.txt", "r", encoding="utf-16").read().replace("\n", " ")
    myobj = gTTS(text=str(file), lang=lang, slow=False)
    myobj.save("summary.wav")
    audio_file = open('summary.wav', 'rb')
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/wav')


text_list = []
uploaded_file = st.file_uploader("Choose a file")

if uploaded_file is not None:
    reader = PdfReader(uploaded_file)
    number_of_pages = len(reader.pages)
    for i, _ in enumerate(reader.pages):
        page = reader.pages[i]
        text_list.append(page.extract_text())
        text = " ".join(text_list)
    max_chunk = 400
    text = text.replace('.', '.<eos>')
    text = text.replace('?', '?<eos>')
    text = text.replace('!', '!<eos>')
    sentences = text.split('<eos>')
    current_chunk = 0
    chunks = []
    for sentence in sentences:
        if len(chunks) == current_chunk + 1: 
            if len(chunks[current_chunk]) + len(sentence.split(' ')) <= max_chunk:
                chunks[current_chunk].extend(sentence.split(' '))
            else:
                current_chunk += 1
                chunks.append(sentence.split(' '))
        else:
            print(current_chunk)
            chunks.append(sentence.split(' '))

    for chunk_id, _ in enumerate(chunks):
        chunks[chunk_id] = ' '.join(chunks[chunk_id])
    st.write(len(chunks))
    summarizer = pipeline("summarization")
    st.write("Summarizing pls wait.......")
    res = summarizer(chunks, max_length=120, min_length=30, do_sample=False)
    # st.write(' '.join([summ['summary_text'] for summ in res]))
    text_summary = ' '.join([summ['summary_text'] for summ in res])
    language = st.selectbox("Select Language to translate paper", ("English", "Tamil", "Hindi", "Telugu","Kn -  Kannada", "Gujarati", "Ml - Malayalam","Urdu", "Bn - Bengali", "Arabic",
                                                               "De - German", "Es - Spanish", "French", "Korean", "Russian", "Italian"))
    
    trans_string = "Translating your Summary to " + str(language)
    st.write(trans_string)
    final = translate_summary(res, lang=str(language)[:2].lower())
    st.write(final)
    play_audio(final, lang=str(language)[:2].lower())
    if name == "":
        st.write("")
    else : 
        with open("summary.txt", "rb") as f:
            contents = f.read()
        contents = contents.decode("utf-16")
        pattern = re.compile(name, re.IGNORECASE)
        matches = pattern.finditer(contents)
        for match in matches:
            start = match.start()
            end = match.end()
            highlighted = contents[:start] + "  ======>   " + contents[start:end] + "   <======  " + contents[end:]
            contents = highlighted
        st.write(contents)

    
