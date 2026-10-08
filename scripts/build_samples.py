"""生成脱敏样本。税号和发票号码都是虚构的。"""

from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "samples" / "data"
BUYER_ID = "91330000MA0000002Y"
SELLER_ID = "91330000MA0000001X"
BUYER_NAME = "示例购买方"
SELLER_NAME = "示例销售方"
CODE = "1090511030000000000"

OFD_SHELL = """<?xml version="1.0" encoding="UTF-8"?>
<ofd:OFD xmlns:ofd="http://www.ofdspec.org/2016" Version="1.0">
  <ofd:DocBody>
    <ofd:DocInfo><ofd:Title>sample</ofd:Title></ofd:DocInfo>
  </ofd:DocBody>
</ofd:OFD>
"""


def english_xml(
    number: str,
    issue_date: str,
    kind: str,
    amount: str,
    tax: str,
    total: str,
    name: str,
    spec: str,
    unit: str,
    quantity: str,
    price: str,
    rate: str,
    code: str,
    drawer: str,
    red: bool = False,
) -> str:
    kind_label = "增值税专用发票" if kind == "专用" else "普通发票"
    red_block = ""
    if red:
        red_block = """
    <UndefinedLabel>
      <Label><LabelName>红字发票</LabelName></Label>
    </UndefinedLabel>"""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<EInvoice>
  <Header>
    <EIid>{number}</EIid>
    <InherentLabel>
      <GeneralOrSpecialVAT><LabelName>{kind_label}</LabelName></GeneralOrSpecialVAT>
    </InherentLabel>{red_block}
  </Header>
  <EInvoiceData>
    <SellerInformation>
      <SellerIdNum>{SELLER_ID}</SellerIdNum>
      <SellerName>{SELLER_NAME}</SellerName>
    </SellerInformation>
    <BuyerInformation>
      <BuyerIdNum>{BUYER_ID}</BuyerIdNum>
      <BuyerName>{BUYER_NAME}</BuyerName>
    </BuyerInformation>
    <BasicInformation>
      <TotalAmWithoutTax>{amount}</TotalAmWithoutTax>
      <TotalTaxAm>{tax}</TotalTaxAm>
      <TotalTax-includedAmount>{total}</TotalTax-includedAmount>
      <RequestTime>{issue_date}</RequestTime>
      <Drawer>{drawer}</Drawer>
    </BasicInformation>
    <IssuItemInformation>
      <ItemName>{name}</ItemName>
      <SpecMod>{spec}</SpecMod>
      <MeaUnits>{unit}</MeaUnits>
      <Quantity>{quantity}</Quantity>
      <UnPrice>{price}</UnPrice>
      <Amount>{amount}</Amount>
      <TaxRate>{rate}</TaxRate>
      <ComTaxAm>{tax}</ComTaxAm>
      <TaxClassificationCode>{code}</TaxClassificationCode>
    </IssuItemInformation>
  </EInvoiceData>
</EInvoice>
"""


def pinyin_xml() -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<EInvoice>
  <Fphm>24330000000000000002</Fphm>
  <Kprq>2026-10-02</Kprq>
  <Fppz>普通</Fppz>
  <Gmfmc>{BUYER_NAME}</Gmfmc>
  <Gmfnsrsbh>{BUYER_ID}</Gmfnsrsbh>
  <Xsfmc>{SELLER_NAME}</Xsfmc>
  <Xsfnsrsbh>{SELLER_ID}</Xsfnsrsbh>
  <Hjje>200.00</Hjje>
  <Hjse>6.00</Hjse>
  <Jshj>206.00</Jshj>
  <Kpr>李四</Kpr>
  <Details>
    <Item>
      <Spmc>咨询服务</Spmc>
      <Ggxh>标准</Ggxh>
      <Dw>次</Dw>
      <Sl>1</Sl>
      <Dj>200.00</Dj>
      <Je>200.00</Je>
      <Slv>3%</Slv>
      <Se>6.00</Se>
      <Spbm>3040301990000000000</Spbm>
    </Item>
  </Details>
</EInvoice>
"""


def text_pdf(lines: list[str]) -> bytes:
    chars: list[str] = []
    for line in lines:
        for char in line:
            if char not in chars:
                chars.append(char)
    mapping = {char: index + 1 for index, char in enumerate(chars)}
    bfchars = "\n".join(f"<{mapping[char]:04X}> <{ord(char):04X}>" for char in chars)
    cmap = f"""/CIDInit /ProcSet findresource begin
12 dict begin
begincmap
/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def
/CMapName /Adobe-Identity-UCS def
/CMapType 2 def
1 begincodespacerange
<0000> <FFFF>
endcodespacerange
{len(chars)} beginbfchar
{bfchars}
endbfchar
endcmap
CMapName currentdict /CMap defineresource pop
end
end
""".encode("ascii")
    commands = ["BT", "/F1 12 Tf", "72 720 Td"]
    for index, line in enumerate(lines):
        if index:
            commands.append("0 -24 Td")
        encoded = "".join(f"{mapping[char]:04X}" for char in line)
        commands.append(f"<{encoded}> Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type0 /BaseFont /STSong /Encoding /Identity-H /DescendantFonts [6 0 R] /ToUnicode 7 0 R >>",
        b"<< /Type /Font /Subtype /CIDFontType2 /BaseFont /STSong /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> /FontDescriptor 8 0 R /CIDToGIDMap /Identity /DW 1000 >>",
        b"<< /Length " + str(len(cmap)).encode("ascii") + b" >>\nstream\n" + cmap + b"\nendstream",
        b"<< /Type /FontDescriptor /FontName /STSong /Flags 4 /FontBBox [0 0 1000 1000] /ItalicAngle 0 /Ascent 800 /Descent -200 /CapHeight 700 /StemV 80 >>",
    ]
    chunks = [b"%PDF-1.4\n"]
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in chunks))
        chunks.append(f"{index} 0 obj\n".encode("ascii") + body + b"\nendobj\n")
    xref_at = sum(len(part) for part in chunks)
    xref = [f"xref\n0 {len(objects) + 1}\n".encode("ascii"), b"0000000000 65535 f \n"]
    for offset in offsets[1:]:
        xref.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    trailer = (
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode("ascii")
    )
    return b"".join(chunks + xref + [trailer])


def write_ofd(path: Path, invoice_xml: bytes | None) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("OFD.xml", OFD_SHELL)
        if invoice_xml is not None:
            archive.writestr("Doc_0/Attachs/einvoice.xml", invoice_xml)
        else:
            archive.writestr(
                "Doc_0/Pages/Content.xml",
                "<?xml version='1.0' encoding='utf-8'?><Page><Text>layout only</Text></Page>",
            )


def main() -> None:
    en = english_xml(
        "24330000000000000001",
        "2026-10-01",
        "专用",
        "100.00",
        "13.00",
        "113.00",
        "办公用品",
        "A4",
        "箱",
        "2",
        "50.00",
        "0.13",
        CODE,
        "张三",
    )
    invoice_005 = english_xml(
        "24330000000000000005",
        "2026-10-05",
        "普通",
        "50.00",
        "0.00",
        "50.00",
        "新鲜蔬菜",
        "千克",
        "千克",
        "1",
        "50.00",
        "免税",
        "1010115010000000000",
        "赵六",
    )
    invoice_006 = english_xml(
        "24330000000000000006",
        "2026-10-06",
        "普通",
        "80.00",
        "7.20",
        "87.20",
        "图书",
        "册",
        "册",
        "1",
        "80.00",
        "0.09",
        "1060201019900000000",
        "钱七",
    )
    invoice_003 = english_xml(
        "24330000000000000003",
        "2026-10-03",
        "专用",
        "300.00",
        "39.00",
        "339.00",
        "打印纸",
        "A4",
        "箱",
        "3",
        "100.00",
        "0.13",
        CODE,
        "王五",
    )
    red = english_xml(
        "24330000000000000004",
        "2026-10-04",
        "专用",
        "-100.00",
        "-13.00",
        "-113.00",
        "办公用品",
        "A4",
        "箱",
        "-2",
        "50.00",
        "0.13",
        CODE,
        "张三",
        red=True,
    )
    pinyin = pinyin_xml()
    files = {
        DATA / "en" / "invoice.xml": en,
        DATA / "en" / "invoice_005.xml": invoice_005,
        DATA / "en" / "invoice_006.xml": invoice_006,
        DATA / "pinyin" / "invoice.xml": pinyin,
        DATA / "ofd" / "invoice.xml": invoice_003,
        DATA / "red" / "invoice.xml": red,
        DATA / "dup" / "invoice_copy.xml": en,
    }
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    write_ofd(DATA / "ofd" / "invoice.ofd", invoice_003.encode("utf-8"))
    write_ofd(DATA / "ofd" / "no_xml.ofd", None)
    pdf_path = DATA / "pdf" / "invoice.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(
        text_pdf(
            [
                "发票号码：24330000000000000001",
                "价税合计（小写）113.00",
            ]
        )
    )
    photo = DATA / "photo" / "scan.jpg"
    photo.parent.mkdir(parents=True, exist_ok=True)
    photo.write_bytes(b"\xff\xd8\xff\xe0phone-photo-sample")
    bundle = DATA / "mixed" / "bundle.zip"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("en_invoice.xml", en)
        archive.writestr("pinyin_invoice.xml", pinyin)
        archive.write(DATA / "ofd" / "invoice.ofd", "invoice.ofd")
        archive.write(pdf_path, "invoice.pdf")
        archive.writestr("red_invoice.xml", red)
        archive.write(photo, "scan.jpg")
    malicious = DATA / "malicious" / "traversal.zip"
    malicious.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(malicious, "w") as archive:
        archive.writestr("../outside.txt", "nope")
    readme = ROOT / "samples" / "README.md"
    readme.write_text(README, encoding="utf-8")


README = f"""# 脱敏样本

税号、名称、发票号码都是虚构的，用来锁定解析结果。真实下载包不要放进这个目录。

手填进项税号：`{BUYER_ID}`。销项税号：`{SELLER_ID}`。

## 八类样本

| 类别 | 文件 | 发票号码 | 价税合计 | 期望 |
|---|---|---|---|---|
| 英文标签 XML | `data/en/invoice.xml` | 24330000000000000001 | 113.00 | 进项合格 |
| 拼音标签 XML | `data/pinyin/invoice.xml` | 24330000000000000002 | 206.00 | 进项合格 |
| 带内嵌 XML 的 OFD | `data/ofd/invoice.ofd` | 24330000000000000003 | 339.00 | 与同号 XML 一致 |
| 同一张票的 PDF | `data/pdf/invoice.pdf` | 24330000000000000001 | 113.00 | 只用来合并来源，不覆盖 XML 金额 |
| 红字票 | `data/red/invoice.xml` | 24330000000000000004 | -113.00 | 进汇总，金额为负，异常表提醒 |
| 重复文件 | `data/dup/invoice_copy.xml` | 24330000000000000001 | 113.00 | 不另起汇总行 |
| 税务局混合压缩包 | `data/mixed/bundle.zip` | 见包内文件 | 见包内文件 | 按号码与包外文件合并 |
| 手机照片 | `data/photo/scan.jpg` |  |  | NEEDS_OCR |

同目录还有这些辅助文件，不属于新的票种：

- `data/ofd/invoice.xml`：与 OFD 内嵌 XML 相同的 0003。
- `data/ofd/no_xml.ofd`：没有内嵌发票 XML，期望 `OFD_NO_XML`。
- `data/en/invoice_005.xml`：号码 24330000000000000005，价税合计 50.00，免税，进项合格。
- `data/en/invoice_006.xml`：号码 24330000000000000006，价税合计 87.20，无授权时成为第 6 张 `LICENSE_LIMIT`。
- `data/malicious/traversal.zip`：路径逃逸样本，只用于解压测试，不是发票。

## 对 samples/data 跑进项

无授权时：合格 5 张，异常 12 行。合格号码按日期为 0001、0002、0003、0004、0005。0006 写入异常表，原因码 `LICENSE_LIMIT`。

异常原因码合计：`DUP_INVOICE` 6、`LICENSE_LIMIT` 1、`NEEDS_OCR` 2、`OFD_NO_XML` 1、`RED_INVOICE` 1、`UNPACK_REJECTED` 1。
"""


if __name__ == "__main__":
    main()
