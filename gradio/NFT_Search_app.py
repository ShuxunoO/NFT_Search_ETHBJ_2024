import gradio as gr
import pandas as pd
import requests


# 清除按钮的功能实现
def clear_text_input():
    input_text.value = ""  # 清除文本框内容
    return ""

def clear_image_input():
    input_image.clear()  # 清除图像输入
    return None

    
if __name__ == "__main__":
    

    # model_path = "/data/sswang/NFT_search/models/finetuned_models/clip/vit-l-14/epoch_latest.pt"
    # base_model_and_function = Base_Model_and_Function(model_path=model_path, GPU_ID=0)


    # top100_img_features_path = "/data/sswang/data/NFT1000_features_ETHBJ/img_gathered_features.index"
    # top100_caption_features_path = "/data/sswang/data/NFT1000_features_ETHBJ/caption_gathered_features.index"
    # top100_index_database_path = "/data/sswang/NFT_search/NFT_Search_ETHBJ_2024/data/ETHBJ_top100_extraction_projects_index.csv"
    # union_feature_and_index = Union_Feature_and_Index(top100_img_features_path, top100_caption_features_path, top100_index_database_path, GPU_ID=1)

    # 睡眠10秒，等待模型加载完成
    time.sleep(10)




    # # 加载索引
    # top100_img_feature_index = load_faiss_index_to_GPU(top100_img_features_path, GPU_ID=1)
    # top100_caption_feature_index = load_faiss_index_to_GPU(top100_caption_features_path, GPU_ID=1)

    # # 加载索引数据库
    # csv_path = "/data/sswang/data/NFT1000/top100_extraction_projects_index_v2.csv"
    # NFT_INDEX_DATABASE = pd.read_csv(csv_path)

    # feature_base_path = Path("/data/sswang/data/NFT1000_features")


    # with gr.Blocks(theme="soft") as demo:
    #     with gr.Row():
    #         with gr.Column():
    #             input_text = gr.Textbox(label="Enter Query Caption", placeholder="Enter your ideal image caption, as detailed as possible", value="", lines=9)
    #             with gr.Row():
    #                 with gr.Column():
    #                     submit_text = gr.Button("Caption search")
    #                 with gr.Column():
    #                     clear_text = gr.Button("Clear Caption")
    #         with gr.Column():
    #             input_image = gr.Image(label="Upload query image", type="pil")
    #             with gr.Row():
    #                 with gr.Column():
    #                     submit_image = gr.Button("Image Search")
    #                 with gr.Column():
    #                     clear_image = gr.Button("Clear Image")
    #     mode = gr.Radio(choices=["txt-img", "txt-txt", "img-img", "max-prob"], label="Select Processing Mode", value="max-prob")


    #     # 定义 10 个 Gallery 组件
    #     gallery_1 = gr.Gallery(label="gallery_1", height=512, object_fit="fill", columns=6, visible=True)
    #     gallery_2 = gr.Gallery(label="gallery_2", height=512, object_fit="fill", columns=6, visible=True)
    #     gallery_3 = gr.Gallery(label="gallery_3", height=512, object_fit="fill", columns=6, visible=True)
    #     gallery_4 = gr.Gallery(label="gallery_4", height=512, object_fit="fill", columns=6, visible=True)
    #     gallery_5 = gr.Gallery(label="gallery_5", height=512, object_fit="fill", columns=6, visible=True)
    #     gallery_6 = gr.Gallery(label="gallery_6", height=512, object_fit="fill", columns=6,  visible=True)
    #     gallery_7 = gr.Gallery(label="gallery_7", height=512, object_fit="fill", columns=6,  visible=True)
    #     gallery_8 = gr.Gallery(label="gallery_8", height=512, object_fit="fill", columns=6,  visible=True)
    #     gallery_9 = gr.Gallery(label="gallery_9", height=512, object_fit="fill", columns=6, visible=True)
    #     gallery_10 = gr.Gallery(label="gallery_10", height=512, object_fit="fill", columns=6, visible=True)


    #     galleries =[gallery_1, gallery_2, gallery_3, gallery_4, gallery_5, gallery_6, gallery_7, gallery_8, gallery_9, gallery_10]
        
    #     #使用回调函数更新 Gallery 组件
    #     submit_text.click(fn=process_input_text, inputs=[input_text, mode], outputs= galleries)
    #     submit_image.click(fn=process_input_img, inputs=[input_image, mode], outputs= galleries)

    #     clear_text.click(fn=clear_text_input, inputs=[], outputs=input_text)
    #     clear_image.click(fn=clear_image_input, inputs=[], outputs=input_image)


    # demo.launch(server_name='0.0.0.0', share=True)

