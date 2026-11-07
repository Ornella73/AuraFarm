"""Audio phrase registry and recording manager for AuraFarm."""
import csv
from pathlib import Path
from typing import Dict, List, Optional, Any
from src.core.config import settings
from src.core.models import Language

class AudioPhrase:
    def __init__(
        self,
        phrase_id: str,
        category: str,
        french_text: str,
        ewe_text: str,
        kabiye_text: str,
        mina_text: str,
        word_count_fr: int,
        notes: str = ""
    ):
        self.phrase_id = phrase_id
        self.category = category
        self.french_text = french_text
        self.ewe_text = ewe_text
        self.kabiye_text = kabiye_text
        self.mina_text = mina_text
        self.word_count_fr = word_count_fr
        self.notes = notes

    def get_text_for_language(self, language: Language) -> str:
        if language == Language.EWE:
            return self.ewe_text
        elif language == Language.KABIYE:
            return self.kabiye_text
        elif language == Language.MINA:
            return self.mina_text
        return self.french_text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phrase_id": self.phrase_id,
            "category": self.category,
            "french_text": self.french_text,
            "ewe_text": self.ewe_text,
            "kabiye_text": self.kabiye_text,
            "mina_text": self.mina_text,
            "word_count_fr": self.word_count_fr,
            "notes": self.notes
        }

class AudioRegistry:
    """Loads and queries modular phrase bank and audio recording statuses."""

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or (settings.DATA_DIR / "audio_phrase_bank.csv")
        self._phrases: Dict[str, AudioPhrase] = {}
        self.load_phrases()

    def load_phrases(self):
        if not self.csv_path.exists():
            return
        with open(self.csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p = AudioPhrase(
                    phrase_id=row["phrase_id"],
                    category=row["category"],
                    french_text=row["french_text"],
                    ewe_text=row["ewe_text"],
                    kabiye_text=row["kabiye_text"],
                    mina_text=row["mina_text"],
                    word_count_fr=int(row["word_count_fr"]),
                    notes=row.get("notes", "")
                )
                self._phrases[p.phrase_id] = p

    def get_phrase(self, phrase_id: str) -> Optional[AudioPhrase]:
        return self._phrases.get(phrase_id)

    def list_phrases(self, category: Optional[str] = None) -> List[AudioPhrase]:
        if category:
            return [p for p in self._phrases.values() if p.category == category]
        return list(self._phrases.values())

    def get_storage_path(self, language: Language, phrase_id: str, speaker_id: str) -> Path:
        """Destination directory for recorded clips: data/recordings/{lang}/{phrase_id}_{speaker_id}.wav"""
        folder = settings.DATA_DIR / "recordings" / language.value
        folder.mkdir(parents=True, exist_ok=True)
        return folder / f"{phrase_id}_{speaker_id}.wav"

