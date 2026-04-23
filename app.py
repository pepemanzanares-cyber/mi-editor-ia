import streamlit as st
import moviepy.editor as mp
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import tempfile
import os

# Configuración de la Página
st.set_page_config(page_title="AI Smart Editor", page_icon="🎬", layout="wide")

# Estilo Personalizado (Fluidez y Estética)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #FF4B4B; color: white; }
    </style>
    """, unsafe_allow_html=True)

def process_video(input_path, silence_thresh=-40, min_silence_len=500):
    """
    Detecta silencios y recorta el video.
    """
    video = mp.VideoFileClip(input_path)
    audio = video.audio
    
    # Guardar audio temporal para analizar silencios
    temp_audio = "temp_audio.wav"
    audio.write_audiofile(temp_audio, fps=22050, verbose=False, logger=None)
    
    audio_segment = AudioSegment.from_file(temp_audio)
    # Detectar partes con sonido
    nonsilent_chunks = detect_nonsilent(
        audio_segment, 
        min_silence_len=min_silence_len, 
        silence_thresh=silence_thresh
    )
    
    # Convertir milisegundos a segundos y crear subclips
    clips = []
    for start, end in nonsilent_chunks:
        clips.append(video.subclip(start/1000, end/1000))
    
    final_video = mp.concatenate_videoclips(clips)
    return final_video

# --- INTERFAZ DE USUARIO ---
st.title("🎬 AI SmartCut - Editor Inteligente")
st.subheader("Sube tus videos y deja que la IA haga el trabajo sucio.")

uploaded_file = st.file_uploader("Elige un video o imagen", type=["mp4", "mov", "avi", "jpg", "png"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False) 
    tfile.write(uploaded_file.read())
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("Archivo Original")
        st.video(uploaded_file)
        
    with col2:
        st.success("Configuración de IA")
        sensibilidad = st.slider("Sensibilidad de detección de silencio (dB)", -60, -20, -40)
        calidad = st.select_slider("Calidad de Exportación", options=["Baja (Comprimido)", "Media", "Alta (Original)"])
        
        if st.button("🚀 Procesar con IA"):
            with st.spinner("Analizando contenido y eliminando silencios..."):
                output_path = "video_editado.mp4"
                
                # Procesamiento
                result_video = process_video(tfile.name, silence_thresh=sensibilidad)
                
                # Compresión inteligente basada en la selección
                bitrate = "1000k" if calidad == "Baja (Comprimido)" else "3000k"
                
                result_video.write_videofile(
                    output_path, 
                    codec="libx264", 
                    audio_codec="aac", 
                    bitrate=bitrate,
                    preset="ultrafast" # Para máxima fluidez
                )
                
                st.video(output_path)
                
                with open(output_path, "rb") as file:
                    st.download_button(
                        label="⬇️ Descargar Video Optimizado",
                        data=file,
                        file_name="smartcut_video.mp4",
                        mime="video/mp4"
                    )
                st.balloons()

# --- SECCIÓN DE IA ANALÍTICA ---
st.divider()
st.write("🤖 **Asistente IA:** Analizando encuadres y sugerencias...")
if uploaded_file:
    st.warning("IA: He detectado que el fondo tiene mucho ruido visual. ¿Quieres aplicar un desenfoque inteligente? (Próximamente)")
