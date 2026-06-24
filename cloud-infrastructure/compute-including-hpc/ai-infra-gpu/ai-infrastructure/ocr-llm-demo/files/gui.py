import base64
from openai import OpenAI
import gradio as gr
import magic
from pdf2image import convert_from_path
from io import BytesIO
from gradio_pdf import PDF
from PIL import Image as Pil
import shutil
import os

uploaded_files = set()

def upload_file(file):
    global uploaded_files
    if file.name in uploaded_files:
        return
    UPLOAD_FOLDER = "./pictures"
    shutil.copy(file, UPLOAD_FOLDER)
    gr.Info("File uploaded", duration=2)
    uploaded_files.add(file.name)

def update_file_explorer_2():
    return gr.FileExplorer(root_dir="./pictures")

def upload_file2(file):
    UPLOAD_FOLDER = "./pictures"
    shutil.copy(file, UPLOAD_FOLDER)
    gr.Info("File uploaded", duration=2)
    return gr.FileExplorer(root_dir="./")

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Path to your image
image_path = "./test.png"

def is_pdf(file_path):
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    return file_type == 'application/pdf'

def contact_llm(model_label,query,image_path):
 images=[]
 
# if upload_button:
#    upload_file(upload_button)

 if not image_path:
    return None, None, None

 # Getting the base64 string
 if is_pdf(image_path):
     images = convert_from_path(image_path)
     im_file = BytesIO()
     images.save(im_file, format="JPEG")
     im_bytes = im_file.getvalue()
     base64_image = base64.b64encode(im_bytes).decode('utf-8')
     image_path=im_file
     image=images
 else:
     base64_image = encode_image(image_path)
     image = Pil.open(image_path)

 if model_label=="Pixtral-12B":
      model="mistralai/Pixtral-12B-2409"
      port=str(8001)
 if model_label=="Qwen2-VL":
      model="Qwen/Qwen2-VL-7B-Instruct"
      port=str(8000)
 if model_label=="Qwen2.5-VL":
      model="Qwen/Qwen2.5-VL-7B-Instruct"
      port=str(9192)
 if model_label=="Qwen2.5-VL-72B":
      model="Qwen/Qwen2.5-VL-72B-Instruct"
      port=str(9193)
 if model_label=="Llama-3.2-Vision":
      model="meta-llama/Llama-3.2-11B-Vision-Instruct"
      port=str(8002)


 if query != "":
    text_query=query
 else:
    gr.Info("Using default Query", duration=1) 
    text_query="Extract text from picture precisely as JSON"

 client = OpenAI(
  base_url="http://localhost:"+port+"/v1",
  api_key="EMPTY"  # vLLM doesn't require an API key by default
  )
 response = client.chat.completions.create(
  model=model,       
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": text_query,
        },
        {
          "type": "image_url",
          "image_url": {
            "url":  f"data:image/jpeg;base64,{base64_image}"
          },
        },
      ],
    }
  ],
 )

 #print(response.choices[0])
 return text_query,response.choices[0], image

def get_from_url(url_input,model_label,query):
 import validators
 images=[]
 
# if upload_button:
#    upload_file(upload_button)

 valid=validators.url(url_input) 
 print (valid,url_input)

 if model_label=="Pixtral-12B":
      model="mistralai/Pixtral-12B-2409"
      port=str(8001)
 if model_label=="Qwen2-VL":
      model="Qwen/Qwen2-VL-7B-Instruct"
      port=str(8000)
 if model_label=="Qwen2.5-VL":
      model="Qwen/Qwen2.5-VL-7B-Instruct"
      port=str(9192)
 if model_label=="Qwen2.5-VL-72B":
      model="Qwen/Qwen2.5-VL-72B-Instruct"
      port=str(9193)
 if model_label=="Llama-3.2-Vision":
      model="meta-llama/Llama-3.2-11B-Vision-Instruct"
      port=str(8002)


 if query != "":
    text_query=query
 else:
    gr.Info("Using default Query", duration=1) 
    text_query="Extract text from picture precisely as JSON"

 client = OpenAI(
  base_url="http://localhost:"+port+"/v1",
  api_key="EMPTY"  # vLLM doesn't require an API key by default
  )
 response = client.chat.completions.create(
  model=model,       
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": text_query,
        },
        {
          "type": "image_url",
          "image_url": {
            "url": url_input
          },
        },
      ],
    }
  ],
 )

 #print(response.choices[0])
 return text_query,response.choices[0], None

if __name__ == "__main__":
    with gr.Blocks() as demo:
        gr.Markdown("# VLM based OCR")
        gr.Markdown("Provide an image and ask questions based on the context generated from it.")

        with gr.Row():
           with gr.Column(scale=1):
                model = gr.Dropdown(
                    ["Qwen2.5-VL", "Qwen2.5-VL-72B","Pixtral-12B", "Qwen2-VL", "Llama3.2-Vision"],
                    label="Model",
                    info="Pick the model to use"
                 )
                query_input = gr.Textbox(label="Enter your query", placeholder="Ask a question about the content")
                url_input = gr.Textbox(label="Enter image URL", placeholder="Paste image URL")
                file_explorer = gr.FileExplorer(glob="**/**", root_dir="./pictures", ignore_glob="**/__init__.py", file_count="single")
                file_upload = gr.File(file_count="single")
                submit_btn = gr.Button("Submit")

           with gr.Column(scale=1):
                query_output = gr.Textbox(label="Query")
                response_output = gr.Textbox(label="Response")
                image_output = gr.Image(type="pil")

        submit_btn.click(
                fn=contact_llm,
                inputs=[model, query_input, file_explorer],
              outputs=[query_output, response_output, image_output]
              )
        file_upload.upload(fn=upload_file2, inputs=file_upload, outputs=file_explorer).then(update_file_explorer_2, outputs=file_explorer)
        url_input.input(fn=get_from_url,inputs=[url_input,model, query_input],outputs=[query_output, response_output, image_output]
              )
# Launch the interface
url = demo.launch(share=True,auth=("opc", "H789lf4z"))

