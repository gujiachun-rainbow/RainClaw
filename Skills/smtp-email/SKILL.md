---
name: smtp-email
description: "通过 SMTP 协议发送邮件。当用户要求发送邮件、发送 Email、发邮件、send email、mail、通知某人等场景时触发此技能。支持发送纯文本和 HTML 格式邮件，支持附件。"
---

# SMTP 邮件发送

通过 SMTP 协议发送邮件的技能。

## 功能

- 发送纯文本邮件
- 发送 HTML 格式邮件
- 支持附件
- 支持 TLS 加密

## 使用方法

### 1. 基本用法

调用脚本发送邮件：

```bash
python scripts/send_email.py \
  --to "recipient@example.com" \
  --subject "邮件主题" \
  --body "邮件内容"
```

### 2. 发送 HTML 邮件

```bash
python scripts/send_email.py \
  --to "recipient@example.com" \
  --subject "HTML邮件" \
  --body "<h1>Hello</h1><p>这是HTML邮件</p>" \
  --html
```

### 3. 添加附件

```bash
python scripts/send_email.py \
  --to "recipient@example.com" \
  --subject "带附件的邮件" \
  --body "请查收附件" \
  --attachment "/path/to/file.pdf"
```

### 4. 多个收件人

```bash
python scripts/send_email.py \
  --to "user1@example.com,user2@example.com" \
  --subject "群发邮件" \
  --body "大家好"
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| --to | 是 | 收件人邮箱，多个用逗号分隔 |
| --subject | 是 | 邮件主题 |
| --body | 是 | 邮件内容（纯文本或HTML） |
| --html | 否 | 标记内容为HTML格式 |
| --attachment | 否 | 附件路径 |
| --cc | 否 | 抄送，多个用逗号分隔 |
| --bcc | 否 | 密送，多个用逗号分隔 |

## 配置文件

SMTP 配置存储在 `scripts/smtp_config.json`，包含以下字段：

```json
{
  "server": "smtp.qq.com",
  "port": 465,
  "username": "your_email@qq.com",
  "password": "your_auth_code",
  "emailFrom": "your_email@qq.com",
  "useTLS": true
}
```

## 工作流程

1. 用户请求发送邮件
2. 确认收件人、主题、内容
3. 调用 `send_email.py` 脚本发送
4. 返回发送结果（成功/失败）

## 示例对话

**用户**: 发送邮件给 test@example.com，主题是"测试"，内容是"这是一封测试邮件"

**助手**: 好的，我来帮你发送邮件...
```bash
python .../send_email.py --to "test@example.com" --subject "测试" --body "这是一封测试邮件"
```
邮件发送成功！

## 注意事项

- QQ邮箱需要使用授权码而非密码
- 建议将敏感配置（密码/授权码）存储在配置文件中，不要硬编码
- 如需修改配置，编辑 `scripts/smtp_config.json` 文件
