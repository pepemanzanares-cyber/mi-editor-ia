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

from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

st.set_page_config(page_title="AI SmartCut Pro", layout="wide")
st.title("🎬 Montador Inteligente v3")

# --- CONFIGURACIÓN ---
with st.sidebar:
    st.header("Ajustes")
    min_silence = st.slider("Corte Silencio (ms)", 100, 1000, 300)
    umbral = st.slider("Sensibilidad (dB)", -60, -20, -42)
    duracion_img = st.slider("Segundos por foto", 1, 10, 3)
    st.info("Nota: Todo se exportará a 720p para asegurar fluidez.")

files = st.file_uploader("Sube videos y fotos", type=["mp4", "mov", "jpg", "png", "jpeg"], accept_multiple_files=True)

if files:
    if st.button("🚀 Crear Montaje"):
        all_clips = []
        progress = st.progress(0)
        status = st.empty()
        
        try:
            for i, f in enumerate(files):
                ext = os.path.splitext(f.name)[1].lower()
                status.text(f"Procesando archivo {i+1}: {f.name}")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(f.read())
                    path = tmp.name

                if ext in ['.mp4', '.mov']:
                    video = VideoFileClip(path).resize(height=720) # Redimensionar al cargar
                    
                    # Análisis de audio
                    temp_a = f"audio_temp_{i}.wav"
                    if video.audio:
                        video.audio.write_audiofile(temp_a, fps=22050, logger=None, verbose=False)
                        audio_seg = AudioSegment.from_file(temp_a)
                        intervals = detect_nonsilent(audio_seg, min_silence_len=min_silence, silence_thresh=umbral)
                        
                        for start, end in intervals:
                            clip = video.subclip(start/1000, end/1000)
                            all_clips.append(clip)
                        
                        os.remove(temp_a)
                    else:
                        all_clips.append(video)

                elif ext in ['.jpg', '.jpeg', '.png']:
                    # Crear clip de imagen con tamaño fijo
                    img_clip = ImageClip(path).set_duration(duracion_img).resize(height=720)
                    # Forzamos a que tenga un ancho par (necesario para muchos codecs)
                    if img_clip.w % 2 != 0:
                        img_clip = img_clip.resize(width=img_clip.w - 1)
                    all_clips.append(img_clip)

                progress.progress((i + 1) / len(files))

            if all_clips:
                status.text("🎬 Uniendo y comprimiendo... esto puede tardar un poco.")
                # 'compose' ayuda a mezclar fotos y videos de distintos formatos
                final = concatenate_videoclips(all_clips, method="compose")
                
                output = "video_final_ia.mp4"
                final.write_videofile(output, codec="libx264", audio_codec="aac", fps=24, logger=None, preset="ultrafast")
                
                st.success("✅ ¡Montaje terminado!")
                st.video(output)
                with open(output, "rb") as vid_file:
                    st.download_button("⬇️ Descargar Video", vid_file, file_name="mi_video_ia.mp4")
                
                final.close()
                for c in all_clips: c.close()

        except Exception as e:
            st.error(f"Se ha producido un error: {e}")
            st.info("Prueba a subir los archivos en grupos más pequeños.")

else:
    st.info("Sube tus archivos para empezar.")
