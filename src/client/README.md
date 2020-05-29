# 注意, 本项目已废弃, 请转用[cqhttp-mirai](https://github.com/yyuueexxiinngg/cqhttp-mirai)以及原版[yobot](https://github.com/yuudi/yobot)

### 本项目初衷为国服第一次公会前移植解燃眉之急, 现已发布更完善的[cqhttp-mirai](https://github.com/yyuueexxiinngg/cqhttp-mirai)

[cqhttp-mirai](https://github.com/yyuueexxiinngg/cqhttp-mirai)为[coolq-http-api](https://github.com/richardchien/coolq-http-api)的`mirai`端移植, 通过`cqhttp-mirai`可接入基于`cqhttp`开发的机器人应用

对于[yobot](https://github.com/yuudi/yobot)以及[HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot/)默认配置, 请在`cqhttp-mirai`中启用Websocket反向客户端并复制`cqhttp-mirai`中给出的配置并修改`reversePort`以及`accessToken`进行接入


## 以下为`yobot-mirai`废弃前的配置说明

### 本项目为 [yobot](https://github.com/yuudi/yobot) 的mirai端移植

### 仅为官方未出mirai版/mirai未推出Mirai-CQ-Adapter时救急临时使用
 
## 运行方法
 
先决条件: 运行mirai以及mirai-api-http  参照[mirai-console](https://github.com/mamoe/mirai-console)

#### 为mirai-api-http配置开启Websocket

运行方法参考原项目源码方式部署, 部署完成后修改config中mirai开头的键值对

```
    "mirai_auth_key": "这里修改为mirai-api-http的密钥",
    "mirai_host": "这里输入mirai-api-http运行的服务器",
    "mirai_port": 8080,   <-  这里输入mirai-api-http运行的端口
    "mirai_qq": 123456789,<-  这里输入mirai的机器人号码
```
 
### 移植
~~经过多次迭代，yobot与[cq-http-api](https://github.com/richardchien/coolq-http-api/)的耦合越来越深，不再适合移植了~~

~~作弊方式移植了~~