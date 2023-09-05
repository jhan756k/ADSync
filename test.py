import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt

def calculate_db(audio_data):
    rms = np.sqrt(np.mean(np.square(audio_data)))
    db = 20 * np.log10(rms)
    return db

def generate_time_db_graph(audio_path, sample_rate=44100, block_size=1024, time_range=(0, 5.2), x_interval=0.2):
    audio_data, _ = sf.read(audio_path)
    audio_length = len(audio_data)
    start_time, end_time = time_range
    
    db_levels = []

    for i in range(0, audio_length, block_size):
        time = i / sample_rate
        if time > end_time:
            break

        audio_frame = audio_data[i:i + block_size]
        db = calculate_db(audio_frame)
        db_levels.append(db)

    time_values = np.arange(start_time, end_time + x_interval, x_interval)
    plt.plot(np.linspace(start_time, len(db_levels) * block_size / sample_rate, len(db_levels)), db_levels)
    plt.xticks(time_values)
    plt.xlabel('Time (s)')
    plt.ylabel('dB Level')
    plt.title('Time-Decibel Graph')
    plt.grid()
    plt.show()

if __name__ == "__main__":
    audio_path =r"C:\Users\Jooney Han\Desktop\과학전람회\충음실 데이터\길이_음원\15길이.wav"
    generate_time_db_graph(audio_path)
