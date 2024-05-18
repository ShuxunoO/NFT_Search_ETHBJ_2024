import gradio as gr
import pandas as pd
import requests

def process_input_text(input_text, mode):
    # 设置请求数据
    url = 'http://localhost:5645/caption_global_search'
    data = {
        "input_caption": input_text,
        "mode": mode
    }

    # 发送POST请求
    response = requests.post(url, json=data)

    # 打印返回结果
    if response.status_code == 200:
        print("Response JSON:", response.json())
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}")
        return None

def process_input_img(input_image, mode):
    # 设置请求数据
    url = 'http://localhost:5645/image_global_search'
    data = {
        "input_image": input_image,
        "mode": mode
    }

    # 发送POST请求
    response = requests.post(url, json=data)

    # 打印返回结果
    if response.status_code == 200:
        print("Response JSON:", response.json())
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}")
        return None
        
# 清除按钮的功能实现
def clear_text_input():
    input_text.value = ""  # 清除文本框内容
    return ""

def clear_image_input():
    input_image.clear()  # 清除图像输入
    return None

    
if __name__ == "__main__":
    


    with gr.Blocks(theme="default") as demo:
        with gr.Row():
            with gr.Column():
                input_text = gr.Textbox(label="Enter Query Caption", placeholder="Enter your ideal image caption, as detailed as possible", value="", lines=9)
                with gr.Row():
                    with gr.Column():
                        submit_text = gr.Button("Caption search")
                    with gr.Column():
                        clear_text = gr.Button("Clear Caption")
            with gr.Column():
                input_image = gr.Image(label="Upload query image", type="pil")
                with gr.Row():
                    with gr.Column():
                        submit_image = gr.Button("Image Search")
                    with gr.Column():
                        clear_image = gr.Button("Clear Image")
        mode = gr.Radio(choices=["txt-img", "txt-txt", "img-img", "max-prob"], label="Select Processing Mode", value="max-prob")


        # 定义 10 个 Gallery 组件
        gallery_1 = gr.Gallery(label="gallery_1", height=512, object_fit="fill", columns=6, visible=True)
        gallery_2 = gr.Gallery(label="gallery_2", height=512, object_fit="fill", columns=6, visible=True)
        gallery_3 = gr.Gallery(label="gallery_3", height=512, object_fit="fill", columns=6, visible=True)
        gallery_4 = gr.Gallery(label="gallery_4", height=512, object_fit="fill", columns=6, visible=True)
        gallery_5 = gr.Gallery(label="gallery_5", height=512, object_fit="fill", columns=6, visible=True)
        gallery_6 = gr.Gallery(label="gallery_6", height=512, object_fit="fill", columns=6,  visible=True)
        gallery_7 = gr.Gallery(label="gallery_7", height=512, object_fit="fill", columns=6,  visible=True)
        gallery_8 = gr.Gallery(label="gallery_8", height=512, object_fit="fill", columns=6,  visible=True)
        gallery_9 = gr.Gallery(label="gallery_9", height=512, object_fit="fill", columns=6, visible=True)
        gallery_10 = gr.Gallery(label="gallery_10", height=512, object_fit="fill", columns=6, visible=True)


        galleries =[gallery_1, gallery_2, gallery_3, gallery_4, gallery_5, gallery_6, gallery_7, gallery_8, gallery_9, gallery_10]
        
        #使用回调函数更新 Gallery 组件
        submit_text.click(fn=process_input_text, inputs=[input_text, mode], outputs= galleries)
        submit_image.click(fn=process_input_img, inputs=[input_image, mode], outputs= galleries)

        clear_text.click(fn=clear_text_input, inputs=[], outputs=input_text)
        clear_image.click(fn=clear_image_input, inputs=[], outputs=input_image)


    demo.launch(server_name='0.0.0.0', share=True)

