# LangGraph 第 7 课：SQLite 持久检查点

这节课学什么：把 LangGraph 的暂停状态写进 SQLite 文件。程序结束后，仍能从暂停位置恢复。

本课解决什么问题：`MemorySaver` 只在当前 Python 进程存活；终端关闭、服务重启后，暂停流程和聊天记录都会消失。

## 第一步：启动并暂停流程

```powershell
py .\LangGraphDemo\07_SQLite持久检查点\demo.py start
```

观察终端提示“已写入 SQLite”。此时本课文件夹会生成：

```text
输出/checkpoints.sqlite
```

## 第二步：用新进程恢复流程

```powershell
py .\LangGraphDemo\07_SQLite持久检查点\demo.py resume 确认
```

这次是重新启动 Python，但它会读回 SQLite 中同一个 `thread_id` 的暂停状态，最后取消订单。

把最后的“确认”改成任意其他文字，可以观察订单不会取消。

## 本课只记一句话

```text
MemorySaver：记忆只在内存，程序关闭即消失
SqliteSaver：记忆写到 .sqlite 文件，程序重启后还能恢复
```
