
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

ETHBJ_top100_name_list_path = "/data/sswang/NFT_search/NFT_Search_ETHBJ_2024/data/ETHBJ_top100_name_list.json"
ETHBJ_top100_name_list = load_json(ETHBJ_top100_name_list_path).get("NFT_name")



# 在0号位置添加NULL
ETHBJ_top100_name_list.insert(0, "NULL")

print(ETHBJ_top100_name_list)