# -*- coding: utf-8 -*-
"""
🔒 安全API LLM加载器 (secure_LLM_api_loader)
================================================
comfyui_LLM_party 的安全配套节点。

问题：原版 `LLM_api_loader` 的 api_key 是一个文本输入框，一旦填写就会被
ComfyUI 当作节点参数存进工作流 JSON；保存图片时整个工作流会被写进 PNG
元数据，于是 api_key 随图片外泄。

本节点改为从一个**本地 JSON 文件**按「配置名称」读取 model_name/base_url/
api_key。工作流中**只保存「配置名称」这个字符串**，api_key 在运行时才从本地
文件读取，永远不会进入工作流 JSON，也就不会泄露到图片元数据里。

设计为独立插件：运行时从已安装的 comfyui_LLM_party 借用 `Chat` 类，输出
`CUSTOM` 类型的 model，可直接接到 LLM party 的 `LLM` 节点。

------------------------------------------------------------------------
Secure companion node for comfyui_LLM_party. Reads model_name/base_url/
api_key from a local JSON file by a profile name; only the profile name is
stored in the workflow, so the api_key never leaks into the workflow JSON
or PNG metadata. The Chat class is borrowed at runtime from an installed
comfyui_LLM_party, and the output is a CUSTOM "model" compatible with the
LLM node.
"""
import importlib
import json
import os
import sys

NODE_DIR = os.path.dirname(os.path.abspath(__file__))
SECURE_API_KEYS_FILENAME = "llm_api_keys.json"


def get_secure_keys_path(json_path=""):
    """返回密钥JSON文件的绝对路径。json_path 为空时使用本插件目录下的默认文件。"""
    path = (json_path or "").strip()
    if path:
        return path
    return os.path.join(NODE_DIR, SECURE_API_KEYS_FILENAME)


def load_secure_api_configs(json_path=""):
    """读取密钥文件，返回 ({配置名称: {model_name, base_url, api_key}}, 实际使用的路径)。"""
    path = get_secure_keys_path(json_path)
    if not os.path.exists(path):
        return {}, path
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[secure_llm_loader] 读取密钥文件失败 / failed to read {path}: {e}")
        return {}, path
    if not isinstance(data, dict):
        print(f"[secure_llm_loader] 密钥文件应为JSON对象 / {path} must be a JSON object")
        return {}, path
    return data, path


def _get_party_chat():
    """运行时从已安装的 comfyui_LLM_party 定位并返回 Chat 类。"""
    # 1) 优先在已加载模块里找 LLM party 的 llm 模块
    for modname, mod in list(sys.modules.items()):
        if mod is None:
            continue
        if "llm_party" in modname.lower() and modname.split(".")[-1] == "llm" and hasattr(mod, "Chat"):
            return getattr(mod, "Chat")
    # 2) 退化：任何同时具备 Chat 和 load_api_keys 的 *.llm 模块
    for modname, mod in list(sys.modules.items()):
        if mod is None:
            continue
        if modname.split(".")[-1] == "llm" and hasattr(mod, "Chat") and hasattr(mod, "load_api_keys"):
            return getattr(mod, "Chat")
    # 3) 再退化：扫 custom_nodes 目录，尝试按包名导入
    custom_nodes_dir = os.path.dirname(NODE_DIR)
    try:
        folders = os.listdir(custom_nodes_dir)
    except Exception:
        folders = []
    for name in folders:
        low = name.lower()
        if "llm_party" not in low and "llm-party" not in low:
            continue
        if not os.path.exists(os.path.join(custom_nodes_dir, name, "llm.py")):
            continue
        for pkgname in (name, name.lower()):
            try:
                mod = importlib.import_module(pkgname + ".llm")
                if hasattr(mod, "Chat"):
                    return getattr(mod, "Chat")
            except Exception:
                continue
    raise RuntimeError(
        "找不到 comfyui_LLM_party 的 Chat 类。请先安装 comfyui_LLM_party "
        "(在 ComfyUI Manager 搜索 'LLM party' 安装) 并重启 ComfyUI。\n"
        "Could not locate the Chat class. Please install comfyui_LLM_party "
        "(search 'LLM party' in ComfyUI Manager) and restart ComfyUI."
    )


class SecureLLMApiLoader:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        configs, _ = load_secure_api_configs()
        names = list(configs.keys()) or [""]
        return {
            "required": {
                "config_name": (
                    names,
                    {"tooltip": "本地JSON文件中定义的配置名称。只有这个名称会被保存进工作流，api_key 不会。"},
                ),
            },
            "optional": {
                "json_path": (
                    "STRING",
                    {
                        "default": "",
                        "tooltip": "可选：自定义密钥JSON文件的绝对路径。留空则使用本插件目录下的 llm_api_keys.json。路径本身不是机密。",
                    },
                ),
                "is_ollama": ("BOOLEAN", {"default": False, "tooltip": "本地 ollama，无需 api_key。"}),
            },
        }

    RETURN_TYPES = ("CUSTOM",)
    RETURN_NAMES = ("model",)
    OUTPUT_TOOLTIPS = ("The loaded model.",)
    DESCRIPTION = "从本地JSON文件按名称安全加载 model/base_url/api_key，避免 api_key 泄露到工作流和图片元数据中。需配合 comfyui_LLM_party 使用。"
    FUNCTION = "chatbot"

    CATEGORY = "大模型派对（llm_party）/模型加载器（model loader）"

    def chatbot(self, config_name, json_path="", is_ollama=False):
        Chat = _get_party_chat()
        if is_ollama:
            return (Chat(config_name or "ollama", "ollama", "http://127.0.0.1:11434/v1/"),)

        configs, used_path = load_secure_api_configs(json_path)
        if not configs:
            raise ValueError(
                f"未找到任何配置，请先创建密钥文件: {used_path} "
                f"(格式可参考 llm_api_keys.json.example)。"
            )
        if config_name not in configs:
            raise ValueError(
                f"配置名称 '{config_name}' 不在密钥文件 {used_path} 中。"
                f"可选名称: {', '.join(configs.keys())}"
            )
        entry = configs.get(config_name) or {}
        api_key = str(entry.get("api_key", "") or "")
        base_url = str(entry.get("base_url", "") or "")
        model_name = str(entry.get("model_name", "") or "") or config_name
        if api_key == "":
            raise ValueError(f"配置 '{config_name}' 缺少 api_key，请在 {used_path} 中填写。")
        return (Chat(model_name, api_key, base_url),)


NODE_CLASS_MAPPINGS = {
    "secure_LLM_api_loader": SecureLLMApiLoader,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "secure_LLM_api_loader": "🔒Secure API LLM Loader (local JSON)",
}
