import pandas as pd
import argparse
import llama_index
from llama_index.core import GPTVectorStoreIndex, SimpleDirectoryReader
from llama_index.core.schema import Document
import openai
import os

openai.api_key = "hoge"

"""
poetry run python preprocess/df2json.py --file_path data/creator_data.xlsx
"""


class save_data_temp:
    def __init__(self, save_dir) -> None:
        self.id = 1
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        self.data2id = {}
    
    def add_data(self, data):
        self.data2id[data] = self.id
        with open(f"{self.save_dir}/data_{self.id}.txt", "w") as f:
            f.write(str(data))
        self.id += 1

    def del_data(self, data):
        del self.data2id[data]
        os.remove(f"{self.save_dir}/data_{self.id}.txt")

    def del_all_data(self):
        os.remove(self.save_dir)



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_path", type=str, required=True)
    return parser.parse_args()


def add_list_as_set(target_list, add_list):
    target_list += add_list
    return list(set(target_list))


def update_enterprise_data(enterprise_data, row_dict):
    pre_categories = enterprise_data["カテゴリ"]
    pre_coverage_area = enterprise_data["対応範囲"]
    pre_expression = enterprise_data["表現"]
    pre_video_info = enterprise_data["動画情報"]
    categories = row_dict["カテゴリ_1"].split("・")
    if pd.isna(row_dict["カテゴリ_2"]):
        pass
    else:
        categories += row_dict["カテゴリ_2"].split("・")
        if pd.isna(row_dict["カテゴリ_3"]):
            pass
        else:
            categories += row_dict["カテゴリ_3"].split("・")
    if pd.isna(row_dict["対応範囲"]):
        coverage_area = None
    else:
        coverage_area = row_dict["対応範囲"].split("｜")
    if pd.isna(row_dict["表現"]):
        expression = None
    else:
        expression = row_dict["表現"]
    video_info = {
        "id": len(pre_video_info) + 1,
        "動画": row_dict["動画タイトル"],
        "総額": row_dict["メンバー1_仕入れ"] + row_dict["メンバー2_仕入れ"] + row_dict["メンバー3_仕入れ"],
        "動画ジャンル": row_dict["動画ジャンル"],
        "尺": row_dict["尺"],
    }
    if pd.isna(row_dict["メンバー1_仕入れ（補足）"]):
        PIC_1 = f'{row_dict["メンバー1_名前"]}_仕入れ額:{row_dict["メンバー1_仕入れ"]}'
    else:
        PIC_1 = f'{row_dict["メンバー1_名前"]}_{row_dict["メンバー1_仕入れ（補足）"]}_仕入れ額:{row_dict["メンバー1_仕入れ"]}'
    if pd.isna(row_dict["メンバー2_名前"]):
        PIC_2 = None
    else:
        if pd.isna(row_dict["メンバー2_仕入れ（補足）"]):
            PIC_2 = f'{row_dict["メンバー2_名前"]}_仕入れ額:{row_dict["メンバー2_仕入れ"]}'
        else:
            PIC_2 = f'{row_dict["メンバー2_名前"]}_{row_dict["メンバー2_仕入れ（補足）"]}_仕入れ額:{row_dict["メンバー2_仕入れ"]}'
        if pd.isna(row_dict["メンバー3_名前"]):
            PIC_3 = None
        else:
            if pd.isna(row_dict["メンバー3_仕入れ（補足）"]):
                PIC_3 = f'{row_dict["メンバー3_名前"]}_仕入れ額:{row_dict["メンバー3_仕入れ"]}'
            else:
                PIC_3 = f'{row_dict["メンバー3_名前"]}_{row_dict["メンバー3_仕入れ（補足）"]}_仕入れ額:{row_dict["メンバー3_仕入れ"]}'
    
    if PIC_2 is not None:
        if PIC_3 is not None:
            enterprise_data["メンバー"] = add_list_as_set(enterprise_data["メンバー"], [PIC_1, PIC_2, PIC_3])
        else:
            enterprise_data["メンバー"] = add_list_as_set(enterprise_data["メンバー"], [PIC_1, PIC_2])
    else:
        enterprise_data["メンバー"] = add_list_as_set(enterprise_data["メンバー"], [PIC_1])
    enterprise_data["カテゴリー"] = add_list_as_set(pre_categories, categories)
    if pre_coverage_area is None:
        if coverage_area is None:
            pass
        else:
            enterprise_data["対応範囲"] = coverage_area
    else:
        if coverage_area is None:
            pass
        else:
            enterprise_data["対応範囲"] = add_list_as_set(pre_coverage_area, coverage_area)
    if pre_expression is None:
        if expression is None:
            pass
        else:
            enterprise_data["表現"] = add_list_as_set([expression], [])
    else:
        if expression is None:
            pass
        else:
            if type(pre_expression) == str:
                enterprise_data["表現"] = add_list_as_set([pre_expression], [expression])
            else:
                enterprise_data["表現"] = add_list_as_set(pre_expression, [expression])
    enterprise_data["動画情報"].append(video_info)
    return enterprise_data


def add_enterprise_data(enterprise_data_list, enterprise, enterprise2index, row_dict):
    if pd.isna(row_dict["メンバー1_仕入れ（補足）"]):
        PIC_1 = f'{row_dict["メンバー1_名前"]}_仕入れ額:{row_dict["メンバー1_仕入れ"]}'
    else:
        PIC_1 = f'{row_dict["メンバー1_名前"]}_{row_dict["メンバー1_仕入れ（補足）"]}_仕入れ額:{row_dict["メンバー1_仕入れ"]}'
    if pd.isna(row_dict["メンバー2_名前"]):
        PIC_2 = None
    else:
        if pd.isna(row_dict["メンバー2_仕入れ（補足）"]):
            PIC_2 = f'{row_dict["メンバー2_名前"]}_仕入れ額:{row_dict["メンバー2_仕入れ"]}'
        else:
            PIC_2 = f'{row_dict["メンバー2_名前"]}_{row_dict["メンバー2_仕入れ（補足）"]}_仕入れ額:{row_dict["メンバー2_仕入れ"]}'
    if pd.isna(row_dict["メンバー3_名前"]):
        PIC_3 = None
    else:
        if pd.isna(row_dict["メンバー3_仕入れ（補足）"]):
            PIC_3 = f'{row_dict["メンバー3_名前"]}_仕入れ額:{row_dict["メンバー3_仕入れ"]}'
        else:
            PIC_3 = f'{row_dict["メンバー3_名前"]}_{row_dict["メンバー3_仕入れ（補足）"]}_仕入れ額:{row_dict["メンバー3_仕入れ"]}'
    if enterprise not in enterprise2index:
        total_purchase = row_dict["メンバー1_仕入れ"] + row_dict["メンバー2_仕入れ"] + row_dict["メンバー3_仕入れ"]
        categories = row_dict["カテゴリ_1"].split("・")
        if pd.isna(row_dict["カテゴリ_2"]):
            pass
        else:
            categories += row_dict["カテゴリ_2"].split("・")
            if pd.isna(row_dict["カテゴリ_3"]):
                pass
            else:
                categories += row_dict["カテゴリ_3"].split("・")
        coverage_area = row_dict["対応範囲"].split("｜")
        enterprise_data = {
            "動画情報": [{
                "id" : 1,
                "動画" : row_dict["動画タイトル"],
                "総額" : total_purchase,
                "動画ジャンル": row_dict["動画ジャンル"],
                "尺": row_dict["尺"],
            }],
            "表現": row_dict["表現"],
            "対応範囲": coverage_area,
            "カテゴリ" : categories,
        }

        if PIC_2 is not None:
            if PIC_3 is not None:
                enterprise_data["メンバー"] = [PIC_1, PIC_2, PIC_3]
            else:
                enterprise_data["メンバー"] = [PIC_1, PIC_2]
        else:
            enterprise_data["メンバー"] = [PIC_1]
        enterprise2index[enterprise] = len(enterprise2index)
        enterprise_data_list.append(enterprise_data)
    else:
        enterprise_idx = enterprise2index[enterprise]
        enterprise_data = enterprise_data_list[enterprise_idx]
        enterprise_data = update_enterprise_data(enterprise_data, row_dict)
        enterprise_data_list[enterprise_idx] = enterprise_data


def add_creator_data(creator_data_list, creator2index, row_dict):
    PIC_1 = f'{row_dict["メンバー1_名前"]}_{row_dict["受注企業"]}'
    if pd.isna(row_dict["メンバー2_名前"]):
        PIC_2 = None
        PIC_3 = None
    else:
        PIC_2 = f'{row_dict["メンバー2_名前"]}_{row_dict["受注企業"]}'
        if pd.isna(row_dict["メンバー3_名前"]):
            PIC_3 = None
        else:
            PIC_3 = f'{row_dict["メンバー3_名前"]}_{row_dict["受注企業"]}'
    if pd.isna(row_dict["カテゴリ_1"]):
        categories = None
    else:
        categories = row_dict["カテゴリ_1"].split("・")
        if pd.isna(row_dict["カテゴリ_2"]):
            pass
        else:
            categories = add_list_as_set(categories, row_dict["カテゴリ_2"].split("・"))
            if pd.isna(row_dict["カテゴリ_3"]):
                pass
            else:
                categories = add_list_as_set(categories, row_dict["カテゴリ_3"].split("・"))
    if PIC_1 not in creator2index:
        creator2index[PIC_1] = len(creator2index)
        if pd.isna(row_dict["職種1"]):
            occupation = None
        else:
            occupation = [row_dict["職種1"]]
            if pd.isna(row_dict["職種2"]):
                pass
            else:
                occupation.append(row_dict["職種2"])
        id = row_dict["NO"]
        movie_data = {
            "id" : id,
            "動画" : row_dict["動画タイトル"],
            "動画URL" : row_dict["動画URL"],
            "概要" : row_dict["概要"],
            "動画ジャンル": row_dict["動画ジャンル"],
            "発注先" : row_dict["発注企業"],
            "費用" : row_dict["メンバー1_仕入れ"],
            "発注コスト" : row_dict["メンバー1_仕入れ"] + row_dict["メンバー2_仕入れ"] + row_dict["メンバー3_仕入れ"],
            "補足" : row_dict["メンバー1_仕入れ（補足）"],
            "表現" : row_dict["表現"],
            "尺": row_dict["尺"],
        }
        creator_data = {
            "名前" : row_dict["メンバー1_名前"],
            "発注企業" : row_dict["受注企業"],
            "所在地" : row_dict["所在地"],
            "職種" : occupation,
            "自己紹介" : row_dict["自己紹介"],
            "特徴/強み" : row_dict["特徴/強み"],
            "対応可能な領域" : row_dict["対応可能な領域"],
            "スキル・使用ソフト・所有機材" : row_dict["スキル・使用ソフト・所有機材"],
            "メンバー_URL" : row_dict["メンバー_URL"],
            "動画" : [movie_data],
        }
        if categories is not None:
            creator_data["動画"][0]["カテゴリ"] = categories
        creator_data_list.append(creator_data)
    else:
        creator_idx = creator2index[PIC_1]
        creator_data = creator_data_list[creator_idx]
        movie_data = {
            "id" : row_dict["NO"],
            "動画" : row_dict["動画タイトル"],
            "動画URL" : row_dict["動画URL"],
            "概要" : row_dict["概要"],
            "動画ジャンル": row_dict["動画ジャンル"],
            "発注先" : row_dict["発注企業"],
            "費用" : row_dict["メンバー1_仕入れ"],
            "発注コスト" : row_dict["メンバー1_仕入れ"] + row_dict["メンバー2_仕入れ"] + row_dict["メンバー3_仕入れ"],
            "補足" : row_dict["メンバー1_仕入れ（補足）"],
            "表現" : row_dict["表現"],
            "尺": row_dict["尺"],
        }
        creator_data["動画"].append(movie_data)
        creator_data_list[creator_idx] = creator_data
    if PIC_2 is not None:
        if PIC_2 not in creator2index:
            creator2index[PIC_2] = len(creator2index)
            movie_data["費用"] = row_dict["メンバー2_仕入れ"]
            movie_data["補足"] = row_dict["メンバー2_仕入れ（補足）"]
            creator_data = {
                "名前" : row_dict["メンバー2_名前"],
                "発注企業" : row_dict["受注企業"],
                "動画" : [movie_data],
            }
            if not pd.isna(row_dict["メンバー_URL.1"]):
                creator_data["メンバー_URL"] = row_dict["メンバー_URL.1"]
            if not pd.isna(row_dict["所在地.1"]):
                creator_data["所在地"] = row_dict["所在地.1"]
            if not pd.isna(row_dict["職種1"]):
                creator_data["職種"] = [row_dict["職種1"]]
                if not pd.isna(row_dict["職種2"]):
                    creator_data["職種"].append(row_dict["職種2"])
            if not pd.isna(row_dict["自己紹介.1"]):
                creator_data["自己紹介"] = row_dict["自己紹介.1"]
            if not pd.isna(row_dict["特徴/強み.1"]):
                creator_data["特徴/強み"] = row_dict["特徴/強み.1"]
            if not pd.isna(row_dict["対応可能な領域.1"]):
                creator_data["対応可能な領域"] = row_dict["対応可能な領域.1"]
            if not pd.isna(row_dict["スキル・使用ソフト・所有機材.1"]):
                creator_data["スキル・使用ソフト・所有機材"] = row_dict["スキル・使用ソフト・所有機材.1"]
            creator_data_list.append(creator_data)
        else:
            creator_idx = creator2index[PIC_2]
            creator_data = creator_data_list[creator_idx]
            movie_data = {
                "id" : row_dict["NO"],
                "動画" : row_dict["動画タイトル"],
                "動画URL" : row_dict["動画URL"],
                "概要" : row_dict["概要"],
                "動画ジャンル": row_dict["動画ジャンル"],
                "発注先" : row_dict["発注企業"],
                "費用" : row_dict["メンバー2_仕入れ"],
                "発注コスト" : row_dict["メンバー1_仕入れ"] + row_dict["メンバー2_仕入れ"] + row_dict["メンバー3_仕入れ"],
                "補足" : row_dict["メンバー2_仕入れ（補足）"],
                "表現" : row_dict["表現"],
                "尺": row_dict["尺"],
            }
            creator_data["動画"].append(movie_data)
            creator_data_list[creator_idx] = creator_data
    if PIC_3 is not None:
        if PIC_3 not in creator2index:
            creator2index[PIC_3] = len(creator2index)
            movie_data["費用"] = row_dict["メンバー3_仕入れ"]
            movie_data["補足"] = row_dict["メンバー3_仕入れ（補足）"]
            creator_data = {
                "名前" : row_dict["メンバー3_名前"],
                "発注企業" : row_dict["受注企業"],
                "動画" : [movie_data],
            }
            if not pd.isna(row_dict["メンバー_URL.2"]):
                creator_data["メンバー_URL"] = row_dict["メンバー_URL.2"]
            if not pd.isna(row_dict["所在地.2"]):
                creator_data["所在地"] = row_dict["所在地.2"]
            if not pd.isna(row_dict["職種1"]):
                creator_data["職種"] = [row_dict["職種1"]]
                if not pd.isna(row_dict["職種2"]):
                    creator_data["職種"].append(row_dict["職種2"])
            if not pd.isna(row_dict["自己紹介.2"]):
                creator_data["自己紹介"] = row_dict["自己紹介.2"]
            if not pd.isna(row_dict["特徴/強み.2"]):
                creator_data["特徴/強み"] = row_dict["特徴/強み.2"]
            if not pd.isna(row_dict["対応可能な領域.2"]):
                creator_data["対応可能な領域"] = row_dict["対応可能な領域.2"]
            if not pd.isna(row_dict["スキル・使用ソフト・所有機材.2"]):
                creator_data["スキル・使用ソフト・所有機材"] = row_dict["スキル・使用ソフト・所有機材.2"]
            creator_data_list.append(creator_data)
        else:
            creator_idx = creator2index[PIC_3]
            creator_data = creator_data_list[creator_idx]
            movie_data = {
                "id" : row_dict["NO"],
                "動画" : row_dict["動画タイトル"],
                "動画URL" : row_dict["動画URL"],
                "概要" : row_dict["概要"],
                "動画ジャンル": row_dict["動画ジャンル"],
                "発注先" : row_dict["発注企業"],
                "費用" : row_dict["メンバー3_仕入れ"],
                "発注コスト" : row_dict["メンバー1_仕入れ"] + row_dict["メンバー2_仕入れ"] + row_dict["メンバー3_仕入れ"],
                "補足" : row_dict["メンバー3_仕入れ（補足）"],
                "表現" : row_dict["表現"],
                "尺": row_dict["尺"],
            }
            creator_data["動画"].append(movie_data)
            creator_data_list[creator_idx] = creator_data
    return creator_data_list

def add_video_data(video_data_list, video, row_dict):
    if video not in video_data_list:
        if pd.isna(row_dict["カテゴリ_1"]):
            categories = None
        else:
            categories = row_dict["カテゴリ_1"].split("・")
            if pd.isna(row_dict["カテゴリ_2"]):
                pass
            else:
                categories = add_list_as_set(categories, row_dict["カテゴリ_2"].split("・"))
                if pd.isna(row_dict["カテゴリ_3"]):
                    pass
                else:
                    categories = add_list_as_set(categories, row_dict["カテゴリ_3"].split("・"))
        video_data = {
            "動画タイトル" : video,
            "動画URL" : row_dict["動画URL"],
            "概要" : row_dict["概要"],
            "動画ジャンル": row_dict["動画ジャンル"],
            "発注先" : row_dict["発注企業"],
            "費用" : row_dict["メンバー1_仕入れ"] + row_dict["メンバー2_仕入れ"] + row_dict["メンバー3_仕入れ"],
            "表現" : row_dict["表現"],
            "尺": row_dict["尺"],
        }
        if categories is not None:
            video_data["カテゴリ"] = categories
        if pd.isna(row_dict["メンバー1_名前"]):
            pass
        else:
            video_data["メンバー1"] = row_dict["メンバー1_名前"]
            video_data["メンバー1_仕入れ"] = row_dict["メンバー1_仕入れ"]
            video_data["メンバー1_仕入れ（補足）"] = row_dict["メンバー1_仕入れ（補足）"]
            if pd.isna(row_dict["メンバー2_名前"]):
                pass
            else:
                video_data["メンバー2"] = row_dict["メンバー2_名前"]
                video_data["メンバー2_仕入れ"] = row_dict["メンバー2_仕入れ"]
                if not pd.isna(row_dict["メンバー2_仕入れ（補足）"]):
                    video_data["メンバー2_仕入れ（補足）"] = row_dict["メンバー2_仕入れ（補足）"]
                if pd.isna(row_dict["メンバー3_名前"]):
                    pass
                else:
                    video_data["メンバー3"] = row_dict["メンバー3_名前"]
                    video_data["メンバー3_仕入れ"] = row_dict["メンバー3_仕入れ"]
                    if not pd.isna(row_dict["メンバー3_仕入れ（補足）"]):
                        video_data["メンバー3_仕入れ（補足）"] = row_dict["メンバー3_仕入れ（補足）"]
        video_data_list.append(video)
    else:
        pass
    return video_data_list



def df2json(df, save_dir="data/export_data"):
    enterprise_data_list = []
    enterprise2index = {}
    creator_data_list = []
    creator2index = {}
    video_data_list = []
    for index, row in df.iterrows():
        row_dict = row.to_dict()
        if pd.isna(row_dict["NO"]) or pd.isnull(row_dict["NO"]):
            continue
        enterprise = row_dict["受注企業"]
        video = row_dict["動画タイトル"]
        add_enterprise_data(enterprise_data_list, enterprise, enterprise2index, row_dict)
        add_creator_data(creator_data_list, creator2index, row_dict)
        add_video_data(video_data_list, video, row_dict)
    enterprise_data_list = [str(enterprise_data) for enterprise_data in enterprise_data_list]
    creator_data_list = [str(creator_data) for creator_data in creator_data_list]
    video_data_list = [str(video_data) for video_data in video_data_list]
    Data_Saver = save_data_temp(save_dir)
    for creator_data in creator_data_list:
        Data_Saver.add_data(creator_data)
    for video_data in video_data_list:
        Data_Saver.add_data(video_data)
    documents =  SimpleDirectoryReader(save_dir).load_data()
    index = GPTVectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir="data/sub")
    for enterprise_data in enterprise_data_list:
        Data_Saver.add_data(enterprise_data)
    # enterprise_data_list = [Document(str(enterprise_data)) for enterprise_data in enterprise_data_list]
    # creator_data_list = [Document(str(creator_data)) for creator_data in creator_data_list]
    # video_data_list = [Document(str(video_data)) for video_data in video_data_list]
    # creator_index = GPTVectorStoreIndex(creator_data_list)
    # enterprise_index = GPTVectorStoreIndex(enterprise_data_list)
    # video_index = GPTVectorStoreIndex(video_data_list)
    # sub_index = creator_index + video_index
    # all_index = sub_index + enterprise_index
    # sub_index.save("data/sub_index.json")
    # all_index.save("data/all_index.json")
    documents =  SimpleDirectoryReader(save_dir).load_data()
    index = GPTVectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir="data/all")


def load_data(file_path):
    return pd.read_excel(file_path)


def main():
    args = parse_args()
    df = load_data(args.file_path)
    df2json(df)


if __name__ == "__main__":
    main()
