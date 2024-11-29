import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from llama_index.core import load_index_from_storage, StorageContext
from llama_index.core import PromptTemplate
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
import openai
# from openai import OpenAI
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--storage_dir", type=str, required=True)
    parser.add_argument("--openai_api_key", type=str, required=True)
    return parser.parse_args()

# 検索機能
# def extract_conditions_from_query(query, client):
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": f"Extract the filtering conditions from the following query: '{query}'"}
#         ]
#     )
#     conditions = response.choices[0].message.content
#     print(conditions)
#     hoge
#     return conditions


# def find_most_similar_question(df, user_query):
#     vectorizer = TfidfVectorizer()
#     print(df.keys())
#     hoge
#     tfidf_matrix = vectorizer.fit_transform(df['質問'])
#     user_query_vector = vectorizer.transform([user_query])
#     cosine_similarities = cosine_similarity(user_query_vector, tfidf_matrix)
#     most_similar_index = cosine_similarities.argmax()
#     return df.iloc[most_similar_index]['回答']

# 応答生成
def generate_response(openai_api_key, search_result):
    openai.api_key = openai_api_key
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"次の質問に対する回答を生成してください: {search_result}",
        max_tokens=50
    )
    return response.choices[0].text.strip()


def apply_conditions_to_df(df, conditions):
    for condition in conditions.split(","):
        key, value = condition.split("=")
        df = df[df[key] == value]
    return df


def custom_chat_engine(index):
    custom_prompt = PromptTemplate(
    """\
    会話（人間とアシスタントの間）と人間からのフォローアップメッセージを元に、\
    フォローアップメッセージを会話のすべての関連する文脈を含む単独の質問に書き直してください。

    <チャット履歴>
    {chat_history}

    <フォローアップメッセージ>
    {question}

    <単独の質問>
    """)

    # list of `ChatMessage` objects
    custom_chat_history = [
        ChatMessage(
        role=MessageRole.USER,
        content="あなたはいくつかのクリエイターと彼らが作った作品について知っています。\
                これから質問をします。あなたの回答は包括的であり、ユーザーにとって最適な\
                クリエイターや動画、そしてそれに付随する多くの情報を提供することが期待されます。\
                そしてそれは以下の文脈と矛盾しないものでなければなりません。関連がない場合は\
                無視してください。",
    ),
    ChatMessage(role=MessageRole.ASSISTANT, content="もちろん、お手伝いします。"),
    ]
    query_engine = index.as_query_engine(similarity_top_k=5)
    chat_engine = CondenseQuestionChatEngine.from_defaults(
    query_engine=query_engine,
    condense_question_prompt=custom_prompt,
    chat_history=custom_chat_history,
    verbose=True,
    )
    return chat_engine



# Chatbotフロー
def chatbot(dir_path):
    llm = OpenAI(chat_engine="gpt-4o")
    Settings.llm = llm
    # lm_predictor = LLMPredictor(llm=llm)
    storage_context = StorageContext.from_defaults(persist_dir=dir_path)
    index = load_index_from_storage(storage_context)
    chat_engine = custom_chat_engine(index)
    while True:
        # User's follow-up question
        follow_up_message = input("質問を入力してください: ")
        # Execute the query
        response = chat_engine.chat(follow_up_message)
        # Print the response
        print("Response:", response)
    # chat_engine = index.as_chat_engine()
    # query_engine = index.as_query_engine(similarity_top_k=5)
    # print(query_engine.query(user_query))
    # conditions = extract_conditions_from_query(user_query, client)
    # filterd_creators = apply_conditions_to_df(df, conditions)
    # search_result = find_most_similar_question(df, user_query)
    hoge
    # response = generate_response(openai_api_key, search_result)
    return response


def main():
    args = parse_args()
    chatbot(args.storage_dir)


if __name__ == "__main__":
    main()
