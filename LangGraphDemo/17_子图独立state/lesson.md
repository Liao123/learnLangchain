# LangGraph 第 17 课：子图独立 state

## 这节课学什么

主图和子图各自定义自己的 state；主图只传给子图必要字段，也只接收必要结果。

## 解决什么问题

主订单 state 有订单号、商品名、金额、余额等内容。支付模块只需要金额和余额，不该依赖全部订单字段。

```text
主图 OrderState
{order_id, product_name, amount, balance}
        ↓ 只挑 amount、balance
支付子图 PaymentState
{amount, balance}
        ↓ 返回 balance、payment_status
主图继续创建订单回答
```

## 运行

```powershell
py .\LangGraphDemo\17_子图独立state\demo.py
```

## 观察结果

```text
主图交给支付子图：{'amount': 28.0, 'balance': 100.0}
支付子图收到：{'amount': 28.0, 'balance': 100.0}
支付子图返回：{'amount': 28.0, 'balance': 72.0, 'payment_status': '已支付'}

最终回答：订单 A1001 的 咖啡豆礼盒 已支付，余额剩余 72.0 元。
```

## 本课只记一句话

```text
子图不是必须共用主图 state；主图可以先挑字段组装子图输入，再挑字段合并子图输出。
```
