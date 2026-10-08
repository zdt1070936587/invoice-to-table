"""原因码与给会计看的说明。"""

from __future__ import annotations

OK = "OK"
RED_INVOICE = "RED_INVOICE"
DUP_INVOICE = "DUP_INVOICE"
DUP_CONFLICT = "DUP_CONFLICT"
AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
TAX_MISMATCH = "TAX_MISMATCH"
TAX_ID_MISMATCH = "TAX_ID_MISMATCH"
PDF_ONLY = "PDF_ONLY"
OFD_NO_XML = "OFD_NO_XML"
NEEDS_OCR = "NEEDS_OCR"
UNKNOWN_SCHEMA = "UNKNOWN_SCHEMA"
UNSUPPORTED_KIND = "UNSUPPORTED_KIND"
UNKNOWN_FILE = "UNKNOWN_FILE"
LICENSE_LIMIT = "LICENSE_LIMIT"
UNPACK_REJECTED = "UNPACK_REJECTED"

MESSAGES: dict[str, str] = {
    OK: "勾稽和税号通过",
    RED_INVOICE: "红字发票，金额为负，请核对",
    DUP_INVOICE: "同一发票号码已有合格票，此文件作为重复来源",
    DUP_CONFLICT: "同一发票号码存在两份内容不一致的 XML",
    AMOUNT_MISMATCH: "金额勾稽失败",
    TAX_MISMATCH: "某行税额和税率不符",
    TAX_ID_MISMATCH: "不是本公司该方向的票",
    PDF_ONLY: "只有 PDF，金额未纳入汇总",
    OFD_NO_XML: "OFD 内没有发票 XML",
    NEEDS_OCR: "图片或扫描件",
    UNKNOWN_SCHEMA: "XML 标签无法映射出 20 位发票号码或三个合计",
    UNSUPPORTED_KIND: "铁路、航空或财政票据，第一版不处理",
    UNKNOWN_FILE: "文件头无法识别",
    LICENSE_LIMIT: "超过免费额度，未写入汇总",
    UNPACK_REJECTED: "压缩包未能安全解开",
}

RED_SIGN_MISMATCH = "红字标记与金额符号不符"
PDF_NUMBER_MISSING = "未能确定发票号码"

SUMMARY_CODES = frozenset({OK, RED_INVOICE})
