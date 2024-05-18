import numpy as np
import torch
import csv
import json
from pathlib import Path
from PIL import Image
import open_clip
import faiss
import pandas as pd
import os
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

os.environ["CUDA_VISIBLE_DEVICES"] = "6,7"

class Base_Model_and_Function():
    """
    基础模型和功能类。
    
    """
    def __init__(self, model_path, GPU_ID = 0, tokenizer_type = "ViT-L-14"):
        self.GPU_ID = GPU_ID
        self.device = torch.device(f"cuda:{self.GPU_ID}" if torch.cuda.is_available() else "cpu")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(tokenizer_type, pretrained=model_path, device=self.device)
        self.tokenizer = open_clip.get_tokenizer(tokenizer_type)
        self.model.to(self.device)

    def extract_txt_features(self, input_text):
        """
        提取文本特征。

        """
        text = self.tokenizer(input_text).cuda(device=self.device)
        with torch.no_grad(), torch.cuda.amp.autocast():
            text_features = self.model.encode_text(text)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            return text_features

    def extract_img_features(self, input_image):
        """
        提取图片特征。
        """
        img = self.preprocess(input_image).unsqueeze(0).cuda(device=self.device)
        with torch.no_grad(), torch.cuda.amp.autocast():
            image_features = self.model.encode_image(img)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            return image_features

class Union_Feature_and_Index():
    def __init__(self,top100_img_features_path, top100_caption_features_path, top100_index_database_path, GPU_ID=1):
        self.GPU_ID = GPU_ID
        self.top100_img_feature_index = load_faiss_index_to_GPU(top100_img_features_path, GPU_ID=self.GPU_ID)
        self.top100_caption_feature_index = load_faiss_index_to_GPU(top100_caption_features_path, GPU_ID=self.GPU_ID)
        self.NFT_INDEX_DATABASE = pd.read_csv(top100_index_database_path)

class Process_Input_Caption():
    def __init__(self, feature_base_path, union_feature_and_index, GPU_ID=0):
        self.feature_base_path = Path(feature_base_path)
        self.top100_img_feature_index = union_feature_and_index.top100_img_feature_index
        self.top100_caption_feature_index = union_feature_and_index.top100_caption_feature_index
        self.NFT_INDEX_DATABASE = union_feature_and_index.NFT_INDEX_DATABASE
        self.GPU_ID = GPU_ID

    def txt_search(self, input_features, mode, img_feature_index = None, caption_feature_index = None, k=100):
        """
        文本-图片搜索。
        将输入的文本作为查询进行搜索，返回搜索结果。

        Args:
            input_features (torch.Tensor): 输入的文本特征
            mode (str): 搜索模式
            img_feature_index (faiss.Index): 图片特征索引
            caption_feature_index (faiss.Index): 文本特征索引
            k (int): 返回结果数量

        Return:
            list: 搜索结果列表，其中每一项为一个（索引，概率）样式的元组
        
        """
        if mode == "txt-img":
            P_img, I_img = img_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
            search_results = list(zip(I_img[0], P_img[0]))

        elif mode == "txt-txt":
            P_caption, I_caption = caption_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
            search_results = list(zip(I_caption[0], P_caption[0]))

        elif mode == "max-prob":
            P_img, I_img = img_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
            P_caption, I_caption = caption_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
            
            # 以索引为key，概率为value，构建字典
            txt_img_search_result = {k: v for k, v in zip(I_img[0], P_img[0])}
            txt_caption_search_result = {k: v for k, v in zip(I_caption[0], P_caption[0])}
            
            # 取出图文搜索与文文搜索的交集
            intersection = set(txt_img_search_result.keys()) & set(txt_caption_search_result.keys())
            
            # 取出交集中的索引，计算两个搜索结果的概率最大值为最终结果
            result = {}
            for idx in intersection:
                result[idx] = max(txt_img_search_result[idx], txt_caption_search_result[idx])

            # 从txt_img_search_result与txt_caption_search_result中取出交集以外的索引
            img_search_result = {k: v for k, v in txt_img_search_result.items() if k not in intersection}
            caption_search_result = {k: v for k, v in txt_caption_search_result.items() if k not in intersection}

            # 汇总结果列表，其中每一项为一个（索引，概率）样式的元组
            search_results = list(result.items()) + list(img_search_result.items()) + list(caption_search_result.items())

            # 按概率降序排列
            search_results.sort(key=lambda x: x[1], reverse=True)
        else:
            raise ValueError("Invalid mode")
        
        return search_results[:k]

    # 定义在全局索引中检索的函数,也就是第一阶段搜索
    def stage1_search(self, input_caption_features, mode, k=2048):
        search_results = self.txt_search(input_caption_features, mode, img_feature_index = self.top100_img_feature_index, caption_feature_index = self.top100_caption_feature_index, k = k)
        NFT_name_list = self.NFT_INDEX_DATABASE["NFT_name"]
        # 概率聚合
        aggregated_prob = aggregate_probability(search_results, NFT_name_list)
        return aggregated_prob

    def stage2_search(self, aggregated_prob, input_caption_features, mode, k=30):
        show_data = []
        # 第二阶段搜索
        for item in aggregated_prob[:10]:
            show_data_item = []
            NFT_name = item[0]
            result_data = text_search_within_a_collection(input_caption_features, self.feature_base_path, NFT_name, mode, k, GPU_ID=self.GPU_ID)
            # 将NFT内部搜索的结果加入到展示数据中
            show_data.append(result_data)
        # 如果show_data长度少于10，补充空数据
        while len(show_data) < 10:
            show_data.append([])

        return show_data

def load_faiss_index_to_GPU(index_path, GPU_ID=0):
    """
    加载faiss索引到指定序号的GPU上。

    Args:
        index_path (str): 索引路径

    Returns:
        faiss.Index: 索引对象

    """
    # 先加载进内存
    CPU_index = faiss.read_index(index_path)
    # 将索引加载到指定GPU上
    GPU_index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), GPU_ID, CPU_index)
    return GPU_index

def aggregate_probability(search_results, index_NFT_name_list):
    """
    聚合搜索结果中的概率，返回最终的搜索结果。

    Args:
        search_results (list): 搜索结果列表，其中每一项为一个（索引，概率）样式的元组
        index_NFT_name_list (pandas.dataframe): 索引与NFT名称的对应关系

    Return:
        list: 最终的搜索结果列表，其中每一项为一个（NFT名称，概率之和）样式的元组

    """
    final_results = {}
    for item in search_results:
        index = item[0]
        prob = item[1]
        NFT_name = index_NFT_name_list.iloc[index]
        if NFT_name not in final_results.keys():
            final_results[NFT_name] = prob
    #将结果转为list
    final_results = list(final_results.items())
    #按概率降序排列后返回
    final_results.sort(key=lambda x: x[1], reverse=True)
    return final_results

def txt_search(input_features, mode, img_feature_index = None, caption_feature_index = None, k=30):
    """
    文本-图片搜索。
    将输入的文本作为查询进行搜索，返回搜索结果。

    Args:
        input_features (torch.Tensor): 输入的文本特征
        mode (str): 搜索模式
        img_feature_index (faiss.Index): 图片特征索引
        caption_feature_index (faiss.Index): 文本特征索引
        k (int): 返回结果数量

    Return:
        list: 搜索结果列表，其中每一项为一个（索引，概率）样式的元组
    
    """
    if mode == "txt-img":
        P_img, I_img = img_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
        search_results = list(zip(I_img[0], P_img[0]))

    elif mode == "txt-txt":
        P_caption, I_caption = caption_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
        search_results = list(zip(I_caption[0], P_caption[0]))

    elif mode == "max-prob":
        P_img, I_img = img_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
        P_caption, I_caption = caption_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
        
        # 以索引为key，概率为value，构建字典
        txt_img_search_result = {k: v for k, v in zip(I_img[0], P_img[0])}
        txt_caption_search_result = {k: v for k, v in zip(I_caption[0], P_caption[0])}
        
        # 取出图文搜索与文文搜索的交集
        intersection = set(txt_img_search_result.keys()) & set(txt_caption_search_result.keys())
        
        # 取出交集中的索引，计算两个搜索结果的概率最大值为最终结果
        result = {}
        for idx in intersection:
            result[idx] = max(txt_img_search_result[idx], txt_caption_search_result[idx])

        # 从txt_img_search_result与txt_caption_search_result中取出交集以外的索引
        img_search_result = {k: v for k, v in txt_img_search_result.items() if k not in intersection}
        caption_search_result = {k: v for k, v in txt_caption_search_result.items() if k not in intersection}

        # 汇总结果列表，其中每一项为一个（索引，概率）样式的元组
        search_results = list(result.items()) + list(img_search_result.items()) + list(caption_search_result.items())

        # 按概率降序排列
        search_results.sort(key=lambda x: x[1], reverse=True)
    else:
        raise ValueError("Invalid mode")
    
    return search_results[:k]

def text_search_within_a_collection(input_caption_features, feature_base_path, nft_name, mode, k=30, GPU_ID=0):
    """
    在指定的NFT内部进行文本搜索。
    
    """
    feature_base_path = Path(feature_base_path)
    result_data = []
    # 加载对应的图片和caption索引
    img_feature_index_path = feature_base_path.joinpath(nft_name, "image_features.index").as_posix()
    img_feature_index = load_faiss_index_to_GPU(img_feature_index_path, GPU_ID=GPU_ID)
    caption_feature_index_path = feature_base_path.joinpath(nft_name, "caption_features.index").as_posix()
    caption_feature_index = load_faiss_index_to_GPU(caption_feature_index_path, GPU_ID=GPU_ID)
    search_results = txt_search(input_caption_features, mode, img_feature_index, caption_feature_index, k)   
    # 加载索引数据库
    csv_path = feature_base_path.joinpath(nft_name, nft_name + "_index.csv").as_posix()
    database_item = pd.read_csv(csv_path)

    # 按照索引取出图片路径，caption, NFT名称 和 token_ID
    for item in search_results:
        index = item[0]
        token_ID = database_item.iloc[index]['token_ID']
        prob = item[1]
        img_path = database_item.iloc[index]['filepath']
        caption = database_item.iloc[index]['caption']
        result_data.append((img_path, f"Token_ID: {nft_name}#{token_ID} | Probability: {prob} | Caption: {caption}"))
    return result_data


def process_input_text(input_caption=None, mode="txt-img"):
    """
    处理文本输入并返回图片及其信息。
    """

    # 第一阶段搜索
    k1 = 2048
    input_text_features = extract_txt_features(input_caption)
    search_results = txt_search(input_text_features, mode, img_feature_index = top100_img_feature_index, caption_feature_index = top100_caption_feature_index, k = k1)
    NFT_name_list = NFT_INDEX_DATABASE["NFT_name"]

    # 概率聚合
    aggregated_prob = aggregate_probability(search_results, NFT_name_list)
    show_data = []

    # 遍历聚合结果，进行二次检索
    for item in aggregated_prob[:10]:
        show_data_item = []
        NFT_name = item[0]
        # 加载对应的图片和caption索引
        img_feature_index_path = feature_base_path.joinpath(NFT_name, "image_features.index").as_posix()
        img_feature_index = load_faiss_index_to_GPU(img_feature_index_path, GPU_ID=0)
        caption_feature_index_path = feature_base_path.joinpath(NFT_name, "caption_features.index").as_posix()
        caption_feature_index = load_faiss_index_to_GPU(caption_feature_index_path, GPU_ID=0)

        # 第二阶段搜索
        k2 = 30
        search_results = txt_search(input_text_features, mode, img_feature_index, caption_feature_index, k2)
        
        # 加载索引数据库
        csv_path = feature_base_path.joinpath(NFT_name, NFT_name + "_index.csv").as_posix()
        database_item = pd.read_csv(csv_path)

        # 按照索引取出图片路径，caption, NFT名称 和 token_ID
        for item in search_results:
            index = item[0]
            token_ID = database_item.iloc[index]['token_ID']
            prob = item[1]
            img_path = database_item.iloc[index]['filepath']
            caption = database_item.iloc[index]['caption']
            NFT_name = database_item.iloc[index]['NFT_name']
            show_data_item.append((img_path, f"Token_ID: {NFT_name}#{token_ID} | Probability: {prob} | Caption: {caption}"))

        # 将NFT内部搜索的结果加入到展示数据中
        show_data.append(show_data_item)
    # 如果show_data长度少于10，补充空数据
    while len(show_data) < 10:
        show_data.append([])

    return show_data


def process_input_img(input_img=None, mode="img-img"):
    """
    处理图像输入并返回图片及其信息。
    """
    # 第一阶段搜索
    k1 = 2048
    input_img_features = extract_img_features(input_img)
    search_results = img_search(input_img_features, mode, img_feature_index = top100_img_feature_index, caption_feature_index = top100_caption_feature_index, k = k1)
    NFT_name_list = NFT_INDEX_DATABASE["NFT_name"]

    # 概率聚合
    aggregated_prob = aggregate_probability(search_results, NFT_name_list)
    show_data = []

    # 遍历聚合结果，进行二次检索
    for item in aggregated_prob[:10]:
        show_data_item = []
        NFT_name = item[0]
        # 加载对应的图片和caption索引
        img_feature_index_path = feature_base_path.joinpath(NFT_name, "image_features.index").as_posix()
        img_feature_index = load_faiss_index_to_GPU(img_feature_index_path, GPU_ID=0)
        caption_feature_index_path = feature_base_path.joinpath(NFT_name, "caption_features.index").as_posix()
        caption_feature_index = load_faiss_index_to_GPU(caption_feature_index_path, GPU_ID=0)

        # 第二阶段搜索
        k2 = 30
        search_results = img_search(input_img_features, mode, img_feature_index, caption_feature_index, k2)
        
        # 加载索引数据库
        csv_path = feature_base_path.joinpath(NFT_name, NFT_name + "_index.csv").as_posix()
        database_item = pd.read_csv(csv_path)

        # 按照索引取出图片路径，caption, NFT名称 和 token_ID
        for item in search_results:
            index = item[0]
            token_ID = database_item.iloc[index]['token_ID']
            prob = item[1]
            img_path = database_item.iloc[index]['filepath']
            caption = database_item.iloc[index]['caption']
            NFT_name = database_item.iloc[index]['NFT_name']
            show_data_item.append((img_path, f"Token_ID: {NFT_name}#{token_ID} | Probability: {prob} | Caption: {caption}"))

        # 将NFT内部搜索的结果加入到展示数据中
        show_data.append(show_data_item)

    return show_data

def img_search(input_features, mode, img_feature_index = None, caption_feature_index = None, k=30):
    """
    图像-图片搜索。
    将输入的图片作为查询进行搜索，返回搜索结果。

    Args:
        input_features (torch.Tensor): 输入的图片特征
        mode (str): 搜索模式
        img_feature_index (faiss.Index): 图片特征索引
        caption_feature_index (faiss.Index): 文本特征索引
        k (int): 返回结果数量

    Return:
        list: 搜索结果列表，其中每一项为一个（索引，概率）样式的元组
    
    """

    if mode == "txt-img":
        P_caption, I_caption = caption_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
        search_results = list(zip(I_caption[0], P_caption[0]))


    elif mode == "img-img":
        P_img, I_img = img_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
        search_results = list(zip(I_img[0], P_img[0]))

    elif mode == "max-prob":
        P_img, I_img = img_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
        P_caption, I_caption = caption_feature_index.search(input_features.cpu().numpy().astype('float32'), k)
        
        # 以索引为key，概率为value，构建字典
        txt_img_search_result = {k: v for k, v in zip(I_img[0], P_img[0])}
        txt_caption_search_result = {k: v for k, v in zip(I_caption[0], P_caption[0])}
        
        # 取出图文搜索与文文搜索的交集
        intersection = set(txt_img_search_result.keys()) & set(txt_caption_search_result.keys())
        
        # 取出交集中的索引，计算两个搜索结果的概率最大值为最终结果
        result = {}
        for idx in intersection:
            result[idx] = max(txt_img_search_result[idx], txt_caption_search_result[idx])

        # 从txt_img_search_result与txt_caption_search_result中取出交集以外的索引
        img_search_result = {k: v for k, v in txt_img_search_result.items() if k not in intersection}
        caption_search_result = {k: v for k, v in txt_caption_search_result.items() if k not in intersection}

        # 汇总结果列表，其中每一项为一个（索引，概率）样式的元组
        search_results = list(result.items()) + list(img_search_result.items()) + list(caption_search_result.items())

        # 按概率降序排列
        search_results.sort(key=lambda x: x[1], reverse=True)
    else:
        raise ValueError("Invalid mode")
    
    return search_results[:k]



@app.route('/caption_global_search', methods=['POST'])
def caption_global_search():
    # 解析出用户输入的文本和搜索模式
    data = request.json
    input_caption = data.get('input_caption')
    mode = data.get('mode')
    # 处理用户输入的文本词汇
    input_caption_features = base_model_and_function.extract_txt_features(input_caption)
    # 第一阶段搜索
    aggregated_prob = process_input_caption.stage1_search(input_caption_features, mode)
    # 第二阶段搜索
    show_data = process_input_caption.stage2_search(aggregated_prob, input_caption_features, mode)
    # return show_data
    return jsonify(show_data)

@app.route('/caption_directed_search', methods=['POST'])
def caption_directed_search():
    # 解析出用户输入的文本和搜索模式
    data = request.json
    input_caption = data.get('input_caption')
    mode = data.get('mode')
    nft_name = data.get('nft_name')
    # 处理用户输入的文本词汇
    input_caption_features = base_model_and_function.extract_txt_features(input_caption)
    # 第二阶段搜索
    show_data = text_search_within_a_collection(input_caption_features, feature_base_path, nft_name, mode)
    # return show_data
    return jsonify(show_data)

feature_base_path = "/data/sswang/data/NFT1000_features_ETHBJ"
model_path = "/data/sswang/NFT_search/models/finetuned_models/clip/vit-l-14/epoch_latest.pt"

base_model_and_function = Base_Model_and_Function(model_path=model_path, GPU_ID=0)

top100_img_features_path = "/data/sswang/data/NFT1000_features_ETHBJ/img_gathered_features.index"
top100_caption_features_path = "/data/sswang/data/NFT1000_features_ETHBJ/caption_gathered_features.index"
top100_index_database_path = "/data/sswang/NFT_search/NFT_Search_ETHBJ_2024/data/ETHBJ_top100_extraction_projects_index.csv"

union_feature_and_index = Union_Feature_and_Index(top100_img_features_path, top100_caption_features_path, top100_index_database_path, GPU_ID=1)

process_input_caption = Process_Input_Caption(feature_base_path, union_feature_and_index, GPU_ID=0)

if __name__ == "__main__":
    
    app.run(host='0.0.0.0', port=5645)


    # # # 睡眠10秒，等待模型加载完成
    # # time.sleep(10)
    # input_caption = "A picture of BoredApeYachtClub, containing Silver Hoop Earring Orange Background Robot Fur Striped Tee Clothes Discomfort Mouth X Eyes Eyes."
    # # mode = "txt-img"
    # # mode = "txt-txt"
    # mode = "max-prob"
    # result = caption_search_2_stage(input_caption, base_model_and_function, process_input_caption)
    # print(result)