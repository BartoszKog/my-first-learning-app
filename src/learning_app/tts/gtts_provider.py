"""gTTS implementation of ``TtsProvider`` (Google Translate unofficial TTS)."""

from __future__ import annotations

import asyncio
from io import BytesIO

from learning_app.tts.provider import TtsError, TtsNetworkError, TtsProvider


class GttsProvider(TtsProvider):
    """Generate MP3 audio through the gTTS library.

    Calls are offloaded with ``asyncio.to_thread`` so Flet handlers stay
    responsive. ``lang_check`` is disabled to avoid an extra network round
    trip per word.
    """

    name = "gtts"
    voice = ""

    def __init__(self, *, timeout: float = 10.0, tld: str = "com"):
        """Configure request timeout and Google Translate TLD.

        Args:
            timeout: Seconds to wait for the gTTS HTTP response.
            tld: Google Translate host TLD (``com``, ``co.uk``, …).
        """
        self.timeout = timeout
        self.tld = tld

    async def synthesize(self, text: str, language: str) -> bytes:
        """Return MP3 bytes from gTTS in a worker thread.

        Args:
            text: Normalized phrase to speak.
            language: IETF language tag accepted by gTTS (for example ``en``).

        Returns:
            MP3 audio bytes.

        Raises:
            TtsNetworkError: The Translate endpoint failed or timed out.
            TtsError: gTTS rejected the input or returned empty audio.
        """
        return await asyncio.to_thread(self._synthesize_sync, text, language)

    def _synthesize_sync(self, text: str, language: str) -> bytes:
        from gtts import gTTS
        from gtts.tts import gTTSError

        buffer = BytesIO()
        try:
            speech = gTTS(
                text=text,
                lang=language,
                lang_check=False,
                tld=self.tld,
                timeout=self.timeout,
            )
            speech.write_to_fp(buffer)
        except gTTSError as error:
            raise TtsNetworkError("gTTS could not generate audio.") from error
        except OSError as error:
            raise TtsNetworkError("gTTS network request failed.") from error
        except ValueError as error:
            raise TtsError("gTTS rejected the text or language.") from error
        except Exception as error:
            raise TtsError("gTTS could not generate audio.") from error

        data = buffer.getvalue()
        if not data:
            raise TtsError("gTTS returned empty audio.")
        return data
