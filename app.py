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

from moviepy.editor import VideoFileClip, concatenate_videoclips
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

st.set_page_config(page_title="AI SmartCut", page_icon="🎬")

st.title("🎬 AI SmartCut: Recorte de Silencios")

# --- AJUSTES ---
with st.sidebar:
    st.header("⚙️ Ajustes de Voz")
    min_silence = st.slider("Duración pausa (ms)", 100, 1000, 300)
    umbral = st.slider("Sensibilidad (dB)", -60, -20, -40)

# --- CARGA ---
files = st.file_uploader("Sube tus clips", type=["mp4", "mov"], accept_multiple_files=True)

if files:
    if st.button("🚀 Quitar Silencios"):
        all_clips = []
        status = st.empty()
        
        for i, f in enumerate(files):
            status.text(f"Procesando clip {i+1}...")
            
            # Guardar temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(f.read())
                path = tmp.name

            video = VideoFileClip(path)
            
            # Para evitar deformación: forzamos a que MoviePy respete el tamaño del primer clip
            # Si los vídeos son de distintos tamaños, los centraremos con fondo negro en lugar de estirar
            
            # Extraer audio para análisis
            temp_audio = f"audio_{i}.wav"
            video.audio.write_audiofile(temp_audio, fps=22050, logger=None)
            audio_seg = AudioSegment.from_file(temp_audio)
            
            # Detectar sonido
            intervals = detect_nonsilent(audio_seg, min_silence_len=min_silence, silence_thresh=umbral)
            
            for start, end in intervals:
                # Cortamos solo la parte con voz
                clip = video.subclip(start/1000, end/1000)
                all_clips.append(clip)
            
            os.remove(temp_audio)

        if all_clips:
            status.text("Finalizando vídeo...")
            # 'chain' hace que se peguen uno detrás de otro sin inventar tamaños nuevos
            final = concatenate_videoclips(all_clips, method="chain") 
            
            output = "video_sin_silencios.mp4"
            final.write_videofile(output, codec="libx264", audio_codec="aac", fps=24)
            
            st.success("¡Hecho!")
            st.video(output)
            with open(output, "rb") as out_f:
                st.download_button("⬇️ Descargar", out_f, file_name="editado.mp4")
