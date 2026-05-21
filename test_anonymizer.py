"""
Test script: checks whether the anonymizer removes all known names from text.
Run from the Demo/ directory:  python test_anonymizer.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.core.layers.privacy_pipeline import process_chunk_sync

# Names taken directly from the real dataset (gen_nse_100.py)
KNOWN_NAMES = [
    "Emma de Vries",
    "Liam Janssen",
    "Sophie Bakker",
    "Noah Pietersen",
    "Julia van den Berg",
    "Daan Smits",
    "Fleur Willems",
    "Lars de Boer",
    "Marieke Hendricks",
    "Sander Meijer",
    "Roos Vermeer",
    "Joris van Dijk",
    "Anouk Brouwer",
    "Tim Visser",
    "Lotte Mulder",
    "Maximilian Schneider",
    "Maria Gonzalez",
    "Yuki Tanaka",
    "Carlos Ferreira",
    "Priya Sharma",
]

# Sentence templates mirroring the real data templates
_TEMPLATES = [
    "Ik ben {name} en ik vind dat de opleiding beter moet.",
    "Mijn naam is {name} en ik wil feedback geven over de docenten.",
    "Als {name} wil ik aandacht vragen voor de studielast.",
    "Ik, {name}, heb vier keer geprobeerd een afspraak te maken.",
    "Student {name} vraagt om betere begeleiding dit jaar.",
    "I am {name} and I think the programme needs improvement.",
    "My name is {name} and I want to highlight the teaching quality.",
    "As {name} I feel the workload this semester is very high.",
    "I, {name}, would appreciate better communication about changes.",
    "Feedback van {name}: de opleiding mist een duidelijke rode draad.",
]


def _build_test_cases():
    cases = []
    for name in KNOWN_NAMES:
        for tmpl in _TEMPLATES:
            cases.append((name, tmpl.format(name=name)))
    return cases  # list of (name, sentence)


def _name_still_present(name: str, text: str) -> list[str]:
    """Return which parts of the name are still visible in text."""
    found = []
    # Check full name
    if name.lower() in text.lower():
        found.append(name)
        return found  # full name leaked, no need to check parts

    # Check meaningful individual parts (skip short particles like de/van)
    for part in name.split():
        if len(part) > 3 and part.lower() in text.lower():
            found.append(part)
    return found


def run_tests(layers: list | None = None) -> bool:
    if layers is None:
        layers = ["presidio", "eu-pii"]

    layer_config = {"names": True, "locations": True, "pii": True, "titles": True}
    test_cases = _build_test_cases()

    print(f"\nLayers: {layers}")
    print(f"Names tested: {len(KNOWN_NAMES)}")
    print(f"Sentences tested: {len(test_cases)}\n")

    originals = [sentence for _, sentence in test_cases]
    anonymized = process_chunk_sync(originals, layer_config, layers)

    failures = []
    for (name, original), result in zip(test_cases, anonymized):
        leaked = _name_still_present(name, result)
        if leaked:
            failures.append({"name": name, "leaked": leaked, "original": original, "output": result})

    passed = len(test_cases) - len(failures)
    print(f"Results: {passed}/{len(test_cases)} passed")

    if failures:
        print(f"\nFAILURES: {len(failures)} sentences still contain a name\n" + "-" * 60)
        for f in failures:
            print(f"  Name expected to be removed : {f['name']}")
            print(f"  Part(s) still visible       : {f['leaked']}")
            print(f"  Original : {f['original']}")
            print(f"  Output   : {f['output']}")
            print()
    else:
        print("\nAll names were successfully anonymized!")

    return len(failures) == 0


# Unusual/rare names that are unlikely to be in any training dataset.
# These test whether the models detect names by pattern (capitalization, context)
# rather than by memorizing known names.
UNUSUAL_NAMES = [
    # Fictional Dutch-style names
    "Bramwijn Koetsveld",
    "Zelda Quispenberg",
    "Norbert Flikweert",
    "Hedwig Ploegmakers",
    "Wulfric van Slagteren",
    "Sixtus Groeneveldt",
    "Trijntje Buskermolen",
    "Aldert van Schaffelaar",
    "Fenneke Rijsbergen",
    "Gijsbert Wolthuis",

    # Fictional international names
    "Xanthippe Drovinski",
    "Tavish Blunderbeck",
    "Solange Kretzschmar",
    "Onyekachi Abubafor",
    "Caoimhe Wielopolski",
    "Zbigniew Przetocki",
    "Luthando Ntombifikile",
    "Radoslaw Chrzanowski",
    "Ekundayo Obafemi",
    "Sigríður Björnsdóttir",

    # Unusual but realistic Dutch names
    "Rombout Haverkamp",
    "Willemijntje de Rooij",
    "Christoffel Vanderputten",
    "Apollonia Schreveling",
    "Methodius van den Bogaert",

    # Mixed/uncommon first names with common last names
    "Zephyr Jansen",
    "Oberon de Wit",
    "Thessaly Visser",
    "Crispin Bakker",
    "Isolde Smit",

    # Names with unusual capitalisation patterns (tussenvoegsel edge cases)
    "Hadewych van der Vlught",
    "Everardus den Hartog",
    "Wenceslaus op den Brink",
    "Cunegonde van Steenbergen",
    "Leocadia ter Horst",
]


def run_unusual_name_tests(layers: list | None = None) -> bool:
    if layers is None:
        layers = ["presidio", "eu-pii"]

    layer_config = {"names": True, "locations": True, "pii": True, "titles": True}
    test_cases = [(name, tmpl.format(name=name)) for name in UNUSUAL_NAMES for tmpl in _TEMPLATES]

    print(f"\n--- Unusual/rare name test ---")
    print(f"Names tested: {len(UNUSUAL_NAMES)}")
    print(f"Sentences tested: {len(test_cases)}\n")

    originals = [sentence for _, sentence in test_cases]
    anonymized = process_chunk_sync(originals, layer_config, layers)

    failures = []
    for (name, original), result in zip(test_cases, anonymized):
        leaked = _name_still_present(name, result)
        if leaked:
            failures.append({"name": name, "leaked": leaked, "original": original, "output": result})

    passed = len(test_cases) - len(failures)
    print(f"Results: {passed}/{len(test_cases)} passed")

    if failures:
        print(f"\nFAILURES: {len(failures)} sentences still contain a name\n" + "-" * 60)
        for f in failures:
            print(f"  Name expected to be removed : {f['name']}")
            print(f"  Part(s) still visible       : {f['leaked']}")
            print(f"  Original : {f['original']}")
            print(f"  Output   : {f['output']}")
            print()
    else:
        print("\nAll unusual names were successfully anonymized!")

    return len(failures) == 0


if __name__ == "__main__":
    ok1 = run_tests()
    print("\n" + "=" * 60)
    ok2 = run_unusual_name_tests()
    sys.exit(0 if (ok1 and ok2) else 1)
