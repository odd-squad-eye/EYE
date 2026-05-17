from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import Image
import torch
import traceback

device = "cuda" if torch.cuda.is_available() else "cpu"

model_id = "microsoft/Florence-2-base"

processor = None
model = None

def load_model():
    global processor, model
    if processor is not None and model is not None:
        return

    print("Loading Florence-2 model...")

    try:
        processor = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=True
        )

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32
        ).to(device)

        print("Florence-2 loaded successfully!")
    except Exception as e:
        print("FLORENCE LOAD FAILED:")
        traceback.print_exc()
        processor = None
        model = None
        raise

def generate_caption(image: Image.Image):
    """Single-pass caption generation. No OCR step — halves inference time."""
    load_model()
    image = image.resize((384, 384))

    # Single inference pass — detailed caption only
    inputs = processor(text="<MORE_DETAILED_CAPTION>", images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=512,
            num_beams=3,
            do_sample=False
        )
    caption = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

    return f"I see: {caption}"