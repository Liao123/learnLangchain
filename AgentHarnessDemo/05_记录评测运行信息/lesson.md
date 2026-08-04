# Agent Harness 第 5 课：记录评测运行信息

## 这课学什么

给每次评测记录模型名、提示词版本、题集版本和题集内容指纹。

## 解决什么问题

两份报告一个 80%、一个 90%，但不知道它们分别用了什么模型、什么提示词和什么题目，数字不能直接比较。

## 你现在要做的

在项目根目录运行：

```powershell
py .\AgentHarnessDemo\05_记录评测运行信息\demo.py
```

打开 `输出\run_manifest.json`。

你会看到类似：

```json
{
  "model_name": "deepseek-v4-pro",
  "prompt_version": "router-v1",
  "dataset_version": "v1",
  "dataset_sha256": "一长串哈希字符"
}
```

## 为什么既要版本又要哈希

`dataset_version` 是人写的标签，例如 `v1`。

`dataset_sha256` 是根据整个 JSON 文件内容算出的指纹。

即使有人忘记把 `v1` 改成 `v2`，只要题目内容变了，哈希也会变化。

一句话：报告必须带来源信息，否则以后看见分数变化，也不知道究竟改了什么。
