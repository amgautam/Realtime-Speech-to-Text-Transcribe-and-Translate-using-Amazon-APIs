##from subprocess import Popen, PIPE

import boto3
import asyncio
import time
import sounddevice
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent


class Amazon_Stt:

    def decode(self):

        class MyEventHandler(TranscriptResultStreamHandler):
            async def handle_transcript_event(self, transcript_event: TranscriptEvent):
                #print('in handler')
                global output
                results = transcript_event.transcript.results
                if results:
                    if results[0].is_partial:
                        pass
                    else:
                        for result in results:
                            for alt in result.alternatives:
                                print(alt.transcript)
                                translate = boto3.client(service_name='translate', region_name='us-west-2', use_ssl=True)
                                translation = translate.translate_text(Text=alt.transcript, SourceLanguageCode='en',TargetLanguageCode='pt')
                                translated_output = translation['TranslatedText']
                                print(translated_output)


        async def mic_stream():
            print('in mic stream')
            # This function wraps the raw input stream from the microphone forwarding
            # the blocks to an asyncio.Queue.
            loop = asyncio.get_event_loop()
            input_queue = asyncio.Queue()

            def callback(indata, frame_count, time_info, status):
                loop.call_soon_threadsafe(input_queue.put_nowait, (bytes(indata), status))

            stream = sounddevice.RawInputStream(
                channels=1,
                samplerate=16000,
                callback=callback,
                blocksize=1024 * 2,
                dtype="int16",
            )

            with stream:
                while True:
                    indata, status = await input_queue.get()
                    yield indata, status

        async def write_chunks(stream):

            async for chunk, status in mic_stream():
                await stream.input_stream.send_audio_event(audio_chunk=chunk)
            await stream.input_stream.end_stream()

        async def basic_transcribe():

            client = TranscribeStreamingClient(region="us-west-2")

            stream = await client.start_stream_transcription(
                language_code="en-US",
                media_sample_rate_hz=16000,
                media_encoding="pcm",
            )

            handler = MyEventHandler(stream.output_stream)
            await asyncio.gather(write_chunks(stream), handler.handle_events())

        loop = asyncio.get_event_loop()
        loop.run_until_complete(basic_transcribe())
        loop.close()

if __name__ == "__main__":
    stt = Amazon_Stt()
    start = time.time()
    out = stt.decode()
    print('time taken',' ',time.time()-start)
    print('transcription is',' ',out)
