### 本项目为 [yobot](https://github.com/yuudi/yobot) 的mirai端移植

### 仅为官方未出mirai版/mirai未推出Mirai-CQ-Adapter时救急临时使用
 
## 运行方法
 
### 先决条件: 运行mirai以及mirai-api-http  参照[mirai-console](https://github.com/mamoe/mirai-console)

### 为mirai-api-http配置开启Websocket

#### 运行方法参考原项目源码方式部署, 部署完成后修改config中mirai开头的键值对

```
    "mirai_auth_key": "这里修改为mirai-api-http的密钥",
    "mirai_host": "这里输入mirai-api-http运行的服务器",
    "mirai_port": 8080,   <-  这里输入mirai-api-http运行的端口
    "mirai_qq": 123456789,<-  这里输入mirai的机器人号码
```
 
### 移植
~~经过多次迭代，yobot与[cq-http-api](https://github.com/richardchien/coolq-http-api/)的耦合越来越深，不再适合移植了~~

~~作弊方式移植了~~