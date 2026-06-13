import unittest

from src.config.response_quality import (
    LOW_INFORMATION_VALUE,
    SUBSTANTIVE_VALUE,
    is_low_information_response,
    normalize_response,
    response_quality,
)


class ResponseQualityTests(unittest.TestCase):
    def test_low_information_responses_are_detected(self) -> None:
        responses = [
            "",
            ".",
            "...",
            "oké",
            "Alles okay!",
            "geen commentaar",
            "Ik heb geen opmerkingen.",
            "Volgende",
            "Geen ervaring mee",
            "Nee hoor",
            "Ga zo door!",
            "n.v.t.",
            "weet ik niet",
            "prima",
            "No comment",
            "Next",
            "Nope",
            "Good job!",
            "Nothing else to add.",
            "I don't know",
            "all good",
            "all okay",
            "Kein Kommentar",
            "Keine Anmerkungen.",
            "Weiß ich nicht",
            "Nicht zutreffend",
            "Alles gut!",
            "N/A",
            "10",
        ]

        for response in responses:
            with self.subTest(response=response):
                self.assertTrue(is_low_information_response(response))
                self.assertEqual(response_quality(response), LOW_INFORMATION_VALUE)

    def test_meaningful_short_responses_are_preserved(self) -> None:
        responses = [
            "Alles goed, maar de docenten reageren te laat.",
            "Prima lessen en duidelijke uitleg.",
            "Nee, de begeleiding is niet voldoende.",
            "Goed rooster, behalve op vrijdag.",
            "Okay teachers, but assessment criteria are unclear.",
            "No comments about teachers because I never see them.",
            "Meer praktijklessen.",
            "Docenten",
            "Die Dozentin erklärt den Stoff sehr gut.",
            "Alles gut, aber der Stundenplan kommt zu spät.",
            "المعلم يشرح جيداً",
        ]

        for response in responses:
            with self.subTest(response=response):
                self.assertFalse(is_low_information_response(response))
                self.assertEqual(response_quality(response), SUBSTANTIVE_VALUE)

    def test_normalization_supports_dutch_accents_and_punctuation(self) -> None:
        self.assertEqual(normalize_response("  N.V.T.  "), "n v t")
        self.assertEqual(normalize_response("Oké!!!"), "oke")


if __name__ == "__main__":
    unittest.main()
