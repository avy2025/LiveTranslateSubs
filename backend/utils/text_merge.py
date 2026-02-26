def merge_overlap(prev_text, new_text):
    """
    Intelligently merges two overlapping text segments.
    Example:
    Previous: "Mera naam"
    New: "naam Ranjan hai"
    Result: "Mera naam Ranjan hai"
    """
    if not prev_text:
        return new_text
    if not new_text:
        return prev_text

    prev_words = prev_text.split()
    new_words = new_text.split()

    overlap = 0
    # Try to find the longest overlap at the end of prev and start of new
    for i in range(min(len(prev_words), len(new_words))):
        if prev_words[-(i+1):] == new_words[:i+1]:
            overlap = i+1

    merged = prev_text + " " + " ".join(new_words[overlap:])
    return merged.strip()
