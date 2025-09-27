from http import HTTPStatus
from re import T
import time
from typing import List
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import requests
from dashscope import ImageSynthesis
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('DASHSCOPE_API_KEY')
api_url = os.getenv('DASHSCOPE_API_URL')

def draw_image(prompt: str, size: str = '512*512', model: str = "wan2.2-t2i-flash"):
    print('----sync call, please wait a moment----')
    rsp = ImageSynthesis.call(api_key=api_key,
                          model=model,
                          prompt=prompt,
                          n=1,
                          size=size)
    print('response: %s' % rsp)
    return rsp

class ImageDescription(BaseModel):
    description: str = Field(description="图片描述")
    serial: int = Field(description="图片序号")

class ImageDescriptionList(BaseModel):
    image_descriptions: List[ImageDescription] = Field(description="图片描述列表")

def generate_images(messages: str, single_image: bool = True, model: str = "qwen-turbo"):
    temperature = 0.2
    llm = ChatOpenAI(model=model, api_key=api_key, base_url=api_url, temperature=temperature)
    image_description_prompt = f"""
    重写用户描述{messages}，生成卡通风格的四格漫画。
    """ if single_image else f"""
    重写用户描述{messages}，丰富描述并按照不同镜头或时间的顺序拆解成四张图片的描述。生成图片的描述必须强调迪斯尼简笔画风格。图片描述的顺序为1-4。
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个{role}。你的任务是{image_description_prompt}，并返回图片描述和图片序号。\n{response_instructions}"),
        ("human", "{question}")
    ])
    parser = PydanticOutputParser(pydantic_object=ImageDescriptionList)
    chain = prompt | llm | parser
    response = chain.invoke({
        "role": "专业的图片生成专家",
        "response_instructions": parser.get_format_instructions(),
        "image_description_prompt": image_description_prompt,
        "question": messages})
    return response

if __name__ == "__main__":
    prompt = "我走在一条乡间的小路上，两边是绿油油的稻田，远处有一间有着精致窗户的花店，漂亮的木质门，摆放着花朵"
    image_descriptions = generate_images(prompt, True)
    image_queue = []
    for image_description in image_descriptions.image_descriptions:
        print(f"serial: {image_description.serial}, description: {image_description.description}")
        rsp = draw_image(image_description.description, size='512*512')
        image_queue.append({"serial": image_description.serial,"task_id": rsp.output.task_id,"status": rsp.output.task_status,"image_url": rsp.output.results[0].url})
    
    while len(image_queue) > 0:
        for image in image_queue:
            if image["status"] == "SUCCEEDED":
                print(f"serial: {image['serial']}, image_url: {image['image_url']}")
                with open(f"./images/{image['serial']}.png", "wb") as f:
                    headers = {"Authorization": f"Bearer {api_key}"}
                    f.write(requests.get(image['image_url'], headers=headers).content)
                image_queue.remove(image)
            else:
                print(f"serial: {image['serial']}, status: {image['status']} , please wait...")
        print(f"image_queue: {image_queue}, sleep 3 seconds...")
        time.sleep(3)
