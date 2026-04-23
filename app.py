import sys, os, tempfile
import streamlit as st

# 1. PARCHE PARA EL ERROR 'ANTIALIAS' Y AUDIOOP
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        sys.modules["audioop"] = audioop
    except ImportError: pass

from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

# Configuración de página
st.set_page_config(page_title="AI SmartCut 720p Fixed", layout="wide")
st.title("🎬 Editor IA Profesional (720p)")

with st.sidebar:
    st.header("⚙️ Ajustes")
    ms = st.slider("Corte Silencio (ms)", 100, 1000, 300)
    db = st.slider("Sensibilidad (dB)", -60, -20, -42)
    dur_img = st.slider("Segundos por foto", 1, 10, 3)
    st.info("Calidad fijada en 720p")

files = st.file_uploader("Sube tus archivos", 
                         type=["mp4", "mov", "jpg", "png", "jpeg"], 
                         accept_multiple_files=True)

if files:
    if st.button("🚀 PROCESAR EN 720p"):
        all_clips = []
        prog = st.progress(0)
        status = st.empty()
        
        try:
            for i, f in enumerate(files):
                ext = os.path.splitext(f.name)[1].lower()
                status.text(f"Procesando: {f.name}")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(f.read())
                    path = tmp.name

                if ext in ['.mp4', '.mov']:
                    # Mantener 720p sin deformar
                    video = VideoFileClip(path).resize(height=720)
                    
                    t_audio = f"t_{i}.wav"
                    video.audio.write_audiofile(t_audio, fps=16000, logger=None, verbose=False)
                    audio_data = AudioSegment.from_file(t_audio)
                    
                    intervals = detect_nonsilent(audio_data, min_silence_len=ms, silence_thresh=db)
                    
                    for start, end in intervals:
                        all_clips.append(video.subclip(start/1000, end/1000).copy())
                    
                    video.close()
                    if os.path.exists(t_audio): os.remove(t_audio)

                elif ext in ['.jpg', '.jpeg', '.png']:
                    # Las imágenes también a 720p
                    img = ImageClip(path).set_duration(dur_img).resize(height=720)
                    if img.w % 2 != 0: img = img.resize(width=img.w - 1)
                    all_clips.append(img)
                
                prog.progress((i + 1) / len(files))

            if all_clips:
                status.text("🎬 Renderizando a 720p... paciencia.")
                final = concatenate_videoclips(all_clips, method="compose")
                
                out_name = "video_720p_final.mp4"
                final.write_videofile(out_name, codec="libx264", audio_codec="aac", fps=24, preset="ultrafast", logger=None)
                
                st.success("✅ ¡Video listo en 720p!")
                st.video(out_name)
                with open(out_name, "rb") as f:
                    st.download_button("⬇️ DESCARGAR", f, file_name="video_ia_720p.mp4")
                
                final.close()
                for c in all_clips: c.close()

        except Exception as e:
            st.error(f"Error: {e}")
