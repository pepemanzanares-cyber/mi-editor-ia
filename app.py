import sys
import os
import tempfile
import streamlit as st

# PARCHE DE COMPATIBILIDAD
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        sys.modules["audioop"] = audioop
    except ImportError:
        pass

from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageSequenceClip
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

st.set_page_config(page_title="AI SmartCut Pro", layout="wide")
st.title("🎬 Montador Inteligente")

# --- CONFIGURACIÓN ---
with st.sidebar:
    st.header("Ajustes")
    min_silence = st.slider("Corte Silencio (ms)", 100, 1000, 300)
    umbral = st.slider("Sensibilidad (dB)", -60, -20, -42)
    duracion_img = st.slider("Segundos por foto", 1, 10, 3)

files = st.file_uploader("Sube videos y fotos", type=["mp4", "mov", "jpg", "png", "jpeg"], accept_multiple_files=True)

if files:
    if st.button("🚀 Crear Montaje"):
        all_clips = []
        progress = st.progress(0)
        
        try:
            for i, f in enumerate(files):
                ext = os.path.splitext(f.name)[1].lower()
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(f.read())
                    path = tmp.name

                if ext in ['.mp4', '.mov']:
                    video = VideoFileClip(path)
                    # Análisis de audio
                    temp_a = f"a_{i}.wav"
                    video.audio.write_audiofile(temp_a, fps=22050, logger=None, verbose=False)
                    audio_seg = AudioSegment.from_file(temp_a)
                    intervals = detect_nonsilent(audio_seg, min_silence_len=min_silence, silence_thresh=umbral)
                    
                    for start, end in intervals:
                        # Cortamos y forzamos un tamaño estándar (1080p vertical es lo más común hoy)
                        clip = video.subclip(start/1000, end/1000).resize(height=720) 
                        all_clips.append(clip)
                    
                    video.close()
                    os.remove(temp_a)

                elif ext in ['.jpg', '.jpeg', '.png']:
                    # Convertimos imagen a video de forma muy ligera
                    img_clip = ImageSequenceClip([path], fps=1).set_duration(duracion_img).resize(height=720)
                    all_clips.append(img_clip)

                progress.progress((i + 1) / len(files))

            if all_clips:
                st.text("Uniendo todo... casi listo.")
                # Usamos method="compose" pero con un tamaño fijo para evitar el error "Oh no"
                final = concatenate_videoclips(all_clips, method="compose")
                out = "video_final.mp4"
                final.write_videofile(out, codec="libx264", audio_codec="aac", fps=24, logger=None)
                
                st.video(out)
                with open(out, "rb") as f:
                    st.download_button("⬇️ Descargar Video", f, file_name="montaje_ia.mp4")
                final.close()

        except Exception as e:
            st.error(f"Error técnico: {e}")
            st.info("Prueba a subir primero los videos y luego las fotos por separado.")
