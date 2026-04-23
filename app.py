import streamlit as st
import os, tempfile
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip

st.set_page_config(page_title="Editor de Emergencia")
st.title("🎬 Editor por Partes (Antifallos)")

st.info("Para evitar el error 'Oh no', procesa tus videos en grupos de 5 o 6.")

files = st.file_uploader("Sube un grupo pequeño de archivos", type=["mp4", "mov", "jpg", "png"], accept_multiple_files=True)

if files and st.button("🚀 Unir este grupo"):
    clips = []
    with st.spinner("Procesando grupo..."):
        for f in files:
            t = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(f.name)[1])
            t.write(f.read())
            if f.type.startswith('video'):
                clips.append(VideoFileClip(t.name).resize(height=720))
            else:
                clips.append(ImageClip(t.name).set_duration(3).resize(height=720))
        
        final = concatenate_videoclips(clips, method="chain")
        final.write_videofile("parte_provisional.mp4", codec="libx264", preset="ultrafast")
        st.video("parte_provisional.mp4")
        with open("parte_provisional.mp4", "rb") as f:
            st.download_button("⬇️ Descargar esta parte", f, file_name="parte.mp4")
