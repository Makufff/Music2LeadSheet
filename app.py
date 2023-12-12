import os
import streamlit as st
import numpy as np
import librosa
import subprocess
from base64 import b64encode
from music21 import note, stream, meter, tempo, metadata , environment
# setup environment
us = environment.UserSettings()
us['musicxmlPath'] = r'C://Program Files//MuseScore 4//bin//MuseScore4.exe'
us['musescoreDirectPNGPath'] = r'C://Program Files//MuseScore 4//bin//MuseScore4.exe'
us['lilypondPath'] = r'C://Music2leadsheet//lilypond-2.24.3//bin//lilypond.exe'


# fix note C3 - C6
note_frequencies = {
    "A3": 220.0,
    "A#3": 233.1,
    "B3": 246.9, 
    "C4": 261.6,
    "C#4": 277.2,
    "D4": 293.7,
    "D#4": 311.1,
    "E4": 329.6,
    "F4": 349.2,
    "F#4": 370.0,
    "G4": 392.0,
    "G#4": 415.3,
    "A4": 440.0
}

def find_bpm():
    return
# use camelots
def find_keys():
    return
def find_chords():
    return 


def find_closest_note(frequency):
    return min(note_frequencies.keys(), key=lambda x: abs(note_frequencies[x] - frequency))

def note_name_to_object(note_name, duration):
    return note.Note(note_name, quarterLength=duration)

def round_duration(duration, subdivision=16):
    return round(duration * subdivision) / subdivision

def create_leadsheet(onset_results , sheet_name="Generated Leadsheet" , composer="Generate APP"):
    # Create a stream for the leadsheet
    leadsheet_stream = stream.Score()
    # Create a part for the leadsheet
    part = stream.Part()

    # Add time signature and tempo  FIX
    part.append(meter.TimeSignature('4/4')) #
    part.append(tempo.MetronomeMark(number=60))  # Adjust the tempo as needed

    # Iterate over onset results and add notes to the part
    for result in onset_results:
        # Round the duration to the nearest subdivision
        rounded_duration = round_duration(result['duration'])
        note_obj = note_name_to_object(result['detected_note'], rounded_duration)
        part.append(note_obj)

    # Add the part to the leadsheet stream
    leadsheet_stream.append(part)
    leadsheet_stream.insert(0, metadata.Metadata())
    leadsheet_stream.metadata.composer = composer
    leadsheet_stream.metadata.title = sheet_name

    return leadsheet_stream
# main function
def generate_sheet(y , sr , sheet_name="Generated Leadsheet" , composer="Generate APP"):
    onset_results = []
    # Compute onset strength
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    # print(onset_times)
    for i in range(len(onset_times) - 1):
        start_time = onset_times[i]
        end_time = onset_times[i + 1]

        # Extract the signal within the onset interval
        onset_interval = y[int(sr * start_time):int(sr * end_time)]

        # Perform FFT
        fft_result = np.fft.fft(onset_interval)
        freqs = np.fft.fftfreq(len(onset_interval), 1/sr)
        freqs = freqs[:len(freqs)//2]
        fft_result = 2.0/len(onset_interval) * np.abs(fft_result[:len(onset_interval)//2])

        # Find the dominant frequency
        dominant_freq_index = np.argmax(fft_result)
        dominant_freq = freqs[dominant_freq_index]

        # Convert frequency to note
        detected_note = find_closest_note(dominant_freq)

        # Calculate duration in seconds
        duration = end_time - start_time
        
        # Save results in a dictionary
        onset_dict = {
            'start_time': start_time,
            'end_time': end_time,
            'detected_note': detected_note,
            'dominant_frequency': dominant_freq,
            'duration': duration
        }

        # Append the dictionary to the list
        onset_results.append(onset_dict)

    leadsheet = create_leadsheet(onset_results, sheet_name=sheet_name, composer=composer)

    # Show or save the leadsheet
    # Save the score as a MusicXML file
    leadsheet.write('musicxml', 'C:/Music2leadsheet/output/result.xml')
    subprocess.run([us['musicxmlPath'], 'C:/Music2leadsheet/output/result.xml', '-o', 'C:/Music2leadsheet/output/result.pdf'])
    # leadsheet.show('musicxml')

def show_pdf(pdf_path):
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    pdf_base64 = b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="700" height="800" type="application/pdf"></iframe>'
    # Display the PDF in Streamlit
    st.markdown(pdf_display, unsafe_allow_html=True)

# Streamlit app
def main():
    st.title("Music to Leadsheet Generator")

    # Get user input for sheet name and composer
    sheet_name = st.text_input("Enter Sheet Name:")
    composer_name = st.text_input("Enter Composer Name:")
    
    uploaded_file = st.file_uploader("Upload a WAV file", type=["wav"])

    if uploaded_file is not None:
        st.audio(uploaded_file, format="audio/wav", start_time=0)

        if st.button("Generate Leadsheet"):
            # Save uploaded file
            filename = "uploaded_file.wav"
            with open(filename, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Process the uploaded file
            os.system(f"demucs -d cpu {filename}")

            # Get file path for separated vocals
            # name = filename.split(".")[0]
            file_path = r'C:\Music2leadsheet\separated\htdemucs\uploaded_file\vocals.wav'
            y, sr = librosa.load(file_path)

            # Generate leadsheet
            generate_sheet(y=y, sr=sr, sheet_name=sheet_name, composer=composer_name)
           
if __name__ == "__main__":
    main()
