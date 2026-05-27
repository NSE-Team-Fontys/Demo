import re


def subtheme_mention_rows(subthemes: list, docs: list) -> list:
    if not subthemes or not docs:
        return []

    stopwords = {
        "and",
        "the",
        "for",
        "with",
        "from",
        "that",
        "this",
        "over",
        "into",
        "aan",
        "een",
        "het",
        "van",
        "voor",
        "met",
        "naar",
    }
    normalized_docs = [str(doc).lower() for doc in docs]
    doc_words = [
        set(re.findall(r"[a-zA-ZÀ-ÿ0-9]+", doc))
        for doc in normalized_docs
    ]
    rows = []

    for subtheme in subthemes:
        label = str(subtheme).strip()
        if not label:
            continue

        label_norm = label.lower()
        tokens = [
            token
            for token in re.findall(r"[a-zA-ZÀ-ÿ0-9]+", label_norm)
            if len(token) > 3 and token not in stopwords
        ]
        token_roots = {token[:6] for token in tokens if len(token) > 6}

        mentions = 0
        for doc, words in zip(normalized_docs, doc_words):
            if (
                label_norm in doc
                or any(token in words for token in tokens)
                or any(any(word.startswith(root) for word in words) for root in token_roots)
            ):
                mentions += 1

        rows.append(
            {
                "subtheme": label,
                "mentions": mentions,
                "doc_percentage": int(round((mentions / len(docs)) * 100)),
                "percentage": 0,
            }
        )

    total_mentions = sum(row["mentions"] for row in rows)
    if total_mentions > 0:
        for row in rows:
            row["percentage"] = int(round((row["mentions"] / total_mentions) * 100))

    return rows
