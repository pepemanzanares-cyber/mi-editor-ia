import sys
try:
    import audioop
except ImportError:
    import audioop_lts as audioop
    sys.modules["audioop"] = audioop

import streamlit as st
from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageSequenceClip
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import tempfile
import os

st.set_page_config(page_title="AI SmartCut Pro", layout="wide")

st.title("🎬 AI SmartCut: Edición Fluida")

# --- AJUSTES DE PRECISIÓN IA ---
with st.sidebar:
    st.header("⚙️ Ajustes de Precisión")
    # Sensibilidad: Menos dB significa que detecta ruidos más flojos como "sonido"
    min_silence_len = st.slider("Duración mínima silencio (ms)", 100, 1000, 300)
    silence_thresh = st.slider("Umbral de silencio (dB)", -60, -20, -45)
    st.info("💡 Consejo: Para eliminar respiraciones cortas, baja la 'Duración mínima'.")

# --- CARGA MÚLTIPLE ---
uploaded_files = st.file_uploader("Sube videos e imágenes de golpe", 
                                  type=["mp4", "mov", "jpg", "png"], 
                                  accept_multiple_files=True)

if uploaded_files:
    all_clips = []
    
    st.write(f"📦 Has subido {len(uploaded_files)} archivos.")
    
    if st.button("🚀 Procesar y Crear Vídeo Fluido"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file in enumerate(uploaded_files):
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.name.split('.')[-1]}")
            tfile.write(file.read())
            
            if file.type.startswith('video'):
                status_text.text(f"Analizando silencios en: {file.name}")
                video = VideoFileClip(tfile.name)
                
                # Extracción de audio para análisis de precisión
                temp_audio = f"temp_{i}.wav"
                video.audio.write_audiofile(temp_audio, fps=22050, logger=None)
                audio_seg = AudioSegment.from_file(temp_audio)
                
                # DETECCIÓN DE PARTES CON VOZ
                non_silent = detect_nonsilent(audio_seg, min_silence_len=min_silence_len, silence_thresh=silence_thresh)
                
                # Cortar y unir solo las partes con voz
                for start, end in non_silent:
                    all_clips.append(video.subclip(start/1000, end/1000))
                
                os.remove(temp_audio)
            
            elif file.type.startswith('image'):
                # Convertir imagen en clip de 3 segundos
                status_text.text(f"Añadiendo imagen: {file.name}")
                img_clip = ImageSequenceClip([tfile.name], fps=24).set_duration(3)
                all_clips.append(img_clip)
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if all_clips:
            status_text.text("Renderizando vídeo final optimizado...")
            final_video = concatenate_videoclips(all_clips, method="compose")
            
            output_path = "video_final_ia.mp4"
            # Compresión H.264 fluida para Android
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24, bitrate="2000k")
            
            st.success("✅ ¡Edición completada!")
            st.video(output_path)
            
            with open(output_path, "rb") as f:
                st.download_button("⬇️ Descargar Vídeo Editado", f, file_name="tu_video_ia.mp4")
