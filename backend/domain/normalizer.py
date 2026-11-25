def normalize_query(raw_query: str) -> str:
    tokens = [word for word in raw_query.lower().strip().split() if word]
    return " ".join(sorted(tokens))