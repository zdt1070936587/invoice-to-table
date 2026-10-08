# 发票成表

把已经下载到本机的数电发票文件夹或压缩包，整理成 Excel 里的三张表：发票汇总、商品明细、异常。

文件只在这台电脑处理。结果用于整理，不代替税务局查验。本工具不核验数字签名，入账归档仍要保存原始 XML。

## 安装

需要 Python 3.12。

```text
pip install -e ".[dev]"
```

## 跑脱敏样本

```text
python -m fapiao run samples/data --tax-id 91330000MA0000002Y --direction in --out 进项_样本.xlsx
```

无授权时合格 5 张，异常 12 行。样本里的税号和发票号码都是虚构的，说明见 [samples/README.md](samples/README.md)。

查看某张 XML 的标签：

```text
python -m fapiao dump samples/data/en/invoice.xml
```

不带参数时打开窗口。窗口和命令行调用同一个 `run`。

已在本机打出单个 exe：`dist/fapiao.exe`。不带参数打开窗口；`run` 和 `dump` 走命令行。目标电脑不需要安装 Python。

## 授权

授权文件是程序目录下的 `license.json`。签发私钥放在 `dev_keys/ed25519.seed`，不要提交。没有有效授权时，每次最多 5 张合格票进入汇总。
