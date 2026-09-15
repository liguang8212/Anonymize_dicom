Windows系统：
Step1: 
打开 CMD

Step2: 
# 安装python环境
winget install Python.Python.3.12

Step3:  
#确认安装python成功
关闭当前CMD，重新打开一个新的CMD
运行python --version 输出 python 3.12.10 

Step3: 
#切换到代码的目录
cd anonymize_dicom的代码路径； 比如：“ cd  C:\Users\Administrator\Desktop\anonymize_dicom”

Step4: 
# 安装依赖
pip install -r requirements.txt

Step5: 

Python PyQt5_test.py




Linux系统：

Step1: 
打开 terminal

Step2: 
# 创建环境
conda create -n myenv python=3.10

Step3: 
# 进入环境
conda activate myenv

Step4: 

Cd anonymize_dicom的代码路径

Step4: 
# 安装依赖
pip install -r requirements.txt

Step5:
Python PyQt5_test.py