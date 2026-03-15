from pydantic import BaseModel, Field
from typing import List

class Character(BaseModel):
    name: str = Field(description="角色情感")
    emotion: str = Field(description="必须严格从以下英文单词中选择：imploring, broken, surprised, laughing, blank, showoff, proud, irritable, shy, smirk, willful, cheering, hungry, anxious, scolding, astonished, pitiful, disdain, striving, others, giggle, painful, majestic, innocent, frustrated, helpless, excited, brave, happy, shocked, eating, awkward, despair")
    text: str = Field(description="少于15字的对话文本")

class Scene(BaseModel):
    title: str = Field(description="当前场景的全局标题")
    place: str = Field(description="场景地点，必须严格从以下选择：office, beach, forest, highway, lab, Mountain, port, river, concert, fantacy, others, rooftop, stage, airport, amusementpark, bank, cinema, classroom, grassland, gym, home, hospital, kitchen, library, museum, park, playground, pool, restaurant, school, shop, station, theater, village")
    scene_type: str = Field(description="镜头类型：'single' 或 'dialogue'")
    characters: List[Character] = Field(description="角色列表")

class StoryAnalysis(BaseModel):
    scenes: List[Scene] = Field(description="根据故事发展拆分出的连续镜头列表")