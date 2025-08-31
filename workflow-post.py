from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2
import dotenv
import os
from typing import Tuple, Optional
from typing_extensions import TypedDict
from pathlib import Path
from langgraph.graph import StateGraph, END

dotenv.load_dotenv()


class WorkflowState(TypedDict):
    """TypedDict for workflow state attributes"""

    image_path: str
    font_path: str
    content: str
    reference: str
    title: str
    title_box: Tuple[int, int, int, int]
    content_box: Tuple[int, int, int, int]
    reference_box: Tuple[int, int, int, int]
    output_path: str
    processed_image: Optional[np.ndarray]


def wrap_text_by_pixel(draw, text, font, max_width):
    """Wrap text to fit within specified pixel width"""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        width = draw.textlength(test_line, font=font)
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def draw_wrapped_custom_font_text_pil(
    cv2_img, text, box, font_path, font_size=40, color=(255, 0, 0), padding=10
):
    """Draw wrapped text on image with custom font"""
    x, y, w, h = box
    pil_img = Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.truetype(font_path, font_size)
    lines = wrap_text_by_pixel(draw, text, font, w - 2 * padding)
    ascent, descent = font.getmetrics()
    line_height = ascent + descent + 4
    current_y = y + padding
    for line in lines:
        if current_y + line_height > y + h:
            break
        current_x = x + padding
        draw.text((current_x, current_y), line, font=font, fill=color)
        current_y += line_height
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def process_image_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node for image processing"""
    # Load image
    image = cv2.imread(state["image_path"])

    # Apply title
    image = draw_wrapped_custom_font_text_pil(
        image, state["title"], state["title_box"], state["font_path"], font_size=100
    )

    # Apply content
    image = draw_wrapped_custom_font_text_pil(
        image, state["content"], state["content_box"], state["font_path"], font_size=40
    )

    # Apply reference
    image = draw_wrapped_custom_font_text_pil(
        image,
        state["reference"],
        state["reference_box"],
        state["font_path"],
        font_size=30,
    )

    # Return updated state
    return {**state, "processed_image": image}


def save_image_node(state: WorkflowState) -> WorkflowState:
    """LangGraph node for saving the processed image"""
    # Create output directory if it doesn't exist
    output_path = Path(state["output_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the image
    cv2.imwrite(str(output_path), state["processed_image"])
    print(f"Image saved to: {output_path}")

    # Return state unchanged (could add saved_path if needed)
    return state


def create_workflow():
    """Create the LangGraph workflow"""
    # Create the state graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("process_image", process_image_node)
    workflow.add_node("save_image", save_image_node)

    # Define the workflow edges
    workflow.set_entry_point("process_image")
    workflow.add_edge("process_image", "save_image")
    workflow.add_edge("save_image", END)

    # Compile the workflow
    return workflow.compile()


# Example usage
def run_workflow(content, reference, title):
    """Run the image processing workflow"""
    # Create initial state
    IMGPATH = os.getenv("IMGPATH", "./base.png")
    FONTPATH = os.getenv("FONTPATH", "./JetBrainsMonoNerdFontMono-BoldItalic.ttf")
    OUTPUTPATH = os.getenv("OUTPUTPATH", "./output/processed_image.png")

    initial_state: WorkflowState = {
        "image_path": IMGPATH,
        "font_path": FONTPATH,
        "content": content,
        "reference": reference,
        "title": title,
        "title_box": (150, 250, 750, 200),
        "content_box": (150, 510, 750, 470),
        "reference_box": (125, 1175, 775, 55),
        "output_path": OUTPUTPATH,
        "processed_image": None,
    }

    # Create and run workflow
    app = create_workflow()
    result = app.invoke(initial_state)

    return result
