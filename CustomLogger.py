import logging

class CustomLogger:
    def __init__(self, log_file_path, console_level=logging.INFO, file_level=logging.INFO):
        self.log_file_path = log_file_path
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # 将日志记录器的级别设置为最低级别 DEBUG

        # 创建日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')

        # 创建文件处理器以将日志写入文件
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(file_level)  # 设置文件处理器的日志级别
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 创建控制台处理器以输出日志到控制台
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)  # 设置控制台处理器的日志级别
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message, error=None):
        if error:
            message += f" Error: {error}"
        self.logger.error(message)

# 使用示例
if __name__ == "__main__":
    # 设置日志文件路径
    log_file_path = "app.log"

    # 实例化自定义日志记录器，并为控制台和文件处理器分别设置日志级别
    logger = CustomLogger(log_file_path, console_level=logging.ERROR, file_level=logging.INFO)

    # 记录不同级别的日志信息
    logger.info("这是一条信息日志。")
    logger.warning("这是一条警告日志。")
    logger.error("这是一条错误日志。")
