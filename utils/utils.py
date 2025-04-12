def split_text(text: str, max_length: int = 4096) -> list[str]:
    parts = []
    while len(text) > 0:
        if len(text) > max_length:
            split_at = text.rfind(' ', 0, max_length)
            if split_at == -1:
                split_at = max_length
            parts.append(text[:split_at])
            text = text[split_at:].lstrip()
        else:
            parts.append(text)
            break

    return parts
