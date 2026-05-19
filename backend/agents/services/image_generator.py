import os
import re
import uuid
from pathlib import Path

import graphviz
from django.conf import settings
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()


def _media_root():
    root = getattr(settings, "MEDIA_ROOT", None)
    if root:
        return Path(root)
    return Path(settings.BASE_DIR) / "media"


IMAGE_OUTPUT_DIR = _media_root() / "generated_images"
IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _detect_content_type(text):
    text_lower = text.lower()

    process_keywords = [
        "step", "steps", "phase", "phases", "first", "then",
        "next", "finally", "start", "end", "process", "workflow",
        "خطوة", "خطوات", "مرحلة", "مراحل", "ثم", "أخيرًا"
    ]

    category_keywords = [
        "type", "types", "category", "categories", "kind", "kinds",
        "class", "classes", "group", "groups",
        "نوع", "أنواع", "تصنيف", "تصنيفات", "قسم", "أقسام"
    ]

    process_score = sum(1 for word in process_keywords if word in text_lower)
    category_score = sum(1 for word in category_keywords if word in text_lower)

    if process_score > category_score:
        return "flowchart"

    return "mindmap"


def _clean_line(line):
    line = line.strip()

    if line.startswith(("-", "*", "•")):
        line = line[1:].strip()

    line = re.sub(r"^\d+[\.\)]\s*", "", line)

    return line


def _parse_hierarchy(text):
    lines = [line for line in text.splitlines() if line.strip()]

    tree = []
    stack = [(-1, tree)]

    for line in lines:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        clean_text = _clean_line(stripped)

        if not clean_text:
            continue

        node = {
            "label": clean_text,
            "children": [],
        }

        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()

        parent_list = stack[-1][1]
        parent_list.append(node)

        stack.append((indent, node["children"]))

    return tree


def _escape_label(text):
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
    )


def _build_dot_graph(tree, diagram_type, title):
    dot_lines = ["digraph G {"]

    if diagram_type == "flowchart":
        dot_lines.append("  rankdir=LR;")
        dot_lines.append('  node [shape=box, style="rounded,filled", fillcolor="#E8F4FF", color="#5AB3EE", fontname="Arial", fontsize=12];')
        dot_lines.append('  edge [color="#6B7280", arrowhead=vee];')
    else:
        dot_lines.append("  rankdir=TB;")
        dot_lines.append('  node [shape=box, style="rounded,filled", fillcolor="#FDF0E1", color="#EC8079", fontname="Arial", fontsize=12];')
        dot_lines.append('  edge [color="#6B7280"];')

    root_label = _escape_label(title or "Main Concept")
    dot_lines.append(f'  root [label="{root_label}", fillcolor="#FEB2B4", color="#EC8079", fontsize=16];')

    node_count = 0

    def add_nodes(nodes, parent_id):
        nonlocal node_count

        for node in nodes:
            node_id = f"node_{node_count}"
            node_count += 1

            label = _escape_label(node["label"])
            dot_lines.append(f'  {node_id} [label="{label}"];')
            dot_lines.append(f"  {parent_id} -> {node_id};")

            if node["children"]:
                add_nodes(node["children"], node_id)

    add_nodes(tree, "root")
    dot_lines.append("}")
    return "\n".join(dot_lines)


def _structure_text_for_diagram(text):
    """
    Uses GPT to convert normal educational content into an indented hierarchy.
    Graphviz then renders the hierarchy into a diagram.
    """
    prompt = f"""
Convert the following educational content into a clean indented hierarchy suitable for a mind map or flowchart.

Rules:
- Keep the same language as the input.
- Return plain text only.
- Do not use markdown.
- Use indentation with two spaces for child items.
- Keep labels short and clear.
- Do not add unrelated information.

Content:
{text}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You structure educational content for diagram generation."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        structured = response.choices[0].message.content.strip()
        return structured or text

    except Exception:
        return text


def generate_image_from_text(prompt, learning_style="visual"):
    """
    Generates an educational diagram or mind map from text using:
    - GPT for structuring content
    - Graphviz for rendering the PNG diagram

    Return:
    {
        "success": True,
        "image_path": "generated_images/example.png",
        "message": "..."
    }
    """

    if not prompt or not prompt.strip():
        return {
            "success": False,
            "image_path": None,
            "message": "لا يوجد نص كافٍ لإنشاء صورة تعليمية.",
        }

    try:
        structured_prompt = _structure_text_for_diagram(prompt)
        diagram_type = _detect_content_type(structured_prompt)
        tree = _parse_hierarchy(structured_prompt)

        if not tree:
            return {
                "success": False,
                "image_path": None,
                "message": "لم يتم العثور على محتوى منظم لإنشاء المخطط.",
            }

        file_name = f"{uuid.uuid4().hex}_diagram"
        output_base = IMAGE_OUTPUT_DIR / file_name

        title = "Learning Diagram"
        dot_source = _build_dot_graph(tree, diagram_type, title)

        dot = graphviz.Source(dot_source)
        output_path = dot.render(str(output_base), format="png", cleanup=True)

        relative_path = f"generated_images/{Path(output_path).name}"

        return {
            "success": True,
            "image_path": relative_path,
            "message": "تم إنشاء المخطط التعليمي بنجاح.",
        }

    except Exception as exc:
        return {
            "success": False,
            "image_path": None,
            "message": f"حدث خطأ أثناء إنشاء الصورة: {exc}",
        }
