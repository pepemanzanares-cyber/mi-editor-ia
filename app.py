import sys, os, tempfile
import streamlit as st

# PARCHE DE COMPATIBILIDAD
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

st.set_page_config(page_title="AI SmartCut Pro", layout="wide")
st.title("🎬 AI SmartCut: Edición con IA")

# --- CONTROLES DE LA IA (Ajustes de precisión) ---
with st.sidebar:
    st.header("⚙️ Ajustes de la IA")
    ms = st.slider("Duración pausa (ms)", 100, 1000, 300, help="Tiempo mínimo de silencio para cortar")
    db = st.slider("Sensibilidad (dB)", -60, -20, -42, help="Umbral de ruido")
    dur_img = st.slider("Segundos por foto", 1, 10, 3)
    st.divider()
    st.warning("Recomendación: Si subes muchos archivos, procesa en tandas de 6-8.")

# --- CARGA DE ARCHIVOS ---
files = st.file_uploader("Sube videos y fotos", type=["mp4", "mov", "jpg", "png", "jpeg"], accept_multiple_files=True)

if files:
    if st.button("🚀 INICIAR PROCESAMIENTO IA"):
        all_clips = []
        prog = st.progress(0)
        status = st.empty()
        
        try:
            for i, f in enumerate(files):
                ext = os.path.splitext(f.name)[1].lower()
                status.text(f"IA analizando archivo {i+1}: {f.name}")
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(f.read())
                    path = tmp.name

                if ext in ['.mp4', '.mov']:
                    video = VideoFileClip(path).resize(height=720)
                    
                    # Análisis de audio para quitar silencios
                    t_audio = f"temp_{i}.wav"
                    if video.audio:
                        video.audio.write_audiofile(t_audio, fps=16000, logger=None, verbose=False)
                        audio_data = AudioSegment.from_file(t_audio)
                        
                        # Aquí ocurre la magia de la IA
                        intervals = detect_nonsilent(audio_data, min_silence_len=ms, silence_thresh=db)
                        
                        for start, end in intervals:
                            # Creamos el subclip sin silencio
                            all_clips.append(video.subclip(start/1000, end/1000))
                        
                        os.remove(t_audio)
                    else:
                        all_clips.append(video)

                elif ext in ['.jpg', '.jpeg', '.png']:
                    # Tratamiento de imágenes
                    img = ImageClip(path).set_duration(dur_img).resize(height=720)
                    # Asegurar ancho par para evitar errores de codec
                    if img.w % 2 != 0: img = img.resize(width=img.w - 1)
                    all_clips.append(img)
                
                prog.progress((i + 1) / len(files))

            if all_clips:
                status.text("🎬 Uniendo clips y exportando...")
                # 'method=compose' es necesario para mezclar fotos y videos
                final = concatenate_videoclips(all_clips, method="compose")
                
                out_name = "video_ia_final.mp4"
                final.write_videofile(out_name, codec="libx264", audio_codec="aac", fps=24, preset="ultrafast", logger=None)
                
                st.success("✅ ¡Vídeo listo!")
                st.video(out_name)
                with open(out_name, "rb") as final_f:
                    st.download_button("⬇️ DESCARGAR VÍDEO EDITADO", final_f, file_name="mi_video_ia.mp4")
                
                # Limpiar memoria
                final.close()
                for c in all_clips: c.close()

        except Exception as e:
            st.error(f"Se detuvo el proceso: {e}")
            st.info("💡 Intenta procesar menos archivos a la vez (ej. solo 6 videos).")
