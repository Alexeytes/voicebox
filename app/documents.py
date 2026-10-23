from __future__ import annotations

import io
import re
import zipfile
from html.parser import HTMLParser
from xml.etree import ElementTree

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx",
    ".epub",
    ".fb2",
    ".odt",
    ".html",
    ".htm",
    ".rtf",
    ".md",
    ".markdown",
}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "head"}:
            self.skip += 1
        elif tag in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "head"} and self.skip:
            self.skip -= 1
        elif tag in {"p", "div", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def text(self):
        return "\n".join(line.strip() for line in "".join(self.parts).splitlines() if line.strip())


def extract_text(filename: str, content: bytes) -> str:
    extension = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Формат не поддерживается: TXT, PDF, DOCX, EPUB, FB2, ODT, HTML, RTF или Markdown."
        )
    if extension == ".txt":
        for encoding in ("utf-8-sig", "utf-8", "cp1251"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("Не удалось определить кодировку TXT-файла.")
    if extension in {".html", ".htm"}:
        parser = _TextExtractor()
        parser.feed(content.decode("utf-8", errors="replace"))
        return parser.text()
    if extension in {".md", ".markdown"}:
        source = content.decode("utf-8-sig", errors="replace")
        source = re.sub(r"!?\[([^\]]+)\]\([^)]*\)", r"\1", source)
        return re.sub(r"[*_~\x60#>]", "", source)
    if extension == ".rtf":
        source = content.decode("cp1252", errors="replace")
        source = re.sub(r"\\par[d]?\b", "\n", source)
        source = re.sub(r"\\'[0-9a-fA-F]{2}", " ", source)
        source = re.sub(r"\\[a-zA-Z]+-?\d* ?|\\[^a-zA-Z]", "", source)
        return re.sub(r"[{}]", "", source)
    if extension == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader
        try:
            reader = PdfReader(io.BytesIO(content))
            if len(reader.pages) > 1000:
                raise ValueError("В PDF больше 1000 страниц.")
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Не удалось прочитать PDF-файл.") from exc
    if extension == ".fb2":
        try:
            root = ElementTree.fromstring(content)
        except ElementTree.ParseError as exc:
            raise ValueError("Не удалось прочитать FB2-книгу.") from exc
        blocks = []
        for node in root.iter():
            if node.tag.rsplit("}", 1)[-1] in {"p", "v", "subtitle", "text-author", "date"}:
                value = " ".join("".join(node.itertext()).split())
                if value:
                    blocks.append(value)
        return "\n\n".join(blocks)
    if extension in {".docx", ".epub", ".odt"}:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 100 * 1024 * 1024:
                    raise ValueError("Архив книги слишком большой после распаковки.")
                if extension == ".odt":
                    root = ElementTree.fromstring(archive.read("content.xml"))
                    blocks = []
                    for node in root.iter():
                        if node.tag.rsplit("}", 1)[-1] in {"p", "h"}:
                            value = " ".join("".join(node.itertext()).split())
                            if value:
                                blocks.append(value)
                    return "\n\n".join(blocks)
                if extension == ".docx":
                    root = ElementTree.fromstring(archive.read("word/document.xml"))
                    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                    blocks = []
                    for paragraph in root.findall(".//w:p", ns):
                        value = "".join(node.text or "" for node in paragraph.findall(".//w:t", ns))
                        if value.strip():
                            blocks.append(value)
                    return "\n\n".join(blocks)
                container = ElementTree.fromstring(archive.read("META-INF/container.xml"))
                rootfile = container.find(
                    ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
                )
                if rootfile is None:
                    raise ValueError("В EPUB не найдена основная книга.")
                opf_path = rootfile.attrib["full-path"]
                opf = ElementTree.fromstring(archive.read(opf_path))
                ns = {"opf": "http://www.idpf.org/2007/opf"}
                manifest = {
                    item.attrib["id"]: item.attrib["href"]
                    for item in opf.findall(".//opf:manifest/opf:item", ns)
                }
                spine = [
                    item.attrib["idref"] for item in opf.findall(".//opf:spine/opf:itemref", ns)
                ]
                base = opf_path.rsplit("/", 1)[0] if "/" in opf_path else ""
                sections = []
                for item_id in spine:
                    href = manifest.get(item_id)
                    if not href:
                        continue
                    root = ElementTree.fromstring(archive.read((base + "/" + href).lstrip("/")))
                    blocks = []
                    for node in root.iter():
                        if node.tag.rsplit("}", 1)[-1] in {
                            "p",
                            "h1",
                            "h2",
                            "h3",
                            "li",
                            "blockquote",
                        }:
                            value = " ".join("".join(node.itertext()).split())
                            if value:
                                blocks.append(value)
                    if not blocks:
                        value = " ".join("".join(root.itertext()).split())
                        if value:
                            blocks = [value]
                    sections.append("\n\n".join(blocks))
                return "\n\n".join(section for section in sections if section.strip())
        except ValueError:
            raise
        except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
            raise ValueError("Файл книги повреждён или имеет неверный формат.") from exc
    return ""
