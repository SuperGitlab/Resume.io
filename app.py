"""FastAPI 应用:托管个人主页 + 渲染 Markdown 笔记。

启动:
    uvicorn app:app --reload --port 8000
或:
    python app.py
"""
from pathlib import Path

import markdown
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="邓文瀚 · 个人主页")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# 笔记文档映射:URL slug -> (页面标题, md 文件名)
NOTES = {
    "resume": ("我的简历", "我的简历.md"),
    "weakness": ("薄弱知识点", "薄弱知识点.md"),
    "algorithm": ("智能优化算法", "智能优化算法.md"),
}

# 注意:不能使用 `extra`,它内置的 fenced_code 会抢先处理围栏代码块,
# 生成无高亮的 <pre><code>,覆盖 superfences + highlight。这里改用单独的
# 扩展来保留表格/脚注等功能,把围栏代码交给 superfences(支持任意长度围栏,
# 含薄弱知识点.md 中的 4 反引号 ````python)。
MARKDOWN_EXTENSIONS = [
    "pymdownx.superfences",
    "pymdownx.highlight",
    "pymdownx.tilde",
    "pymdownx.tasklist",
    "pymdownx.magiclink",
    "tables",
    "attr_list",
    "def_list",
    "abbr",
    "footnotes",
    "sane_lists",
    "toc",
    "admonition",
]

EXTENSION_CONFIGS = {
    "pymdownx.highlight": {
        "css_class": "codehilite",
        "guess_lang": False,
    },
}


def render_markdown(text: str) -> str:
    md = markdown.Markdown(
        extensions=MARKDOWN_EXTENSIONS,
        extension_configs=EXTENSION_CONFIGS,
    )
    return md.convert(text)


@app.get("/")
def index():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/notes/{note_id}", response_class=HTMLResponse)
def notes(note_id: str):
    if note_id not in NOTES:
        raise HTTPException(status_code=404, detail="笔记不存在")
    title, filename = NOTES[note_id]
    md_path = BASE_DIR / filename
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="文件未找到")

    md_text = md_path.read_text(encoding="utf-8")
    content = render_markdown(md_text)
    template = (BASE_DIR / "notes_template.html").read_text(encoding="utf-8")
    return (
        template
        .replace("{{ title }}", title)
        .replace("{{ content }}", content)
    )


if __name__ == "__main__":
    import uvicorn
    # 绑定 :: (IPv6 wildcard):Linux 默认双栈,同一 socket 同时接受 IPv4(127.0.0.1)
    # 与 IPv6(::1)连接,确保 localhost 在任何浏览器(多数优先 IPv6)下都能访问。
    uvicorn.run("app:app", host="::", port=8000, reload=True)
