using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace CapriDesktop
{
    [DataContract]
    internal sealed class WhisperReply
    {
        [DataMember(Name = "text")] internal string Text;
    }

    internal sealed class LocalWhisper : IDisposable
    {
        internal const string Endpoint = "http://127.0.0.1:8000/transcribe";
        private readonly object gate = new object();
        private readonly List<short> samples = new List<short>();
        private readonly HttpClient client = new HttpClient();
        private volatile bool running;
        private bool speaking;
        private int quietChunks;
        private bool transcribing;

        internal event Action<string> Heard;
        internal event Action<string> Failed;

        internal void Start()
        {
            lock (gate)
            {
                samples.Clear();
                speaking = false;
                quietChunks = 0;
                transcribing = false;
                running = true;
            }
        }

        internal void Stop()
        {
            lock (gate)
            {
                running = false;
                samples.Clear();
                speaking = false;
                quietChunks = 0;
            }
        }

        internal void Feed(short[] chunk)
        {
            if (chunk == null || chunk.Length == 0) return;
            bool submit = false;
            lock (gate)
            {
                if (!running || transcribing) return;
                double level = Speaker.Loudness(chunk, 0, chunk.Length);
                if (level >= 0.02)
                {
                    speaking = true;
                    quietChunks = 0;
                }
                else if (speaking) quietChunks++;
                if (speaking)
                {
                    samples.AddRange(chunk);
                    if (samples.Count > Ears.Rate * 15) submit = true;
                    else if (quietChunks >= 8) submit = true;
                }
                if (submit)
                {
                    transcribing = true;
                    speaking = false;
                    quietChunks = 0;
                    short[] phrase = samples.ToArray();
                    samples.Clear();
                    Task.Run(delegate { Transcribe(phrase); });
                }
            }
        }

        private async void Transcribe(short[] phrase)
        {
            try
            {
                byte[] wav = Wave(phrase);
                using (MultipartFormDataContent form = new MultipartFormDataContent())
                using (ByteArrayContent audio = new ByteArrayContent(wav))
                {
                    audio.Headers.ContentType = new MediaTypeHeaderValue("audio/wav");
                    form.Add(audio, "audio", "capri.wav");
                    using (HttpResponseMessage response = await client.PostAsync(Endpoint, form))
                    {
                        response.EnsureSuccessStatusCode();
                        using (Stream body = await response.Content.ReadAsStreamAsync())
                        {
                            WhisperReply reply = (WhisperReply)new DataContractJsonSerializer(typeof(WhisperReply)).ReadObject(body);
                            if (!string.IsNullOrWhiteSpace(reply.Text))
                            {
                                Action<string> heard = Heard;
                                if (heard != null) heard(reply.Text.Trim());
                            }
                        }
                    }
                }
            }
            catch (Exception error)
            {
                Action<string> failed = Failed;
                if (failed != null) failed("Whisper is unavailable: " + error.Message);
            }
            finally
            {
                lock (gate) transcribing = false;
            }
        }

        private static byte[] Wave(short[] samples)
        {
            using (MemoryStream stream = new MemoryStream())
            using (BinaryWriter writer = new BinaryWriter(stream))
            {
                writer.Write(Encoding.ASCII.GetBytes("RIFF"));
                writer.Write(36 + samples.Length * 2);
                writer.Write(Encoding.ASCII.GetBytes("WAVEfmt "));
                writer.Write(16);
                writer.Write((short)1);
                writer.Write((short)1);
                writer.Write(Ears.Rate);
                writer.Write(Ears.Rate * 2);
                writer.Write((short)2);
                writer.Write((short)16);
                writer.Write(Encoding.ASCII.GetBytes("data"));
                writer.Write(samples.Length * 2);
                for (int i = 0; i < samples.Length; i++) writer.Write(samples[i]);
                return stream.ToArray();
            }
        }

        public void Dispose() { client.Dispose(); }
    }
}
