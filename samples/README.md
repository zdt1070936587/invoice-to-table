# 脱敏样本

税号、名称、发票号码都是虚构的，用来锁定解析结果。真实下载包不要放进这个目录。

手填进项税号：`91330000MA0000002Y`。销项税号：`91330000MA0000001X`。

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
