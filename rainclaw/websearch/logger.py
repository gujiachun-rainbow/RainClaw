# -*- coding: utf-8 -*-
"""
日志模块 - 提供统一的日志记录功能

This module provides unified logging functionality for the entire application.
"""

import logging
import sys
from typing import Optional

# 默认日志格式
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# 创建日志记录器
logger = logging.getLogger("sear-crawl4ai")


def setup_logger(level: str = "INFO", log_format: Optional[str] = None) -> logging.Logger:
    """
    配置并返回应用程序日志记录器

    Args:
        level: 日志级别，可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL
        log_format: 日志格式，如果为None则使用默认格式

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 设置日志级别
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # 如果没有处理器，添加一个控制台处理器
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(log_format or DEFAULT_LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# 默认设置日志记录器
setup_logger()


# 导出常用日志函数，方便直接调用
def debug(msg: str, *args, **kwargs) -> None:
    """
    记录DEBUG级别的日志
    """
    logger.debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs) -> None:
    """
    记录INFO级别的日志
    """
    logger.info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs) -> None:
    """
    记录WARNING级别的日志
    """
    logger.warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs) -> None:
    """
    记录ERROR级别的日志
    """
    logger.error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs) -> None:
    """
    记录CRITICAL级别的日志
    """
    logger.critical(msg, *args, **kwargs)
