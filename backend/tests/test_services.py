import pytest

from app.config import settings
from app.services.image_generation import (
    ImageGenerationNotConfiguredError,
    resolve_image_provider,
)
from app.services.prompt_optimizer import (
    PromptOptimizerError,
    _parse_dual_prompt_json,
    optimize_prompt_with_rules,
)
from app.services.speech_recognition import (
    SpeechRecognitionNotConfiguredError,
    resolve_speech_provider,
)


@pytest.fixture(autouse=True)
def restore_settings():
    snapshot = {
        "speech_provider": settings.speech_provider,
        "image_provider": settings.image_provider,
        "openai_api_key": settings.openai_api_key,
        "dashscope_api_key": settings.dashscope_api_key,
    }
    yield
    settings.speech_provider = snapshot["speech_provider"]
    settings.image_provider = snapshot["image_provider"]
    settings.openai_api_key = snapshot["openai_api_key"]
    settings.dashscope_api_key = snapshot["dashscope_api_key"]


def test_resolve_speech_provider_local():
    settings.speech_provider = "local"
    settings.openai_api_key = "sk-test"
    assert resolve_speech_provider() == "local"


def test_resolve_speech_provider_openai():
    settings.speech_provider = "openai"
    assert resolve_speech_provider() == "openai"


def test_resolve_speech_provider_auto_with_openai_key():
    settings.speech_provider = "auto"
    settings.openai_api_key = "sk-test"
    settings.dashscope_api_key = None
    assert resolve_speech_provider() == "openai"


def test_resolve_speech_provider_auto_without_key():
    settings.speech_provider = "auto"
    settings.openai_api_key = None
    settings.dashscope_api_key = None
    assert resolve_speech_provider() == "local"


def test_resolve_speech_provider_auto_with_dashscope_key():
    settings.speech_provider = "auto"
    settings.dashscope_api_key = "sk-test"
    assert resolve_speech_provider() == "dashscope"


def test_resolve_speech_provider_dashscope_requires_key():
    settings.speech_provider = "dashscope"
    settings.dashscope_api_key = None
    with pytest.raises(SpeechRecognitionNotConfiguredError):
        resolve_speech_provider()


def test_resolve_speech_provider_dashscope():
    settings.speech_provider = "dashscope"
    settings.dashscope_api_key = "sk-test"
    assert resolve_speech_provider() == "dashscope"


def test_resolve_image_provider_stablehorde():
    settings.image_provider = "stablehorde"
    assert resolve_image_provider() == "stablehorde"


def test_resolve_image_provider_dashscope_requires_key():
    settings.image_provider = "dashscope"
    settings.dashscope_api_key = None
    with pytest.raises(ImageGenerationNotConfiguredError):
        resolve_image_provider()


def test_resolve_image_provider_dashscope():
    settings.image_provider = "dashscope"
    settings.dashscope_api_key = "sk-test"
    assert resolve_image_provider() == "dashscope"


def test_resolve_dashscope_image_size_square():
    from app.services.dashscope_image import resolve_dashscope_image_size

    assert resolve_dashscope_image_size(512, 512) == "1328*1328"


def test_resolve_dashscope_image_size_landscape():
    from app.services.dashscope_image import resolve_dashscope_image_size

    assert resolve_dashscope_image_size(1024, 512) == "1664*928"


def test_resolve_image_provider_openai_requires_key():
    settings.image_provider = "openai"
    settings.openai_api_key = None
    with pytest.raises(ImageGenerationNotConfiguredError):
        resolve_image_provider()


def test_optimize_prompt_with_rules_chinese_short():
    optimized_cn, optimized_en, message = optimize_prompt_with_rules("一只猫")
    assert "猫" in optimized_cn
    assert optimized_en
    assert message


def test_parse_dual_prompt_json_plain():
    content = '{"display_cn": "赛博朋克城市中的猫", "prompt_en": "a cat in cyberpunk city"}'
    display_cn, prompt_en = _parse_dual_prompt_json(content)
    assert display_cn == "赛博朋克城市中的猫"
    assert prompt_en == "a cat in cyberpunk city"


def test_parse_dual_prompt_json_codeblock():
    content = """```json
{"display_cn": "星空下的马", "prompt_en": "a horse under starry sky"}
```"""
    display_cn, prompt_en = _parse_dual_prompt_json(content)
    assert "马" in display_cn
    assert "horse" in prompt_en


def test_parse_dual_prompt_json_invalid():
    with pytest.raises(PromptOptimizerError):
        _parse_dual_prompt_json("not json at all")
