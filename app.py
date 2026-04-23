import sys, os, tempfile
import streamlit as st

# PARCHE
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

st.set_page_config(page_title="AI Editor Final")
st.title("🎬 AI Editor: Modo Estable")

with st.sidebar:
    st.header("Ajustes IA")
    ms = st.slider("Corte (ms)", 100, 1000, 300)
    db = st.slider("Sensibilidad (dB)", -60, -20, -42)
    dur_img = st.slider("Segundos foto", 1, 10, 3)

files = st.file_uploader("Sube todo aquí", type=["mp4", "mov", "jpg", "png", "jpeg"], accept_multiple_files=True)

if files and st.button("🚀 Iniciar Montaje"):
    final_clips = []
    status = st.empty()
    prog = st.progress(0)
    
    try:
        for i, f in enumerate(files):
            ext = os.path.splitext(f.name)[1].lower()
            status.text(f"Procesando: {f.name}")
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(f.read())
                path = tmp.name

            if ext in ['.mp4', '.mov']:
                video = VideoFileClip(path)
                
                # Análisis de audio ultra-rápido
                t_audio = f"t_{i}.wav"
                video.audio.write_audiofile(t_audio, fps=16000, logger=None, verbose=False)
                audio = AudioSegment.from_file(t_audio)
                
                # Detectar voz
                intervals = detect_nonsilent(audio, min_silence_len=ms, silence_thresh=db)
                
                for start, end in intervals:
                    # Guardamos el clip recortado
                    clip = video.subclip(start/1000, end/1000)
                    final_clips.append(clip)
                
                # CERRAR ARCHIVOS INMEDIATAMENTE
                os.remove(t_audio)
                # No cerramos 'video' aún porque sus subclips dependen de él
            
            elif ext in ['.jpg', '.jpeg', '.png']:
                img = ImageClip(path).set_duration(dur_img).resize(width=1280) # Forzamos ancho estándar
                final_clips.append(img)
            
            prog.progress((i + 1) / len(files))

        if final_clips:
            status.text("🎬 Pegando clips... casi casi.")
            # 'method=chain' es el que menos RAM consume
            result = concatenate_videoclips(final_clips, method="chain")
            
            out = "video_final.mp4"
            # Usamos 'ultrafast' para que el servidor no se canse
            result.write_videofile(out, codec="libx264", audio_codec="aac", fps=24, preset="ultrafast", logger=None)
            
            st.success("¡CONSEGUIDO!")
            st.video(out)
            with open(out, "rb") as vf:
                st.download_button("⬇️ Descargar", vf, file_name="mi_video.mp4")
            
            # Limpieza total
            result.close()
            for c in final_clips: c.close()
            
    except Exception as e:
        st.error(f"Error: {e}")
