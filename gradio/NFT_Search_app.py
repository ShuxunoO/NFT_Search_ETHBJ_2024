import gradio as gr
import requests
from PIL import Image
import io
import json

def load_json(json_path):
    """
    以只读的方式打开json文件

    Args:
        config_path: json文件路径

    Returns:
        A dictionary

    """
    with open(json_path, 'r', encoding='UTF-8') as f:
        return json.load(f)

def process_input_text(input_text, mode, directed_search_name):
    # 设置请求数据
    caption_global_search_url = 'http://localhost:5645/caption_global_search'
    caption_directed_search_url = 'http://localhost:5645/caption_directed_search'
    data = {
        "input_caption": input_text,
        "mode": mode,
        "nft_name": directed_search_name
    }
    
    if directed_search_name == "NULL":
        url = caption_global_search_url
    else:
        url = caption_directed_search_url

    # 发送POST请求
    response = requests.post(url, json=data)

    # 打印返回结果
    if response.status_code == 200:
        # print("Response JSON:", response.json())
        return response.json()
    else:
        # print(f"Request failed with status code {response.status_code}")
        return None

def process_input_img(input_image, mode, directed_search_name):
    # 设置请求的 URL
    img_global_search_url = 'http://localhost:5645/img_global_search'
    img_directed_search_url = 'http://localhost:5645/img_directed_search'
    
    # 将 PIL 图像对象保存到一个临时缓存
    img_bytes = io.BytesIO()
    input_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    # 创建表单数据
    files = {
        'input_img': ('image.png', img_bytes, 'image/png')
    }
    data = {
        'mode': mode,
        'nft_name': directed_search_name
    }

    if directed_search_name == "NULL":
        url = img_global_search_url
        
    else:
        url = img_directed_search_url

    # 发送 POST 请求
    response = requests.post(url, files=files, data=data)

    # 打印返回结果
    if response.status_code == 200:
        print("Response JSON:", response.json())
        return response.json()
    else:
        # print(f"Request failed with status code {response.status_code}")
        return None


# 清除按钮的功能实现
def clear_text_input():
    return ""

def clear_image_input():
    return None

if __name__ == "__main__":
    ETHBJ_top100_name_list_path = "/data/sswang/NFT_search/NFT_Search_ETHBJ_2024/data/ETHBJ_top100_name_list.json"
    ETHBJ_top100_name_list = load_json(ETHBJ_top100_name_list_path).get("NFT_name")
    # 在0号位置添加NULL
    ETHBJ_top100_name_list.insert(0, "NULL")

    with gr.Blocks(theme="soft") as demo:
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
        
        # 添加下拉框
        dropdown = gr.Dropdown(label="Directed Search", choices=ETHBJ_top100_name_list, value="NULL")
        
        # 定义 10 个 Gallery 组件
        galleries = [gr.Gallery(label=f"gallery_{i}", height=512, object_fit="fill", columns=6) for i in range(1, 11)]
        
        # 使用回调函数更新 Gallery 组件
        submit_text.click(fn=process_input_text, inputs=[input_text, mode, dropdown], outputs=galleries)
        submit_image.click(fn=process_input_img, inputs=[input_image, mode, dropdown], outputs=galleries)

        clear_text.click(fn=clear_text_input, inputs=[], outputs=input_text)
        clear_image.click(fn=clear_image_input, inputs=[], outputs=input_image)

    demo.launch(server_name='0.0.0.0', share=True)
