

# import fitz  # PyMuPDF
# import json
# import os
# import re
# from collections import Counter


# def extract_outline(pdf_path):
#     """Extract title and hierarchical headings (H1–H4) from a PDF."""
#     doc = fitz.open(pdf_path)

#     # --- Title: largest meaningful span on first page ---
#     title = ""
#     spans = []
#     first = doc[0].get_text("dict")
#     for block in first["blocks"]:
#         if block.get("type") != 0: continue
#         for line in block["lines"]:
#             for span in line["spans"]:
#                 text = span["text"].strip()
#                 if len(text.split()) >= 3:
#                     spans.append({"text": text, "size": round(span["size"],1), "y": line["bbox"][1]})
#     if spans:
#         spans.sort(key=lambda x: (-x["size"], x["y"]))
#         title = spans[0]["text"]

#     # --- Gather all text spans ---
#     all_spans = []
#     sizes = []
#     for page in doc:
#         pd = page.get_text("dict")
#         for block in pd.get("blocks", []):
#             if block.get("type") != 0: continue
#             for line in block["lines"]:
#                 y = line["bbox"][1]
#                 for span in line["spans"]:
#                     txt = span["text"].strip()
#                     if not txt: continue
#                     sz = round(span["size"],1)
#                     all_spans.append({"text": txt, "size": sz, "page": page.number+1, "y": y})
#                     sizes.append(sz)

#     if not sizes:
#         return {"title": title, "outline": []}

#     # --- Cluster sizes into up to 4 levels ---
#     uniq = sorted(set(sizes), reverse=True)
#     clusters = [uniq[0]]
#     for s in uniq[1:]:
#         if s / clusters[-1] < 0.9:
#             clusters.append(s)
#         if len(clusters) == 4:
#             break

#     # --- Map cluster thresholds to H1–H4 ---
#     levels = {}
#     for i, s in enumerate(clusters):
#         levels[s] = f'H{i+1}'
#     thresholds = sorted(levels.keys(), reverse=True)

#     # --- Identify headings only ---
#     heads = []
#     for sp in all_spans:
#         # find its cluster
#         for s in thresholds:
#             if sp["size"] >= s:
#                 lvl = levels[s]
#                 heads.append({"level": lvl, "text": sp["text"], "page": sp["page"], "y": sp["y"]})
#                 break

#     # --- Merge adjacent same-level spans on same line ---
#     heads.sort(key=lambda h: (h["page"], h["y"], -ord(h["level"][1])))
#     merged = []
#     for h in heads:
#         if merged and merged[-1]["level"] == h["level"] and merged[-1]["page"] == h["page"] and abs(merged[-1]["y"] - h["y"]) < 2:
#             merged[-1]["text"] += ' ' + h["text"]
#         else:
#             merged.append(h.copy())

#     # --- Remove duplicates & boilerplate ---
#     seen = set()
#     outline = []
#     for h in merged:
#         key = (h["level"], h["text"])
#         if key in seen: continue
#         if re.match(r'^[\W_]+$', h["text"]): continue
#         seen.add(key)
#         outline.append({"level": h["level"], "text": h["text"], "page": h["page"]})

#     return {"title": title, "outline": outline}


# # --- Batch process directory ---
# if __name__ == '__main__':
#     import sys
#     if len(sys.argv) != 3:
#         print("Usage: python extract_outline.py <input_dir> <output_dir>")
#         sys.exit(1)
#     in_dir, out_dir = sys.argv[1], sys.argv[2]
#     os.makedirs(out_dir, exist_ok=True)
#     for fn in os.listdir(in_dir):
#         if not fn.lower().endswith('.pdf'): continue
#         ip = os.path.join(in_dir, fn)
#         op = os.path.join(out_dir, os.path.splitext(fn)[0] + '.json')
#         res = extract_outline(ip)
#         with open(op, 'w', encoding='utf-8') as f:
#             json.dump(res, f, indent=2, ensure_ascii=False)
#     print("Done.")



#!/usr/bin/env python3
import os, sys, json, re
import fitz  # PyMuPDF

def extract_outline(pdf_path):
    """Extract title and hierarchical headings (H1–H4) from a PDF."""
    doc = fitz.open(pdf_path)

    # --- Title: largest meaningful span on first page ---
    title = ""
    spans = []
    first = doc[0].get_text("dict")
    for block in first["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if len(text.split()) >= 3:
                    spans.append({
                        "text": text,
                        "size": round(span["size"], 1),
                        "y": line["bbox"][1]
                    })
    if spans:
        spans.sort(key=lambda x: (-x["size"], x["y"]))
        title = spans[0]["text"]

    # --- Gather all text spans ---
    all_spans = []
    sizes = []
    for page in doc:
        pd = page.get_text("dict")
        for block in pd.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                y = line["bbox"][1]
                for span in line["spans"]:
                    txt = span["text"].strip()
                    if not txt:
                        continue
                    sz = round(span["size"], 1)
                    all_spans.append({
                        "text": txt,
                        "size": sz,
                        "page": page.number + 1,
                        "y": y
                    })
                    sizes.append(sz)

    if not sizes:
        return {"title": title, "outline": []}

    # --- Cluster sizes into up to 4 levels ---
    uniq = sorted(set(sizes), reverse=True)
    clusters = [uniq[0]]
    for s in uniq[1:]:
        if s / clusters[-1] < 0.9:
            clusters.append(s)
        if len(clusters) == 4:
            break

    # --- Map cluster thresholds to H1–H4 ---
    levels = {}
    for i, s in enumerate(clusters):
        levels[s] = f'H{i+1}'
    thresholds = sorted(levels.keys(), reverse=True)

    # --- Identify headings only ---
    heads = []
    for sp in all_spans:
        for s in thresholds:
            if sp["size"] >= s:
                lvl = levels[s]
                heads.append({
                    "level": lvl,
                    "text":  sp["text"],
                    "page":  sp["page"],
                    "y":     sp["y"]
                })
                break

    # --- Merge adjacent same-level spans on same line ---
    heads.sort(key=lambda h: (h["page"], h["y"], h["level"]))
    merged = []
    for h in heads:
        if (merged and
            merged[-1]["level"] == h["level"] and
            merged[-1]["page"]  == h["page"]  and
            abs(merged[-1]["y"] - h["y"]) < 2):
            merged[-1]["text"] += ' ' + h["text"]
        else:
            merged.append(h.copy())

    # --- Remove duplicates & boilerplate; build final outline with correct key order ---
    seen = set()
    outline = []
    for h in merged:
        key = (h["level"], h["text"])
        if key in seen:
            continue
        if re.match(r'^[\W_]+$', h["text"]):
            continue
        seen.add(key)
        outline.append({
            "level": h["level"],
            "text":  h["text"],
            "page":  h["page"]
        })

    return {"title": title, "outline": outline}


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python extract_outline.py <input_dir> <output_dir>")
        sys.exit(1)
    in_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    for fn in os.listdir(in_dir):
        if not fn.lower().endswith('.pdf'):
            continue
        ip = os.path.join(in_dir, fn)
        op = os.path.join(out_dir, os.path.splitext(fn)[0] + '.json')
        res = extract_outline(ip)
        with open(op, 'w', encoding='utf-8') as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
    print("Done.")
