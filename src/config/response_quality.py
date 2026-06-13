"""Editable response-quality policy for survey answers.

Add low-information words or complete phrases to LOW_INFORMATION_RESPONSES.
Matching is case-insensitive and ignores accents and punctuation.
"""

import re
import unicodedata


RESPONSE_QUALITY_METADATA_KEY = "response_quality"
LOW_INFORMATION_VALUE = "low_information"
SUBSTANTIVE_VALUE = "substantive"
RESPONSE_QUALITY_VERSION = 2


LOW_INFORMATION_RESPONSES = {
    # Dutch
    "alles goed",
    "alles is goed",
    "alles is okay",
    "alles oke",
    "alles is oke",
    "alles okay",
    "ga zo door",
    "gaat goed",
    "geen",
    "geen antwoord",
    "geen bijzondere omstandigheden",
    "geen commentaar",
    "geen ervaring mee",
    "geen verdere opmerking",
    "geen verdere opmerkingen",
    "geen idee",
    "geen mening",
    "geen opmerking",
    "geen opmerkingen",
    "goed",
    "goed bezig",
    "goed geregeld",
    "goedzo",
    "heb geen bijzondere omstandigheden",
    "heb ik niet",
    "heel goed",
    "houden zo",
    "ik heb geen commentaar",
    "ik heb geen bijzondere omstandigheden",
    "ik heb geen opmerkingen",
    "ik heb er geen",
    "ik heb niets toe te voegen",
    "ik weet het niet",
    "is goed",
    "is prima",
    "ja",
    "kan beter",
    "leuke opleiding",
    "liever niet",
    "nee",
    "nee bedankt",
    "nee ben tevreden",
    "nee hoeft niet",
    "nee hoor",
    "nein",
    "neutraal",
    "niet echt",
    "niet nodig",
    "niet van toepassing",
    "niets",
    "niets toe te voegen",
    "niks",
    "niks speciaals",
    "niks toe te voegen",
    "n v t",
    "nvt",
    "oke",
    "ongewijzigd",
    "prima",
    "tevreden",
    "top",
    "top opleiding",
    "valt mee",
    "volgende",
    "was prima",
    "weet ik niet",
    "zie eerdere opmerking",
    "zie eerdere opmerkingen",
    "zie eerste opmerking",
    "zie vorige bericht",
    "zie vorige opmerking",
    "zie vorige opmerkingen",
    "zie voorgaande opmerking",
    # English
    "all good",
    "all is good",
    "all okay",
    "amazing",
    "do not know",
    "dont know",
    "everything is fine",
    "everything is okay",
    "fine",
    "good",
    "good job",
    "great",
    "i do not know",
    "i dont know",
    "i have no comment",
    "i have no comments",
    "i have nothing to add",
    "n a",
    "next",
    "no",
    "no answer",
    "no comment",
    "no comments",
    "no further comments",
    "no idea",
    "no opinion",
    "no thanks",
    "nope",
    "none",
    "not applicable",
    "not needed",
    "nothing",
    "nothing else",
    "nothing else to add",
    "nothing to add",
    "ok",
    "okay",
    "satisfied",
    "see earlier comment",
    "see previous comment",
    "test",
    "very good",
    "watch my other feedback",
    "yes",
    # German
    "alles gut",
    "alles ist gut",
    "alles in ordnung",
    "alles okay",
    "gut",
    "ich weiss es nicht",
    "in ordnung",
    "ja",
    "k a",
    "kein kommentar",
    "keine",
    "keine ahnung",
    "keine anmerkung",
    "keine anmerkungen",
    "keine antwort",
    "keine kommentare",
    "keine meinung",
    "nein",
    "nicht anwendbar",
    "nicht zutreffend",
    "nichts",
    "nichts hinzuzufugen",
    "passt so",
    "sehr gut",
    "weiter",
    "weiss ich nicht",
    "zufrieden",
}


def normalize_response(text) -> str:
    value = unicodedata.normalize("NFKD", str(text or ""))
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.casefold().replace("’", "").replace("'", "")
    value = re.sub(r"[_]+", " ", value)
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


_NORMALIZED_LOW_INFORMATION_RESPONSES = {
    normalized
    for response in LOW_INFORMATION_RESPONSES
    if (normalized := normalize_response(response))
}


def is_low_information_response(text) -> bool:
    normalized = normalize_response(text)
    if not normalized:
        return True
    if normalized in _NORMALIZED_LOW_INFORMATION_RESPONSES:
        return True
    if normalized.isdigit():
        return True
    if len(normalized) == 1 and normalized.isascii() and normalized.isalpha():
        return True
    return False


def response_quality(text) -> str:
    if is_low_information_response(text):
        return LOW_INFORMATION_VALUE
    return SUBSTANTIVE_VALUE
