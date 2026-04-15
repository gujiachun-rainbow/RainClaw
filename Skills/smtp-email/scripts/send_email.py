#!/usr/bin/env python3
"""
SMTP 邮件发送脚本
支持纯文本、HTML格式邮件和附件
"""

import argparse
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path


def load_config():
    """加载 SMTP 配置"""
    config_path = Path(__file__).parent / "smtp_config.json"
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_message(config, to_addrs, subject, body, is_html=False, cc=None, bcc=None, attachment=None):
    """创建邮件消息"""
    msg = MIMEMultipart()
    msg["From"] = config["emailFrom"]
    msg["To"] = to_addrs
    msg["Subject"] = subject
    
    if cc:
        msg["Cc"] = cc
    if bcc:
        msg["Bcc"] = bcc
    
    # 添加邮件正文
    if is_html:
        msg.attach(MIMEText(body, "html", "utf-8"))
    else:
        msg.attach(MIMEText(body, "plain", "utf-8"))
    
    # 添加附件
    if attachment:
        attachment_path = Path(attachment)
        if not attachment_path.exists():
            raise FileNotFoundError(f"附件不存在: {attachment}")
        
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {attachment_path.name}"
            )
            msg.attach(part)
    
    return msg


def send_email(to, subject, body, is_html=False, cc=None, bcc=None, attachment=None):
    """发送邮件"""
    config = load_config()
    
    # 创建消息
    msg = create_message(
        config, to, subject, body, 
        is_html=is_html, cc=cc, bcc=bcc, attachment=attachment
    )
    
    # 收件人列表（包括 To, Cc, Bcc）
    recipients = [addr.strip() for addr in to.split(",")]
    if cc:
        recipients.extend([addr.strip() for addr in cc.split(",")])
    if bcc:
        recipients.extend([addr.strip() for addr in bcc.split(",")])
    
    # 发送邮件
    try:
        if config.get("useTLS", True):
            # 使用 SSL/TLS
            server = smtplib.SMTP_SSL(config["server"], config["port"])
        else:
            # 不使用 SSL
            server = smtplib.SMTP(config["server"], config["port"])
            server.starttls()
        
        server.login(config["username"], config["password"])
        server.sendmail(config["emailFrom"], recipients, msg.as_string())
        server.quit()
        
        return {
            "success": True,
            "message": f"邮件发送成功！收件人: {to}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="SMTP 邮件发送工具")
    parser.add_argument("--to", required=True, help="收件人邮箱（多个用逗号分隔）")
    parser.add_argument("--subject", required=True, help="邮件主题")
    parser.add_argument("--body", required=True, help="邮件内容")
    parser.add_argument("--html", action="store_true", help="内容为HTML格式")
    parser.add_argument("--cc", help="抄送（多个用逗号分隔）")
    parser.add_argument("--bcc", help="密送（多个用逗号分隔）")
    parser.add_argument("--attachment", help="附件路径")
    
    args = parser.parse_args()
    
    result = send_email(
        to=args.to,
        subject=args.subject,
        body=args.body,
        is_html=args.html,
        cc=args.cc,
        bcc=args.bcc,
        attachment=args.attachment
    )
    
    if result["success"]:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ 发送失败: {result['error']}")
        exit(1)


if __name__ == "__main__":
    main()
