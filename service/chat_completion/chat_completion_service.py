import json
import os
from typing import Annotated, TypeVar, Type, Literal
from fastapi import Depends, Query
from openai import AsyncOpenAI
from pydantic import BaseModel, TypeAdapter

# 제네릭 타입 T를 정의합니다.
T = TypeVar("T", bound=BaseModel)
api_key = os.getenv("chat_gpt_api_key_1")


def get_openai_client() -> AsyncOpenAI:
    return AsyncOpenAI(api_key=api_key)


async def get_chat_completion_response(
        prompt: str,
        system_prompt: str = "You are a helpful assistant."
) -> str:
    openai_client = get_openai_client()
    print(f"### LLM request ### : {prompt} \n ### LLM request ### ")

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )

        print(f"LLM response: {response}")

        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return "error occured."


async def get_chat_completion_json(
        prompt: str,
        response_model: Type[T],
        system_prompt: str = "You are a helpful assistant that responds in JSON format."
) -> T:
    openai_client = get_openai_client()
    print(f"### LLM request ### : {prompt} \n ### LLM request ### ")

    try:
        response = await openai_client.chat.completions.create(
            model="gpt-5",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        json_string = response.choices[0].message.content

        print(f"LLM response: {json_string}")

        data = json.loads(json_string)
        model_fields = response_model.model_fields.keys()
        filtered_data = {key: value for key, value in data.items() if key in model_fields}
        parsed_object = response_model(**filtered_data)
        return parsed_object
    except Exception as e:
        print(f"An error occurred: {e}")
        return response_model()
