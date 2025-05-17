
import cv2
import pytesseract
import numpy as np
from PIL import Image
import os

# Set up tesseract if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def load_image(image_path):
    return cv2.imread(image_path)

def extract_text_blocks(image):
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    n_boxes = len(data['level'])

    boxes = []
    for i in range(n_boxes):
        # if int(data['conf'][i]) > 30:  # confidence threshold
        (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
        text = data['text'][i].strip()
        if text:
            boxes.append({'x': x, 'y': y, 'w': w, 'h': h, 'text': text})
            # Draw rectangle around the text
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.imshow('Text Detection', image)
    cv2.waitKey(0)
    return boxes

# def merge_vertically(boxes, y_threshold=100):
#     boxes = sorted(boxes, key=lambda b: b['y'])
#     groups = []
#     current_group = [boxes[0]]

#     for i in range(1, len(boxes)):
#         prev = current_group[-1]
#         curr = boxes[i]
#         if abs(curr['y'] - (prev['y'] + prev['h'])) < y_threshold:
#             if curr['y'] + curr['h'] < prev['y'] + prev['h']:
#                 print(f"Swapping {prev['text']} with {curr['text']}")
#                 temp = prev
#                 current_group.pop()
#                 current_group.append(curr)
#                 current_group.append(temp)
#             else:
#                 current_group.append(curr)
#         else:
#             groups.append(current_group)
#             current_group = [curr]
#     groups.append(current_group)
#     return groups

# def merge_vertically(boxes, y_threshold=150, x_offset_threshold=100):
#     boxes = sorted(boxes, key=lambda b: (b['y'], b['x']))
#     groups = []
#     current_group = [boxes[0]]

#     for i in range(1, len(boxes)):
#         prev = current_group[-1]
#         curr = boxes[i]
#         # Check for vertical proximity
#         vertical_close = abs(curr['y'] - (prev['y'] + prev['h'])) < y_threshold
#         # Check for horizontal offset (question number)
#         horizontal_offset = curr['x'] + 5 < min(b['x'] for b in current_group) - x_offset_threshold

#         if horizontal_offset:
#             print("HORIZONTAL OFFSET")
#             groups.append(current_group)
#             current_group = [curr]
#         elif vertical_close:
#             current_group.append(curr)
#         else:
#             groups.append(current_group)
#             current_group = [curr]
#     groups.append(current_group)
#     return groups

def merge_vertically(boxes, y_threshold=150, x_offset_threshold=100):
    boxes = sorted(boxes, key=lambda b: (b['y'], b['x']))
    groups = []
    current_group = [boxes[0]]

    for i in range(1, len(boxes)):
        prev = current_group[-1]
        curr = boxes[i]
        vertical_close = abs(curr['y'] - (prev['y'] + prev['h'])) < y_threshold

        # Find the second smallest x in the current group
        x_values = sorted(set(b['x'] for b in current_group))
        if len(x_values) > 1:
            second_min_x = x_values[1]
        else:
            second_min_x = x_values[0]

        horizontal_offset = curr['x'] + 5 < second_min_x - x_offset_threshold

        if horizontal_offset:
            print("HORIZONTAL OFFSET (second min x)")
            groups.append(current_group)
            current_group = [curr]
        elif vertical_close:
            current_group.append(curr)
        else:
            groups.append(current_group)
            current_group = [curr]
    groups.append(current_group)
    return groups

def is_question_start(group):
    text = ' '.join([b['text'] for b in group]).lower()
    return (text.startswith(tuple(str(i) for i in range(1, 21))) or
            '(a)' in text or '(i)' in text)

def save_question_images(image, groups, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    count = 1
    for group in groups:
        if not is_question_start(group):
            continue
        x1 = min(b['x'] for b in group)
        y1 = min(b['y'] for b in group)
        x2 = max(b['x'] + b['w'] for b in group)
        y2 = max(b['y'] + b['h'] for b in group)

        crop = image[y1:y2+10, x1:x2+10]
        cv2.imwrite(os.path.join(output_dir, f"question_{count}.png"), crop)
        count += 1

def process_page(image_path, output_dir):
    image = load_image(image_path)
    boxes = extract_text_blocks(image)
    groups = merge_vertically(boxes)
    save_question_images(image, groups, output_dir)

# Example
process_page("input/page_1.png", "output/questions")
