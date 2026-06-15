# 🔒 ComfyUI Secure LLM API Loader

A tiny **companion node** for [comfyui_LLM_party](https://github.com/heshengtao/comfyui_LLM_party)
that stops your **API key from leaking through image (PNG) metadata**.

> 中文说明见下方 [中文](#中文)。

## The problem

`comfyui_LLM_party`'s stock `☁️API LLM加载器 (LLM_api_loader)` exposes `api_key`
as a **text widget**. Once you type your key there, ComfyUI saves it into the
workflow JSON — and ComfyUI embeds the *entire workflow* into the **PNG metadata**
of every image you generate. Share that image and you share your key.

## The fix

This node (`🔒 Secure API LLM Loader`) reads `model_name / base_url / api_key`
from a **local JSON file**, selected by a **profile-name dropdown**. Only the
profile name is stored in the workflow; the key is resolved at runtime and
**never touches the workflow JSON or the PNG metadata**.

Its output is a `CUSTOM` "model" object, fully compatible with the
`☁️API LLM通用链路 (LLM)` node — just wire it in where you used the old loader.

## Requirements

- **[comfyui_LLM_party](https://github.com/heshengtao/comfyui_LLM_party) must be installed.**
  This node borrows the `Chat` class from it at runtime. Install it from ComfyUI
  Manager (search "LLM party") if you haven't.

## Install

### Via ComfyUI Manager (recommended)
Search for **"Secure LLM API Loader"** in ComfyUI Manager → Install → restart ComfyUI.

### Via git
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/R0smontis/comfyui_secure_llm_loader.git
```
Then restart ComfyUI.

## Usage

1. In this node's folder, copy `llm_api_keys.json.example` to `llm_api_keys.json`.
2. Fill in your providers:
   ```json
   {
     "my-deepseek": {
       "model_name": "deepseek-chat",
       "base_url": "https://api.deepseek.com/v1/",
       "api_key": "sk-your-real-key"
     }
   }
   ```
   - The top-level key (`"my-deepseek"`) is the **dropdown label** and the *only*
     thing stored in the workflow.
   - `model_name` is the real model id sent to the API (defaults to the label if omitted).
3. **Restart ComfyUI** (a new node needs a restart; later JSON edits only need a page refresh to update the dropdown).
4. Add `🔒Secure API LLM Loader` (under *LLM party → model loader*), pick a profile, and wire its `model` output into the `LLM` node.

### Options
- `json_path` (optional): absolute path to a custom key file. Leave empty to use
  `llm_api_keys.json` next to this node. **Tip:** put the key file *outside* the
  ComfyUI folder for extra safety. The path itself is not a secret.
- `is_ollama` (optional): local ollama, no api_key needed.

## Security notes
- `llm_api_keys.json` is gitignored and stores keys in **plaintext** — never pack
  or share that file. Share only workflows and images.
- Even with this node, double-check that any image you share contains no key in
  its metadata.
- If a key was ever saved into a workflow/image before, treat it as compromised
  and rotate it.

## License
AGPL-3.0, matching the upstream comfyui_LLM_party (this node depends on its code
at runtime). Original project © heshengtao.

---

## 中文

为避免 **api_key 通过图片(PNG)元数据泄露**，本节点是 [comfyui_LLM_party](https://github.com/heshengtao/comfyui_LLM_party)
的安全配套小插件。

原版 `☁️API LLM加载器` 的 `api_key` 是文本输入框，填了就会被存进工作流 JSON，
而 ComfyUI 保存图片时会把整个工作流写进 PNG 元数据 → key 随图外泄。

本节点（`🔒Secure API LLM Loader`）改为从**本地 JSON 文件**按「配置名称」读取
`model_name/base_url/api_key`，工作流里**只保存配置名称**，api_key 运行时才读，
绝不进工作流、不进图片元数据。输出是 `CUSTOM` 类型 model，直接接到 `LLM` 节点。

**前提**：必须先装 `comfyui_LLM_party`（本插件运行时借用它的 `Chat` 类）。

**安装**：ComfyUI Manager 搜 “Secure LLM API Loader” 安装，或 `git clone` 到
`custom_nodes`，重启即可。

**使用**：把 `llm_api_keys.json.example` 复制为 `llm_api_keys.json` 填好 key →
重启 ComfyUI → 在 *大模型派对 → 模型加载器* 里找到本节点 → 下拉选配置 →
`model` 接到 `LLM` 节点。`json_path` 可指向 ComfyUI 目录外的密钥文件更安全。

**安全**：`llm_api_keys.json` 已 gitignore，明文存 key，切勿分享该文件；分享工作流/
图片前确认元数据里没有 key；曾经存进工作流/图片的 key 视为已泄露，请及时重置。
