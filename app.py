import sys, os, tempfile
import streamlit as st
import PIL.Image

# PARCHE ANTIALIAS PARA EVITAR EL ERROR PREVIO
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

st.set_page_config(page_title="AI SmartCut: Etapas", layout="wide")
st.title("🎬 AI Editor: Procesamiento por Etapas")

with st.sidebar:
    st.header("⚙️ Configuración")
    ms = st.slider("Corte Silencio (ms)", 100, 1000, 300)
    db = st.slider("Sensibilidad (dB)", -60, -20, -42)
    dur_img = st.slider("Segundos por foto", 1, 10, 3)
    st.info("Estrategia: Limpieza individual + Unión final (720p)")

uploaded_files = st.file_uploader("Sube tus vídeos y fotos", 
                                  type=["mp4", "mov", "jpg", "png", "jpeg"], 
                                  accept_multiple_files=True)

if uploaded_files:
    if st.button("🚀 INICIAR PROCESAMIENTO"):
        processed_clips = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        try:
            for i, f in enumerate(uploaded_files):
                ext = os.path.splitext(f.name)[1].lower()
                status.text(f"Etapa 1: Limpiando silencios en {f.name}...")
                
                # Crear temporal para el archivo original
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                    tmp.write(f.read())
                    path_original = tmp.name

                if ext in ['.mp4', '.mov']:
                    # Cargar, redimensionar y procesar audio
                    video = VideoFileClip(path_original).resize(height=720)
                    
                    t_audio = f"temp_audio_{i}.wav"
                    video.audio.write_audiofile(t_audio, fps=16000, logger=None, verbose=False)
                    audio_segment = AudioSegment.from_file(t_audio)
                    
                    # Detectar zonas con voz
                    intervals = detect_nonsilent(audio_segment, min_silence_len=ms, silence_thresh=db)
                    
                    # Crear subclips de este video específico
                    subclips_del_video = [video.subclip(start/1000, end/1000) for start, end in intervals]
                    
                    if subclips_del_video:
                        # Unimos los pedazos de este video individualmente
                        video_limpio = concatenate_videoclips(subclips_del_video, method="chain")
                        processed_clips.append(video_limpio)
                    
                    # Limpieza inmediata de archivos de audio
                    if os.path.exists(t_audio): os.remove(t_audio)
                    # Nota: No cerramos el video original aquí porque processed_clips aún lo referencia

                elif ext in ['.jpg', '.jpeg', '.png']:
                    img_clip = ImageClip(path_original).set_duration(dur_img).resize(height=720)
                    if img_clip.w % 2 != 0: img_clip = img_clip.resize(width=img_clip.w - 1)
                    processed_clips.append(img_clip)
                
                progress_bar.progress((i + 1) / len(uploaded_files))

            if processed_clips:
                status.text("Etapa 2: Uniendo todos los clips procesados...")
                final_video = concatenate_videoclips(processed_clips, method="compose")
                
                output_filename = "resultado_final_720p.mp4"
                final_video.write_videofile(output_filename, codec="libx264", audio_codec="aac", fps=24, preset="ultrafast", logger=None)
                
                st.success("✅ ¡Montaje finalizado con éxito!")
                st.video(output_filename)
                with open(output_filename, "rb") as f:
                    st.download_button("⬇️ DESCARGAR VÍDEO FINAL", f, file_name="mi_video_editado.mp4")
                
                # Limpieza final de memoria
                final_video.close()
                for c in processed_clips: c.close()

        except Exception as e:
            st.error(f"Error durante el proceso: {e}")
            st.info("Tip: Si falla, prueba a subir los vídeos en dos grupos (9 y 9).")
