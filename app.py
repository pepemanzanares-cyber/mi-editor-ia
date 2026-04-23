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

st.set_page_config(page_title="AI SmartCut Pro", page_icon="🎬", layout="wide")

st.title("🎬 Montador IA: Videos + Imágenes")
st.markdown("Corta silencios y une todo en un solo video fluido sin deformaciones.")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Ajustes de Voz")
    min_silence = st.slider("Duración pausa (ms)", 100, 1000, 300)
    umbral = st.slider("Sensibilidad (dB)", -60, -20, -42)
    st.divider()
    duracion_img = st.slider("Segundos por imagen", 1, 10, 3)

# --- CARGA MÚLTIPLE ---
files = st.file_uploader("Sube tus videos y tus 4 imágenes", 
                         type=["mp4", "mov", "jpg", "png", "jpeg"], 
                         accept_multiple_files=True)

if files:
    if st.button("🚀 Montar todo el contenido"):
        all_clips = []
        status = st.empty()
        
        # Primero definimos el tamaño del video final basado en el primer clip para evitar deformar
        final_width = None
        final_height = None

        for i, f in enumerate(files):
            status.text(f"Analizando archivo {i+1} de {len(files)}...")
            
            # Guardar temporal
            ext = os.path.splitext(f.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(f.read())
                path = tmp.name

            if f.type.startswith('video'):
                video = VideoFileClip(path)
                
                # Establecer tamaño base si es el primer clip
                if final_width is None:
                    final_width, final_height = video.size

                # Analizar audio
                temp_audio = f"audio_{i}.wav"
                video.audio.write_audiofile(temp_audio, fps=22050, logger=None, verbose=False)
                audio_seg = AudioSegment.from_file(temp_audio)
                
                # Detectar voz
                intervals = detect_nonsilent(audio_seg, min_silence_len=min_silence, silence_thresh=umbral)
                
                for start, end in intervals:
                    # Cortar y reescalar para que encaje sin deformar
                    clip = video.subclip(start/1000, end/1000).resize(height=final_height)
                    if clip.w > final_width:
                        clip = clip.resize(width=final_width)
                    all_clips.append(clip)
                
                video.close()
                os.remove(temp_audio)

            elif f.type.startswith('image'):
                # Convertir imagen a clip de video
                img_clip = ImageClip(path).set_duration(duracion_img)
                
                if final_width is None:
                    # Si lo primero es una imagen, usamos un tamaño estándar HD
                    final_width, final_height = (1080, 1920) 
                
                # Ajustar imagen al tamaño del video sin estirar
                img_clip = img_clip.resize(height=final_height)
                if img_clip.w > final_width:
                    img_clip = img_clip.resize(width=final_width)
                
                all_clips.append(img_clip)

        if all_clips:
            status.text("🎬 Uniendo clips y renderizando... Ten paciencia.")
            # method="compose" es necesario cuando mezclamos fotos y videos de distintos tamaños
            final = concatenate_videoclips(all_clips, method="compose") 
            
            output = "resultado_final.mp4"
            final.write_videofile(output, codec="libx264", audio_codec="aac", fps=24, logger=None)
            
            st.success("¡Montaje completado!")
            st.video(output)
            with open(output, "rb") as out_f:
                st.download_button("⬇️ Descargar Montaje Final", out_f, file_name="mi_video_ia.mp4")
            
            final.close()
        else:
            st.error("No se pudo procesar nada. Revisa los archivos.")
