from langchain_text_splitters import RecursiveCharacterTextSplitter


import re
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_movie_plot(plot: str, max_chars: int = 2400) -> list[str]:
    plot = plot.replace("\r\n", "\n").replace("\r", "\n").strip()

    # Split into paragraph-like blocks
    if re.search(r"\n\s*\n", plot):
        paragraphs = re.split(r"\n\s*\n", plot)
    else:
        paragraphs = plot.split("\n")

    paragraphs = [
        p.strip()
        for p in paragraphs
        if p.strip()
    ]

    # Merge small paragraphs until max_chars
    merged_chunks = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                merged_chunks.append(current)
            current = paragraph

    if current:
        merged_chunks.append(current)

    # 3. Fallback split for oversized chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chars,
        chunk_overlap=300,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    final_chunks = []

    for chunk in merged_chunks:
        if len(chunk) > max_chars:
            final_chunks.extend(splitter.split_text(chunk))
        else:
            final_chunks.append(chunk)

    return final_chunks

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2400,
    chunk_overlap=300,
    separators=["\n\n", "\n", ". ", " ", ""]
)

# chunks = text_splitter.split_text(plot)



def split_plot_into_paragraphs(plot: str) -> list[str]:
    plot = plot.replace("\r\n", "\n").replace("\r", "\n").strip()

    # Αν υπάρχουν κενές γραμμές τότε αυτές δείχνουν paragraph breaks
    if re.search(r"\n\s*\n", plot):
        paragraphs = re.split(r"\n\s*\n", plot)
    else:
        # Αλλιώς κάθε απλό newline θεωρείται paragraph break
        paragraphs = plot.split("\n")

    return [
        p.strip()
        for p in paragraphs
        if p.strip()
    ]


# split_plot_into_paragraphs(plot)