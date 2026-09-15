import os
import sys
import json
import argparse
import logging
import pydicom
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton,
                             QFileDialog, QMessageBox, QWidget, QVBoxLayout)

# ==================== 日志配置 ====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==================== 配置文件加载 ====================
def resource_path(relative_path):
    """获取资源路径（兼容 PyInstaller 打包后路径）"""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, relative_path)


def _get_config_path():
    """查找配置文件路径：exe/脚本目录 → 当前工作目录 → None"""
    # 1. 可执行文件/脚本所在目录（打包后 exe 同级）
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'anonymize_config.json')
    if os.path.exists(config_path):
        return config_path

    # 2. 当前工作目录
    cwd_config = os.path.join(os.getcwd(), 'anonymize_config.json')
    if os.path.exists(cwd_config):
        return cwd_config

    return None


def _load_config():
    """加载匿名化配置文件"""
    config_path = _get_config_path()

    if config_path:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            remove_fields = tuple(config_data.get('remove_fields', []))
            substitute_fields = config_data.get('substitute_fields', {})
            logger.info(f"已加载匿名化配置文件: {config_path}")
            return remove_fields, substitute_fields
        except Exception as e:
            logger.warning(f"配置文件读取失败 ({config_path}): {e}，不执行配置字段匿名化")

    logger.warning("未找到匿名化配置文件，不执行配置字段匿名化")
    return (), {}


# 从配置文件加载字段设置
REMOVE_FIELDS, SUBSTITUTE_FIELDS = _load_config()


# ==================== 命令行参数解析 ====================
def parse_args():
    parser = argparse.ArgumentParser(description="Anonymizes DICOM directory")
    parser.add_argument("-d",
                        "--input_dir",
                        type=str,
                        help="Input DICOM directory path",
                        required=True)
    parser.add_argument("-o",
                        "--output_dir",
                        type=str,
                        default='./anondata',
                        help="Output DICOM directory path")
    parser.add_argument("-l",
                        "--link_log_dir",
                        type=str,
                        default='./linklog',
                        help="Linking log directory")
    parser.add_argument("-g",
                        "--group_by",
                        type=str,
                        default='a',
                        help="Group output dicoms into subfolders by"
                             "anonymized accession number (a), Study Instance UID (s), MRN (m),"
                             "or do not group into subfolders at all (n)")
    args = parser.parse_args()
    return args


# ==================== 核心匿名化逻辑 ====================
def is_dicom_file(filename):
    """判断是否为DICOM文件"""
    if not os.path.isfile(filename):
        return False
    try:
        with open(filename, 'rb') as file_stream:
            file_stream.seek(128)
            data = file_stream.read(4)
        return data == b'DICM'
    except Exception as e:
        logger.warning(f"检查DICOM文件格式失败: {filename}, 错误: {str(e)}")
        return False


def list_all_files(path):
    """递归获取所有文件（跨平台兼容）"""
    _files = []
    if not os.path.isdir(path):
        return _files
    for root, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(root, file)
            _files.append(full_path)
    return _files


def safe_remove_private_tags(ds):
    """安全删除私有标签，增加异常处理"""
    try:
        for tag in list(ds.keys()):
            if tag.is_private:
                try:
                    if ds[tag].VR != "SQ":
                        del ds[tag]
                except Exception as e:
                    logger.warning(f"跳过损坏的私有标签 {tag}: {str(e)}")
        # 递归处理嵌套数据集
        for data_element in ds:
            if data_element.VR == "SQ":
                for item in data_element.value:
                    safe_remove_private_tags(item)
    except Exception as e:
        logger.error(f"删除私有标签时出错: {str(e)}")


def anonymize_dir(in_path, out_path):
    """匿名化目录下所有DICOM文件"""
    in_path = os.path.abspath(in_path)
    out_path = os.path.abspath(out_path)

    if not os.path.isdir(in_path):
        raise Exception(f"输入目录不存在: {in_path}")

    os.makedirs(out_path, exist_ok=True)

    in_files = list_all_files(in_path)
    success_count = 0
    fail_count = 0

    for f in in_files:
        if is_dicom_file(f):
            try:
                rel_path = os.path.relpath(f, in_path)
                new_file_name = os.path.join(out_path, rel_path)
                sub_new_dir = os.path.dirname(new_file_name)
                os.makedirs(sub_new_dir, exist_ok=True)
                anonymize_file(f, new_file_name)
                success_count += 1
                logger.info(f"成功处理文件: {f}")
            except Exception as e:
                fail_count += 1
                logger.error(f"处理文件失败: {f}, 错误: {str(e)}")
        else:
            logger.debug(f"非DICOM文件，跳过: {f}")

    logger.info(f"处理完成！成功: {success_count}, 失败: {fail_count}")
    logger.info(f"输出目录: {out_path}")


def anonymize_file(in_path, out_path, keep_private_tags=False, overwrite=True):
    """匿名化单个DICOM文件"""
    if os.path.exists(out_path) and not overwrite:
        raise Exception(f"文件已存在: {out_path}（使用overwrite=True覆盖）")

    try:
        f = pydicom.dcmread(
            in_path,
            force=True
        )
    except Exception as e:
        raise Exception(f"读取DICOM文件失败: {in_path}, 错误: {str(e)}")

    def _camelize(s):
        """下划线转驼峰"""
        return ''.join([frag[0].upper() + frag[1:] for frag in s.split('_') if frag])

    def _update_field(field, value):
        if not hasattr(f, field):
            return
        try:
            if value is None:
                delattr(f, field)
            else:
                setattr(f, field, value)
        except Exception as e:
            logger.warning(f"更新字段失败 {field}: {str(e)}")

    # 仅使用配置文件中的字段
    remove = [_camelize(field) for field in REMOVE_FIELDS]
    substitute = {_camelize(key): value for key, value in SUBSTITUTE_FIELDS.items()}

    # 执行删除/替换
    for field in remove:
        _update_field(field, None)
    for field, value in substitute.items():
        _update_field(field, value)

    # 安全删除私有标签
    if not keep_private_tags:
        safe_remove_private_tags(f)

    # 保存文件
    try:
        f.save_as(out_path)
    except Exception as e:
        raise Exception(f"保存DICOM文件失败: {out_path}, 错误: {str(e)}")


# ==================== GUI 界面 ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.input_folder = ""
        self.output_folder = ""
        self.initUI()

    def initUI(self):
        self.setWindowTitle("DICOM数据匿名化")
        self.setGeometry(100, 100, 500, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(100, 50, 100, 50)

        self.btn_input = QPushButton("选择输入文件夹")
        self.btn_output = QPushButton("选择输出文件夹")
        self.btn_run = QPushButton("运行")

        self.btn_input.clicked.connect(self.select_input_folder)
        self.btn_output.clicked.connect(self.select_output_folder)
        self.btn_run.clicked.connect(self.run_anonymize)

        layout.addWidget(self.btn_input)
        layout.addWidget(self.btn_output)
        layout.addWidget(self.btn_run)

    def select_input_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择输入文件夹")
        if folder_path:
            self.input_folder = folder_path
            self.btn_input.setText(f"输入文件夹: {os.path.basename(folder_path)}")

    def select_output_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder_path:
            self.output_folder = folder_path
            self.btn_output.setText(f"输出文件夹: {os.path.basename(folder_path)}")

    def run_anonymize(self):
        if not self.input_folder:
            QMessageBox.warning(self, "警告", "请先选择输入文件夹！")
            return
        if not self.output_folder:
            QMessageBox.warning(self, "警告", "请先选择输出文件夹！")
            return

        QMessageBox.information(self, "提示", "开始匿名化处理，请稍候...")
        try:
            anonymize_dir(self.input_folder, self.output_folder)
            QMessageBox.information(self, "成功", "DICOM数据匿名化完成！")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"匿名化失败：{str(e)}")


# ==================== 主入口 ====================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 命令行模式
        args = parse_args()
        anonymize_dir(args.input_dir, args.output_dir)
        print(f"匿名化完成！输出目录: {args.output_dir}")
    else:
        # GUI 模式
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)

        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        mainWindow = MainWindow()
        mainWindow.show()
        sys.exit(app.exec_())
