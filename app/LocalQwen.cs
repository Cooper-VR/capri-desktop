using System;
using System.IO;
using System.Net;
using System.Text;

namespace CapriDesktop
{
    internal sealed class LocalQwen
    {
        internal const string Endpoint = "http://127.0.0.1:8001/synthesize";

        internal byte[] Speak(string text)
        {
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(Endpoint);
            request.Method = "POST";
            request.ContentType = "application/json";
            request.Timeout = 120000;
            request.ReadWriteTimeout = 120000;
            byte[] body = Encoding.UTF8.GetBytes("{\"text\":" + Voice.Quote(Voice.Sayable(text)) + "}");
            request.ContentLength = body.Length;
            using (Stream upload = request.GetRequestStream()) upload.Write(body, 0, body.Length);
            try
            {
                using (WebResponse response = request.GetResponse())
                using (Stream stream = response.GetResponseStream())
                using (MemoryStream copy = new MemoryStream())
                {
                    stream.CopyTo(copy);
                    return Voice.Clean(copy.ToArray());
                }
            }
            catch (WebException error)
            {
                HttpWebResponse response = error.Response as HttpWebResponse;
                if (response == null) throw new VoiceException("Can't reach local Qwen TTS.");
                string detail;
                using (response)
                using (StreamReader reader = new StreamReader(response.GetResponseStream())) detail = reader.ReadToEnd();
                throw new VoiceException("Local Qwen TTS failed: " + Voice.Short(detail));
            }
        }
    }
}
