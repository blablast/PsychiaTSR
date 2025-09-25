from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import os
load_dotenv()
elevenlabs = ElevenLabs(
  api_key=os.getenv("ELEVENLABS_API_KEY"),
)
audio = elevenlabs.text_to_speech.convert(
    text='To naturalne, że czujesz się zestresowany na początku naszej rozmowy. Chciałabym się upewnić, jak mogę się do Ciebie zwracać – czy preferujesz formę "Ty" czy "Pan/Pani"? Co chciałbyś osiągnąć dzięki dzisiejszej rozmowie?',
    voice_id="MAjucoa86FdrzVZbe1um",
    model_id="eleven_flash_v2_5",
    output_format="mp3_44100_128",
)

play(audio)
