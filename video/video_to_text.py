#!/usr/bin/env python
# coding: utf-8

# In[2]:


# For video tweet

def download_file(url, output_file_type='.mp4'):
    """Downloads the given file."""
    import requests
    
    r = requests.get(url, allow_redirects=True)
    open('data/original' + output_file_type, 'wb').write(r.content)

    
def convert_mp4_to_audio(input_file='data/original', 
                         input_file_type='.mp4', 
                         output_file_type='.wav'):
    """ Converts .mp4 to audio (.wav). """
    import moviepy.editor as mp
    
    path = input_file+input_file_type
    clip = mp.VideoFileClip(path) 
    clip.audio.write_audiofile('data/converted'+output_file_type)


def transcribe_audio_from_video_for_description(input_file='data/converted',
                                                input_file_type='.wav'):
    """
    Splits audio file into chunks 
    and apply speech recognition on each of these chunks.
    """

    import speech_recognition as sr 
    import os 
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
    import json
    
    path = input_file+input_file_type
    # Initialize the recognizer.
    r = sr.Recognizer()
    
    # Open the audio file and adjust for ambient noise.
    with sr.AudioFile(path) as source:
        r.adjust_for_ambient_noise(source, duration=.1)
    sound = AudioSegment.from_wav(path)
    
    # Split sound where silence is >1/2 second, and get chunks.
    chunks = split_on_silence(sound, 
                              min_silence_len=500,
                              silence_thresh=sound.dBFS-14,
                              keep_silence=500
                             )

    # Create a directory to store the audio chunks.
    folder_name = 'data/audio-chunks'
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
        
    # Process each chunk.
    whole_text = ''
    for i, audio_chunk in enumerate(chunks, start=1):
        # Export chunk and save it in the `folder_name` directory.
        chunk_filename = os.path.join(folder_name, f'chunk{i}'+input_file_type)
        audio_chunk.export(chunk_filename, format=input_file_type[1:])
        # Convert the chunk into text.
        with sr.AudioFile(chunk_filename) as source:
            audio_listened = r.record(source)
            try:
                text = r.recognize_google(audio_listened)
                text = f'{text.capitalize()}.'
            except sr.UnknownValueError as e:
                text = '[VOICE INDISTINGUISABLE..]'
            else:
                # Concatenate all chunks.
                whole_text += text + ' '
    
    with open('data/text.txt', 'w') as outfile:
        json.dump(whole_text, outfile)
        

def transcribe_audio_from_video_for_subtitles(input_file='data/converted',
                                              input_file_type='.wav',
                                              audio_channel_count=2): 
    """ Transcribes the given audio file. """
    from google.cloud import speech
    import io
    import json
    
    # Import Google API credentials (Cloud Speech-to-Text). 
    # Use your own 'service_account.json' here.
    client = speech.SpeechClient.from_service_account_json(
        'service_account.json'
    )
    
    # Open audio file.
    path = input_file + input_file_type
    with io.open(path, 'rb') as audio_file:
        content = audio_file.read()
    
    # Transcribes to text.
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        #sample_rate_hertz=44100,
        language_code="en-US",
        enable_word_time_offsets=True,
        audio_channel_count=audio_channel_count,
    )
    response = client.recognize(config=config, audio=audio)
    
    # Enumerate words, start and end times for each response chunk.
    list_words = []
    list_start_times = []
    list_end_times = []
    for res in response.results:
        result = res.alternatives[0]
        list_words += [word_info.word for word_info in result.words]
        list_start_times += [word_info.start_time.total_seconds() for word_info in result.words]
        list_end_times += [word_info.end_time.total_seconds() for word_info in result.words]
    output_lists = {'list_words': list_words,
                    'list_start_times': list_start_times, 
                    'list_end_times': list_end_times
                   }
    
    with open('data/lists.txt', 'w') as outfile:
        json.dump(output_lists, outfile)


def main(url):
    download_file(url)
    convert_mp4_to_audio()
    transcribe_audio_from_video_for_subtitles()
    transcribe_audio_from_video_for_description()
     
url = 'https://video.twimg.com/ext_tw_video/1330183742573473792/pu/vid/406x720/FvSwKv_YK7bm_al_.mp4?tag=10'
main(url)

