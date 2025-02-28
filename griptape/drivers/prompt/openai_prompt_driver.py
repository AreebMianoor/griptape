import os
from typing import Optional
import openai
from attr import define, field, Factory
from griptape.artifacts import TextArtifact
from griptape.drivers import BasePromptDriver
from griptape.tokenizers import TiktokenTokenizer


@define
class OpenAiPromptDriver(BasePromptDriver):
    api_type: str = field(default=openai.api_type, kw_only=True)
    api_version: Optional[str] = field(default=openai.api_version, kw_only=True)
    api_base: str = field(default=openai.api_base, kw_only=True)
    api_key: Optional[str] = field(default=Factory(lambda: os.environ.get("OPENAI_API_KEY")), kw_only=True)
    organization: Optional[str] = field(default=openai.organization, kw_only=True)
    model: str = field(default=TiktokenTokenizer.DEFAULT_OPENAI_GPT_3_MODEL, kw_only=True)
    tokenizer: TiktokenTokenizer = field(
        default=Factory(lambda self: TiktokenTokenizer(model=self.model), takes_self=True),
        kw_only=True
    )
    user: str = field(default="", kw_only=True)

    def __attrs_post_init__(self) -> None:
        openai.api_type = self.api_type
        openai.api_version = self.api_version
        openai.api_base = self.api_base
        openai.api_key = self.api_key
        openai.organization = self.organization

    def try_run(self, value: str) -> TextArtifact:
        if self.tokenizer.is_chat():
            return self.__run_chat(value)
        else:
            return self.__run_completion(value)

    def _chat_params(self, value: str) -> dict:
        return {
            "model": self.tokenizer.model,
            "messages":  [
                {
                    "role": "user",
                    "content": value
                }
            ],
            "max_tokens":  self.tokenizer.tokens_left(value),
            "temperature":  self.temperature,
            "stop":  self.tokenizer.stop_sequences,
            "user":  self.user
        }

    def _completion_params(self, value: str) -> dict:
        return {
            "model": self.tokenizer.model,
            "prompt":  value,
            "max_tokens":  self.tokenizer.tokens_left(value),
            "temperature":  self.temperature,
            "stop":  self.tokenizer.stop_sequences,
            "user":  self.user
        }

    def __run_chat(self, value: str) -> TextArtifact:
        result = openai.ChatCompletion.create(**self._chat_params(value))

        if len(result.choices) == 1:
            return TextArtifact(
                value=result.choices[0]["message"]["content"].strip()
            )
        else:
            raise Exception("Completion with more than one choice is not supported yet.")

    def __run_completion(self, value: str) -> TextArtifact:
        result = openai.Completion.create(**self._completion_params(value))

        if len(result.choices) == 1:
            return TextArtifact(
                value=result.choices[0].text.strip()
            )
        else:
            raise Exception("Completion with more than one choice is not supported yet.")
