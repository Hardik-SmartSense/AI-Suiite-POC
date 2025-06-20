CONVERSATION_TONE_CONFIG = {
    "formal": {
        "en-US": {
            "prompt": "You are a professional and respectful AI assistant. Use a formal and informative tone. Avoid slang.",
            "voice": "en-US-GuyNeural",
            "style": "narration-professional",
            "rate": "+0%",
            "pitch": "+0Hz"
        },
        "de-DE": {
            "prompt": "Du bist ein professioneller und respektvoller KI-Assistent. Verwende einen formellen und informativen Ton. Vermeide Umgangssprache.",
            "voice": "de-DE-ConradNeural",
            "style": "newscast-casual",  # best available match
            "rate": "+0%",
            "pitch": "+0Hz"
        }
    },
    "friendly": {
        "en-US": {
            "prompt": "You are a friendly and cheerful AI assistant. Use casual language and be supportive.",
            "voice": "en-US-JennyNeural",
            "style": "cheerful",
            "rate": "+10%",
            "pitch": "+2Hz"
        },
        "de-DE": {
            "prompt": "Du bist ein freundlicher und fröhlicher KI-Assistent. Verwende eine lockere Sprache und sei hilfsbereit.",
            "voice": "de-DE-KatjaNeural",
            "style": "cheerful",
            "rate": "+10%",
            "pitch": "+2Hz"
        }
    },
    "concise": {
        "en-US": {
            "prompt": "You are a concise AI assistant. Keep responses short and to the point.",
            "voice": "en-US-DavisNeural",
            "style": "assistant",
            "rate": "-5%",
            "pitch": "-2Hz"
        },
        "de-DE": {
            "prompt": "Du bist ein prägnanter KI-Assistent. Halte deine Antworten kurz und auf den Punkt.",
            "voice": "de-DE-ConradNeural",
            "style": "assistant",
            "rate": "-5%",
            "pitch": "-2Hz"
        }
    },
    "empathetic": {
        "en-US": {
            "prompt": "You are a compassionate AI assistant. Show empathy and offer emotional support when needed.",
            "voice": "en-US-AmberNeural",
            "style": "empathetic",
            "rate": "+5%",
            "pitch": "+2Hz"
        },
        "de-DE": {
            "prompt": "Du bist ein mitfühlender KI-Assistent. Zeige Empathie und biete emotionale Unterstützung an, wenn nötig.",
            "voice": "de-DE-KatjaNeural",
            "style": "empathetic",  # supported in some voices, fallback gracefully
            "rate": "+5%",
            "pitch": "+2Hz"
        }
    },
    "technical": {
        "en-US": {
            "prompt": "You are a technical AI assistant. Provide accurate and detailed answers using precise terminology.",
            "voice": "en-US-BrandonNeural",
            "style": "narration-professional",
            "rate": "-2%",
            "pitch": "-1Hz"
        },
        "de-DE": {
            "prompt": "Du bist ein technischer KI-Assistent. Gib genaue und detaillierte Antworten mit präziser Fachsprache.",
            "voice": "de-DE-ConradNeural",
            "style": "newscast-casual",  # or narration as fallback
            "rate": "-2%",
            "pitch": "-1Hz"
        }
    }
}
