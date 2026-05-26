# 模块用途：解析 .docx、.pdf 文件，提取纯文本内容

import os


def parse_docx(filepath: str) -> str:
    """解析 Word 文档，返回纯文本"""
    try:
        from docx import Document
        doc = Document(filepath)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return '\n'.join(paragraphs)
    except Exception as e:
        raise ValueError(f'无法读取 Word 文档：{e}')


def parse_pdf(filepath: str) -> str:
    """解析 PDF 文件，返回纯文本"""
    try:
        import pdfplumber
        texts = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    texts.append(text.strip())
        if not texts:
            raise ValueError('PDF 中未能提取到文字，可能是扫描件图片格式')
        return '\n'.join(texts)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f'无法读取 PDF 文件：{e}')


def parse_file(filepath: str) -> str:
    """根据文件扩展名自动选择解析方式，返回纯文本"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.docx':
        return parse_docx(filepath)
    elif ext == '.pdf':
        return parse_pdf(filepath)
    else:
        raise ValueError(f'不支持的文件格式：{ext}，请上传 .docx 或 .pdf 文件')
