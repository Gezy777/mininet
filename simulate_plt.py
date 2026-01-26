from typing import List
import matplotlib.pyplot as plt

# 这是一个用于Matplotlib绘图的工具类
# 通过调用这个类更便捷地自定义生成图表
class SimulatePlt:
    def __init__(self):
        self.default_figsize = (14, 12)

    def simple_plot(self, x, y, output_file, title, xlabel, ylabel):
        # 定义画布的大小
        plt.figure(figsize=self.default_figsize)

        # 绘制简单折线图，每个点用圆圈标记
        plt.plot(x, y, marker='o')

        # 添加标题和坐标轴
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        # 显示网格
        plt.grid(True)

        # 保存图表到指定文件
        plt.savefig(output_file)
        
        # 关闭图表，释放内存
        plt.close()