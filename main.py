import os
import json
import re
from collections import defaultdict
import fitz  # PyMuPDF

INPUT_DIR = "input"
OUTPUT_DIR = "output"


def extract_text_metadata(pdf_path):
    doc = fitz.open(pdf_path)
    results = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if not text:
                        continue
                    font_name = span["font"]
                    is_bold = "bold" in font_name.lower()
                    results.append({
                        "text": text,
                        "font_size": span["size"],
                        "font_name": font_name,
                        "is_bold": is_bold,
                        "bbox": span["bbox"],
                        "page": page_num
                    })
    return results


def analyze_font_sizes(spans):
    freq = defaultdict(int)
    for item in spans:
        size = round(item["font_size"], 1)
        freq[size] += 1

    sorted_freq = sorted(freq.items(), key=lambda x: -x[0])

    # print("\n📊 Font Size Frequency (rounded):")
    # print(f"{'Font Size':<10} {'Count'}")
    # print("-" * 20)
    # for size, count in sorted_freq:
    #     print(f"{size:<10} {count}")

    return sorted_freq


def is_probable_table_row(text):
    words = text.split()

    if re.match(r'^\d+(\.\d+)*\s', text):
        return False

    if "–" in text or "-" in text:
        return False

    short_words = [w for w in words if len(w) <= 3]
    if len(words) >= 4 and len(short_words) >= 3:
        return True

    if re.search(r"\s{2,}", text):
        return True

    return False


def merge_heading_spans(spans, y_tolerance=8.0, x_gap_threshold=100.0):
    merged = []
    i = 0
    while i < len(spans):
        current = spans[i]
        combined_text = current["text"]
        combined_bbox = list(current["bbox"])
        j = i + 1

        while j < len(spans):
            next_span = spans[j]
            same_page = current["page"] == next_span["page"]
            size_match = abs(current["font_size"] -
                             next_span["font_size"]) <= 0.5
            line_gap = abs(next_span["bbox"][1] -
                           current["bbox"][3]) <= y_tolerance
            x_gap = next_span["bbox"][0] - current["bbox"][2]

            if (
                same_page
                and size_match
                and (
                    line_gap
                    or (0 <= x_gap <= x_gap_threshold)
                )
            ):
                combined_text += " " + next_span["text"]
                combined_bbox[2] = next_span["bbox"][2]
                combined_bbox[3] = max(combined_bbox[3], next_span["bbox"][3])
                j += 1
                current = next_span
            else:
                break

        merged.append({**spans[i], "text": combined_text,
                      "bbox": tuple(combined_bbox)})
        i = j

    return merged


def classify_headings(spans, min_h3_length=5):
    all_sizes = sorted({round(span["font_size"], 1)
                       for span in spans}, reverse=True)
    size_to_level = {}
    if len(all_sizes) > 0:
        size_to_level[all_sizes[0]] = "title"
    if len(all_sizes) > 1:
        size_to_level[all_sizes[1]] = "H1"
    if len(all_sizes) > 2:
        size_to_level[all_sizes[2]] = "H2"
    if len(all_sizes) > 3 and all_sizes[3] > min(all_sizes):
        size_to_level[all_sizes[3]] = "H3"

    title = None
    outline = []

    for span in spans:
        size = round(span["font_size"], 1)
        level = size_to_level.get(size)
        if not level:
            continue

        text = span["text"].strip()

        if len(text) > 200:
            continue
        if len(text.split()) > 20 and not re.match(r'^\d+(\.\d+)*\s', text):
            continue

        if is_probable_table_row(text):
            continue

        if level == "H3":
            if len(text.replace(" ", "")) < min_h3_length:
                continue
            if len(text.split()) < 2:
                continue
            if re.fullmatch(r'[0-9. ]+', text):
                continue
            if text.lower().startswith("page") or "table" in text.lower():
                continue

        if level == "title" and not title:
            title = text
            continue

        if text == title:
            continue

        outline.append({"level": level, "text": text, "page": span["page"]})

    if not title:
        max_size = all_sizes[0] if all_sizes else None
        if max_size:
            for span in spans:
                if round(span["font_size"], 1) == max_size:
                    fallback_title = span["text"].strip()
                    if fallback_title:
                        title = fallback_title
                        break

    return {
        "title": title if title else "Untitled Document",
        "outline": outline
    }


def clean_text(text):
    return re.sub(r'[^\w\s.-]', '', text.strip())


def save_outline_to_json(filename, classified_data):
    output_data = {
        "title": clean_text(classified_data["title"]),
        "outline": [
            {
                "level": item["level"],
                "text": clean_text(item["text"]),
                "page": item["page"]
            } for item in classified_data["outline"]
        ]
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    json_path = os.path.join(
        OUTPUT_DIR, os.path.splitext(filename)[0] + ".json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"✅ JSON saved to: {json_path}")


def main():
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            print(f"\nProcessing: {filename}")

            spans = extract_text_metadata(pdf_path)
            analyze_font_sizes(spans)
            merged_spans = merge_heading_spans(spans)
            classified = classify_headings(merged_spans)

            # print("\n📘 Title:", classified["title"])
            # print("🧾 Outline:")
            # for item in classified["outline"]:
            #     print(
            #         (
            #             f"  - {item['level']}: \"{item['text']}\" "
            #             f"(Page {item['page']})"
            #         )
            #     )

            save_outline_to_json(filename, classified)

            # print("\n🧪 Sample extracted spans:")
            # for item in merged_spans[:10]:
            #     print(item)


if __name__ == "__main__":
    main()
